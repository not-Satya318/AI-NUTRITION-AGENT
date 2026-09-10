"""
NutriAI – Nutrition Agent service layer.

Handles all interaction with the Groq API and constructs
the system / user prompts for the nutrition plan generation.
"""

import os
import json
import re
import logging

from groq import Groq, APIConnectionError, RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are NutriAI, a friendly and knowledgeable nutrition education assistant.
You help people learn about general healthy eating habits and create personalised
nutrition guidance based on the information they provide.

IMPORTANT BOUNDARIES:
- You are NOT a doctor, dietitian, or medical professional.
- You do NOT diagnose, treat, or manage any medical condition.
- You do NOT recommend prescription medications or supplements beyond common
  food-based nutrients.
- You do NOT promote extreme calorie restriction, crash diets, or eating patterns
  that could cause harm.
- For any user who mentions medical conditions, medications, severe allergies,
  eating disorders, pregnancy, or other high-risk situations, you MUST strongly
  recommend consulting a qualified healthcare professional (doctor, registered
  dietitian, etc.) before following any plan.

GUIDELINES FOR GENERATING PLANS:
- Use the user's supplied profile data exactly as given.
- Calorie and macro figures are approximations / educational estimates only.
  Always label them as such.
- Give practical, realistic, affordable food suggestions.
- Favour whole foods and balanced meals.
- Consider Indian cuisine options where relevant, alongside other cuisines.
- Fully respect the user's food preference (Vegetarian, Vegan, Eggetarian,
  Non-Vegetarian) – never include excluded foods.
- Fully respect stated allergies and disliked foods – never include them.
- Respect the preferred cuisine and budget level.
- Match the number of meals to the user's stated preference.
- Avoid recommending any food the user is allergic to, even as a minor ingredient.
- Keep language encouraging, practical, and easy to understand.

OUTPUT FORMAT:
You MUST respond with a single valid JSON object that matches the following
structure exactly. Do not add any text before or after the JSON object.

{
  "summary": "2-3 sentence personalised summary of the user and their goals",
  "calorie_guidance": "Estimated daily calorie range with a brief explanation",
  "macros": {
    "protein": "Amount in grams and food sources",
    "carbs": "Amount in grams and food sources",
    "fats": "Amount in grams and food sources"
  },
  "meal_plan": [
    {"meal": "Breakfast", "foods": ["food 1", "food 2"]},
    {"meal": "Mid-Morning Snack", "foods": ["food 1"]},
    {"meal": "Lunch", "foods": ["food 1", "food 2", "food 3"]},
    {"meal": "Evening Snack", "foods": ["food 1"]},
    {"meal": "Dinner", "foods": ["food 1", "food 2", "food 3"]}
  ],
  "weekly_plan": [
    {
      "day": "Monday",
      "breakfast": "Description",
      "lunch": "Description",
      "snack": "Description",
      "dinner": "Description"
    }
  ],
  "hydration": "Daily water intake guidance",
  "foods_to_prioritize": ["food 1", "food 2", "food 3"],
  "foods_to_limit": ["food 1", "food 2", "food 3"],
  "tips": ["tip 1", "tip 2", "tip 3"],
  "disclaimer": "Standard disclaimer reminding the user this is educational guidance only and not a substitute for professional medical or dietary advice."
}

The weekly_plan array must contain exactly 7 objects (Monday through Sunday).
All arrays must contain at least 3 items unless the user's meal count is lower.
"""


def _build_user_prompt(profile: dict) -> str:
    """Convert the user profile dict into a clear natural-language prompt."""
    lines = [
        "Please create a personalised nutrition plan for the following person:",
        "",
        f"Name: {profile.get('name', 'User')}",
        f"Age: {profile.get('age')} years",
        f"Gender: {profile.get('gender')}",
        f"Height: {profile.get('height')} cm",
        f"Weight: {profile.get('weight')} kg",
        f"BMI: {profile.get('bmi', 'N/A')} ({profile.get('bmi_category', 'N/A')})",
        f"Activity Level: {profile.get('activity_level')}",
        f"Fitness Goal: {profile.get('fitness_goal')}",
        f"Food Preference: {profile.get('food_preference')}",
        f"Meals Per Day: {profile.get('meals_per_day', 3)}",
    ]

    if profile.get("allergies"):
        lines.append(f"Allergies / Intolerances: {profile['allergies']}")
    if profile.get("disliked_foods"):
        lines.append(f"Foods to Avoid (dislikes): {profile['disliked_foods']}")
    if profile.get("cuisine_preference"):
        lines.append(f"Preferred Cuisine: {profile['cuisine_preference']}")
    if profile.get("budget_preference"):
        lines.append(f"Budget Level: {profile['budget_preference']}")
    if profile.get("additional_notes"):
        lines.append(f"Additional Notes: {profile['additional_notes']}")

    lines += [
        "",
        "Please generate a complete, practical nutrition plan following the JSON "
        "structure specified in your instructions.",
    ]
    return "\n".join(lines)


def calculate_bmi(height_cm: float, weight_kg: float) -> tuple[float, str]:
    """Return (bmi_value, category_string)."""
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal range"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obesity"

    return bmi, category


def _extract_json(text: str) -> dict:
    """
    Try to extract a JSON object from the model response.
    Falls back to a minimal error structure if parsing fails.
    """
    # First attempt: the whole string is JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Second attempt: find the first { … } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: return plain text wrapped in the expected structure
    logger.warning("Could not parse JSON from model response; using raw text fallback.")
    return {
        "summary": text[:500] if len(text) > 500 else text,
        "calorie_guidance": "Please refer to the summary above.",
        "macros": {"protein": "N/A", "carbs": "N/A", "fats": "N/A"},
        "meal_plan": [],
        "weekly_plan": [],
        "hydration": "Aim for 8 glasses (2 litres) of water per day.",
        "foods_to_prioritize": [],
        "foods_to_limit": [],
        "tips": [],
        "disclaimer": (
            "This information is for general educational purposes only and is not "
            "a substitute for professional medical or dietary advice."
        ),
    }


def generate_nutrition_plan(profile: dict) -> dict:
    """
    Call the Groq API and return the parsed nutrition plan dict.

    Raises:
        ValueError: if GROQ_API_KEY is not set.
        RuntimeError: for Groq API / network errors.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. "
            "Please add it to your .env file."
        )

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    client = Groq(api_key=api_key)
    user_prompt = _build_user_prompt(profile)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
    except RateLimitError:
        raise RuntimeError(
            "The Groq API rate limit has been reached. Please wait a moment and try again."
        )
    except APIConnectionError:
        raise RuntimeError(
            "Could not connect to the Groq API. Please check your internet connection."
        )
    except APIStatusError as exc:
        logger.error("Groq APIStatusError: %s", exc)
        raise RuntimeError(
            f"Groq API returned an error (status {exc.status_code}). "
            "Please try again shortly."
        )

    raw_content = response.choices[0].message.content or ""
    return _extract_json(raw_content)

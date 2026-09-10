"""
NutriAI – Flask Application Entry Point.
"""

import os
import logging

from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from werkzeug.exceptions import RequestEntityTooLarge

load_dotenv()

from services.nutrition_agent import generate_nutrition_plan, calculate_bmi

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB request limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ["name", "age", "gender", "height", "weight",
                   "activity_level", "fitness_goal", "food_preference"]

ALLOWED_ACTIVITY_LEVELS = {
    "Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"
}
ALLOWED_FITNESS_GOALS = {
    "Weight Loss", "Weight Maintenance", "Muscle Gain", "General Healthy Eating"
}
ALLOWED_FOOD_PREFERENCES = {
    "Vegetarian", "Non-Vegetarian", "Vegan", "Eggetarian"
}
ALLOWED_GENDERS = {"Male", "Female", "Non-binary", "Prefer not to say"}


def _validate_profile(data: dict) -> list[str]:
    """Return a list of validation error messages (empty = valid)."""
    errors = []

    for field in REQUIRED_FIELDS:
        if not data.get(field, "").strip():
            errors.append(f"'{field}' is required.")

    # Numeric validation
    try:
        age = int(data.get("age", 0))
        if age < 1 or age > 120:
            errors.append("Age must be between 1 and 120.")
    except (ValueError, TypeError):
        errors.append("Age must be a whole number.")

    try:
        height = float(data.get("height", 0))
        if height < 50 or height > 300:
            errors.append("Height must be between 50 cm and 300 cm.")
    except (ValueError, TypeError):
        errors.append("Height must be a number.")

    try:
        weight = float(data.get("weight", 0))
        if weight < 10 or weight > 500:
            errors.append("Weight must be between 10 kg and 500 kg.")
    except (ValueError, TypeError):
        errors.append("Weight must be a number.")

    if data.get("activity_level") not in ALLOWED_ACTIVITY_LEVELS:
        errors.append("Invalid activity level selected.")
    if data.get("fitness_goal") not in ALLOWED_FITNESS_GOALS:
        errors.append("Invalid fitness goal selected.")
    if data.get("food_preference") not in ALLOWED_FOOD_PREFERENCES:
        errors.append("Invalid food preference selected.")

    meals = data.get("meals_per_day", "3")
    if meals:
        try:
            meals_int = int(meals)
            if meals_int < 1 or meals_int > 10:
                errors.append("Meals per day must be between 1 and 10.")
        except (ValueError, TypeError):
            errors.append("Meals per day must be a whole number.")

    return errors


def _sanitize_text(value: str, max_length: int = 500) -> str:
    """Strip and truncate free-text input."""
    return value.strip()[:max_length] if value else ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    """Validate user profile, call the nutrition agent, render results."""
    form = request.form

    # Build a clean profile dict
    profile = {
        "name":              _sanitize_text(form.get("name", ""), 100),
        "age":               _sanitize_text(form.get("age", "")),
        "gender":            _sanitize_text(form.get("gender", "")),
        "height":            _sanitize_text(form.get("height", "")),
        "weight":            _sanitize_text(form.get("weight", "")),
        "activity_level":    _sanitize_text(form.get("activity_level", "")),
        "fitness_goal":      _sanitize_text(form.get("fitness_goal", "")),
        "food_preference":   _sanitize_text(form.get("food_preference", "")),
        "allergies":         _sanitize_text(form.get("allergies", "")),
        "disliked_foods":    _sanitize_text(form.get("disliked_foods", "")),
        "meals_per_day":     _sanitize_text(form.get("meals_per_day", "3")),
        "cuisine_preference":_sanitize_text(form.get("cuisine_preference", "")),
        "budget_preference": _sanitize_text(form.get("budget_preference", "")),
        "additional_notes":  _sanitize_text(form.get("additional_notes", "")),
    }

    errors = _validate_profile(profile)
    if errors:
        return render_template(
            "error.html",
            error_title="Invalid Input",
            error_message="Please correct the following errors:",
            error_list=errors,
        ), 400

    # Calculate BMI (skip for very young users – no adult categories)
    age = int(profile["age"])
    height = float(profile["height"])
    weight = float(profile["weight"])

    if age >= 18:
        bmi_value, bmi_category = calculate_bmi(height, weight)
        profile["bmi"] = bmi_value
        profile["bmi_category"] = bmi_category
        bmi_note = None
    else:
        bmi_value = None
        bmi_category = None
        bmi_note = (
            "BMI categories for children and teenagers depend on age- and "
            "sex-specific growth charts. Please consult a qualified healthcare "
            "professional for an accurate assessment."
        )
        profile["bmi"] = "N/A (under 18)"
        profile["bmi_category"] = "See note"

    try:
        plan = generate_nutrition_plan(profile)
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        return render_template(
            "error.html",
            error_title="Configuration Error",
            error_message=str(exc),
            error_list=[],
        ), 500
    except RuntimeError as exc:
        logger.error("Groq API error: %s", exc)
        return render_template(
            "error.html",
            error_title="Service Unavailable",
            error_message=str(exc),
            error_list=[],
        ), 503
    except Exception as exc:
        logger.exception("Unexpected error during plan generation: %s", exc)
        return render_template(
            "error.html",
            error_title="Unexpected Error",
            error_message=(
                "Sorry, we couldn't generate your plan right now. "
                "Please try again in a moment."
            ),
            error_list=[],
        ), 500

    return render_template(
        "result.html",
        profile=profile,
        plan=plan,
        bmi_value=bmi_value,
        bmi_category=bmi_category,
        bmi_note=bmi_note,
    )


@app.route("/calculate-bmi", methods=["POST"])
def calculate_bmi_route():
    """JSON endpoint for the client-side BMI calculator."""
    data = request.get_json(silent=True) or {}

    try:
        height = float(data.get("height", 0))
        weight = float(data.get("weight", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Height and weight must be numbers."}), 400

    if height < 50 or height > 300:
        return jsonify({"error": "Height must be between 50 and 300 cm."}), 400
    if weight < 10 or weight > 500:
        return jsonify({"error": "Weight must be between 10 and 500 kg."}), 400

    bmi, category = calculate_bmi(height, weight)
    return jsonify({"bmi": bmi, "category": category})


@app.route("/health")
def health():
    """Simple liveness probe."""
    return jsonify({"status": "ok", "service": "NutriAI"}), 200


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_error):
    return render_template(
        "error.html",
        error_title="Page Not Found",
        error_message="The page you are looking for does not exist.",
        error_list=[],
    ), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return render_template(
        "error.html",
        error_title="Method Not Allowed",
        error_message="This request method is not supported for that URL.",
        error_list=[],
    ), 405


@app.errorhandler(RequestEntityTooLarge)
def request_too_large(_error):
    return render_template(
        "error.html",
        error_title="Request Too Large",
        error_message="Your request was too large. Please reduce the input size.",
        error_list=[],
    ), 413


@app.errorhandler(500)
def server_error(_error):
    return render_template(
        "error.html",
        error_title="Server Error",
        error_message=(
            "An internal server error occurred. Please try again in a moment."
        ),
        error_list=[],
    ), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)

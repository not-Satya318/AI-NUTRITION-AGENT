# AI-NUTRITION-AGENT
NutriAI is an AI dietary planner built with Flask and Python. It calculates BMI deterministically and uses agentic AI to generate custom meal plans tailored to user biometrics, fitness goals, allergies, and food preferences. Features include robust input validation, custom error handling, and instant health guidance.
# NutriAI – AI-Powered Nutrition Agent

NutriAI is a Flask-based web application that generates personalized dietary recommendations and nutrition plans based on individual biometric data, fitness targets, and lifestyle preferences.

---

## Features

* **Deterministic BMI Calculation:** Directly calculates BMI values and categories using Python arithmetic to ensure numerical accuracy.


* **Personalized Nutrition Plans:** Evaluates user attributes—such as age, gender, height, weight, activity level, fitness goals, and food preferences—to formulate custom nutrition plans.


* **Allergy & Preference Filtering:** Considers allergies, disliked foods, cuisine choices, budget levels, and target meal frequencies.


* **Input Validation & Sanitization:** Enforces numeric ranges and permitted values on user profiles, along with text sanitization and request size limits (1 MB).


* **REST & JSON Endpoints:** Includes routes for UI rendering, asynchronous BMI calculation, and service health checks.



---

## Repository Structure

```text
NutritionAgent/
├── app.py                     # Application entry point and Flask routing[cite: 1, 2]
├── requirements.txt           # Package dependencies[cite: 1]
├── .env                       # Environment variables (API keys, secrets)[cite: 1]
├── services/                  # Business logic and agent integration[cite: 1]
│   ├── __init__.py[cite: 1]
│   └── nutrition_agent.py     # Plan generation and BMI calculation logic[cite: 1, 2]
├── static/                    # Frontend styling and scripts[cite: 1]
│   ├── css/
│   │   └── style.css[cite: 1]
│   └── js/
│       └── script.js[cite: 1]
└── templates/                 # Jinja2 HTML templates[cite: 1]
    ├── index.html             # Profile intake form[cite: 1, 2]
    ├── result.html            # Nutrition plan and BMI output[cite: 1, 2]
    └── error.html             # Error handling pages[cite: 1, 2]

```

---

## Setup & Installation

### 1. Prerequisites

* Python 3.10 or later installed on your system.
* An active API key for the underlying LLM service (e.g., Groq API key).



### 2. Clone the Repository

```bash
git clone https://github.com/your-username/NutritionAgent.git
cd NutritionAgent

```

### 3. Create a Virtual Environment

* **Windows:**
```cmd
python -m venv venv
venv\Scripts\activate

```


* **macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate

```



### 4. Install Dependencies

```bash
pip install -r requirements.txt

```

### 5. Configure Environment Variables

Create a `.env` file in the project root directory:

```env
SECRET_KEY=your_secret_key_here[cite: 2]
GROQ_API_KEY=your_api_key_here
FLASK_DEBUG=True[cite: 2]

```

---

## Running the Application

Start the local development server:

```bash
python app.py

```

The application will launch on `[http://0.0.0.0:5000](http://0.0.0.0:5000)` (or `[http://127.0.0.1:5000](http://127.0.0.1:5000)`). Open the URL in your web browser to access the interface.

---

## API Reference

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | `GET` | Renders the primary profile input form (`index.html`).

 |
| `/generate-plan` | `POST` | Validates profile input, computes BMI, invokes the nutrition agent, and displays `result.html`.

 |
| `/calculate-bmi` | `POST` | JSON API endpoint that validates height/weight and returns the BMI score and category.

 |
| `/health` | `GET` | Health check probe returning `{"status": "ok", "service": "NutriAI"}` with HTTP 200.

 |

---

## Error Handling

Custom error pages are rendered via `templates/error.html` for common HTTP status codes:

* **400:** Input validation errors (invalid numeric ranges or missing required fields).


* **404:** Page not found.


* **405:** Method not allowed.


* **413:** Request entity exceeds the 1 MB size limit.


* **500 / 503:** Service or LLM API configuration/availability failures.

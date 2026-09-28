import json
import os
import re
from typing import Any

import httpx

DISCLAIMER = "General wellness example only. This is not medical advice or a clinical nutrition plan."

MEALS = {
    "breakfast": [
        {"name": "Cinnamon apple overnight oats", "description": "Oats, apple, chia and oat milk", "calories": 360, "tags": ["vegan", "vegetarian", "gluten-free", "nuts-free"]},
        {"name": "Berry yogurt and toasted seeds", "description": "Plain yogurt, berries and pumpkin seeds", "calories": 330, "tags": ["vegetarian", "dairy", "gluten-free", "nuts-free"]},
        {"name": "Avocado and tomato toast", "description": "Sourdough toast with avocado and tomato", "calories": 390, "tags": ["vegan", "vegetarian", "gluten", "nuts-free"]},
    ],
    "lunch": [
        {"name": "Green goddess chickpea bowl", "description": "Chickpeas, greens, cucumber and lemon tahini", "calories": 510, "tags": ["vegan", "vegetarian", "sesame", "gluten-free", "nuts-free"]},
        {"name": "Roasted vegetable grain bowl", "description": "Seasonal vegetables, brown rice and herbs", "calories": 480, "tags": ["vegan", "vegetarian", "gluten-free", "nuts-free"]},
        {"name": "Lemon chicken and farro", "description": "Chicken, farro, greens and lemon", "calories": 540, "tags": ["meat", "gluten", "nuts-free"]},
    ],
    "snack": [
        {"name": "Pear with sunflower butter", "description": "Fresh pear and sunflower seed butter", "calories": 210, "tags": ["vegan", "vegetarian", "nuts-free", "gluten-free"]},
        {"name": "Hummus and crunchy vegetables", "description": "Hummus with carrot and cucumber", "calories": 190, "tags": ["vegan", "vegetarian", "sesame", "gluten-free", "nuts-free"]},
        {"name": "Cottage cheese and peaches", "description": "Cottage cheese with sliced peach", "calories": 220, "tags": ["vegetarian", "dairy", "gluten-free", "nuts-free"]},
    ],
    "dinner": [
        {"name": "Miso-glazed salmon and greens", "description": "Salmon, sesame greens and brown rice", "calories": 620, "tags": ["fish", "sesame", "gluten-free", "nuts-free"]},
        {"name": "Smoky lentil and sweet potato stew", "description": "Lentils, sweet potato and greens", "calories": 520, "tags": ["vegan", "vegetarian", "gluten-free", "nuts-free"]},
        {"name": "Herby tofu with roasted vegetables", "description": "Tofu, seasonal vegetables and quinoa", "calories": 500, "tags": ["vegan", "vegetarian", "soy", "gluten-free", "nuts-free"]},
    ],
}

ALLERGEN_TAGS = {"dairy": "dairy", "lactose": "dairy", "nuts": "nuts", "peanut": "nuts", "gluten": "gluten", "sesame": "sesame", "soy": "soy", "fish": "fish", "egg": "egg"}


def _eligible(meal: dict[str, Any], preference: str, allergies: list[str]) -> bool:
    tags = set(meal["tags"])
    if preference == "vegan" and "vegan" not in tags:
        return False
    if preference == "vegetarian" and "vegetarian" not in tags:
        return False
    blocked = {ALLERGEN_TAGS[item.lower()] for item in allergies if item.lower() in ALLERGEN_TAGS}
    return not blocked.intersection(tags)


def rule_based_plan(profile: dict[str, Any]) -> dict[str, Any]:
    preference = profile.get("dietary_preference", "omnivore")
    allergies = profile.get("allergies", [])
    selected = {}
    for meal_name, options in MEALS.items():
        choices = [meal for meal in options if _eligible(meal, preference, allergies)]
        if not choices:
            raise ValueError(f"No {meal_name} options match these preferences and allergies")
        index = sum(map(ord, str(profile.get("goal", "balanced")) + meal_name)) % len(choices)
        selected[meal_name] = choices[index] | {"calories": choices[index]["calories"]}
    total = sum(meal["calories"] for meal in selected.values())
    return {
        **selected,
        "nutrition_summary": {
            "approximate_calories": total,
            "approximate_macros_g": {"protein": round(total * 0.25 / 4), "carbohydrates": round(total * 0.45 / 4), "fat": round(total * 0.30 / 9)},
            "note": "Illustrative estimates only; portions and brands vary.",
        },
        "hydration_reminder": "Keep water nearby and drink to thirst; individual needs vary.",
        "disclaimer": DISCLAIMER,
        "generation_mode": "local-rules",
    }


def _validate_provider_plan(data: Any, profile: dict[str, Any]) -> dict[str, Any]:
    required = ("breakfast", "lunch", "snack", "dinner")
    if not isinstance(data, dict) or any(not isinstance(data.get(key), dict) or not data[key].get("name") for key in required):
        raise ValueError("AI provider returned an incomplete plan")
    for key in required:
        data[key] = {"name": str(data[key]["name"])[:120], "description": str(data[key].get("description", ""))[:240], "calories": int(data[key].get("calories", 0))}
        if not 0 <= data[key]["calories"] <= 1500:
            raise ValueError("AI provider returned invalid nutrition data")
    meal_text = " ".join(f"{data[key]['name']} {data[key]['description']}" for key in required).lower()
    restricted_terms = {
        "vegan": ("beef", "pork", "chicken", "turkey", "fish", "salmon", "seafood", "egg", "milk", "cheese", "yogurt", "butter", "honey"),
        "vegetarian": ("beef", "pork", "chicken", "turkey", "fish", "salmon", "seafood"),
    }
    for term in restricted_terms.get(profile.get("dietary_preference"), ()):
        if re.search(rf"\b{re.escape(term)}\b", meal_text):
            raise ValueError("AI provider returned a meal that conflicts with the selected diet")
    allergy_terms = {
        "dairy": ("dairy", "milk", "cheese", "yogurt", "butter", "cream"),
        "lactose": ("dairy", "milk", "cheese", "yogurt", "butter", "cream"),
        "nuts": ("nut", "almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut"),
        "peanut": ("peanut",),
        "gluten": ("gluten", "wheat", "barley", "rye"),
        "sesame": ("sesame",),
        "soy": ("soy", "tofu",),
        "fish": ("fish", "salmon", "tuna", "cod"),
        "egg": ("egg",),
    }
    for allergy in profile.get("allergies", []):
        for term in allergy_terms.get(allergy, ()):
            if re.search(rf"\b{re.escape(term)}\b", meal_text):
                raise ValueError("AI provider returned a meal that conflicts with an allergy filter")
    calories = sum(data[key]["calories"] for key in required)
    data["nutrition_summary"] = {
        "approximate_calories": calories,
        "approximate_macros_g": {"protein": round(calories * 0.25 / 4), "carbohydrates": round(calories * 0.45 / 4), "fat": round(calories * 0.30 / 9)},
        "note": "Illustrative estimates only; portions and brands vary.",
    }
    data["hydration_reminder"] = "Keep water nearby and drink to thirst; individual needs vary."
    data["disclaimer"] = DISCLAIMER
    data["generation_mode"] = "optional-ai"
    return data


def generate_plan(profile: dict[str, Any]) -> dict[str, Any]:
    endpoint = os.getenv("AI_API_URL")
    api_key = os.getenv("AI_API_KEY")
    if endpoint and api_key:
        try:
            response = httpx.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": os.getenv("AI_MODEL", "gpt-4o-mini"), "response_format": {"type": "json_object"}, "messages": [
                    {"role": "system", "content": "Return a JSON object with breakfast, lunch, snack, dinner (each name, description, integer calories). General wellness suggestions only, no medical claims. Respect the supplied diet and allergy filters."},
                    {"role": "user", "content": json.dumps({"goal": profile.get("goal"), "dietary_preference": profile.get("dietary_preference"), "allergies": profile.get("allergies", []), "preferences": profile.get("preferences", "")})},
                ]},
                timeout=8,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return _validate_provider_plan(json.loads(content), profile)
        except (httpx.HTTPError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    plan = rule_based_plan(profile)
    plan["generation_mode"] = "local-rules-fallback" if endpoint and api_key else "local-rules"
    return plan
"""
NutriPulse — Gemini AI Service
Handles food image recognition and meal recommendations.
Uses Google Gemini 2.0 Flash for fast, accurate results.
"""
import os
import json
import re
import google.generativeai as genai

API_KEY = os.getenv('GEMINI_API_KEY', '')

# Configure only if key exists
if API_KEY and API_KEY != 'your_gemini_api_key_here':
    genai.configure(api_key=API_KEY)

MODEL_NAME = 'gemini-2.0-flash'


def is_ai_available():
    return bool(API_KEY) and API_KEY != 'your_gemini_api_key_here'


def _parse_json_response(text):
    """Strip markdown fences and parse JSON from Gemini response."""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return json.loads(text.strip())


def analyze_food_image(image_path):
    """
    Send a food image to Gemini and get nutrition analysis.
    Returns dict with food_name, calories, protein, carbs, fat, etc.
    """
    if not is_ai_available():
        return {'error': 'Gemini API key not configured. Add GEMINI_API_KEY to .env'}

    try:
        model = genai.GenerativeModel(MODEL_NAME)

        # Read image as bytes
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        # Detect MIME type from extension
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                    '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
        mime_type = mime_map.get(ext, 'image/jpeg')

        image_part = {'mime_type': mime_type, 'data': image_bytes}

        prompt = """Analyze this food image. Identify the food and estimate its nutritional content.
Return ONLY a valid JSON object (no markdown, no explanation) with these fields:
{
  "food_name": "name of the food",
  "calories": estimated calories per serving as a number,
  "protein": grams of protein as a number,
  "carbs": grams of carbs as a number,
  "fat": grams of fat as a number,
  "fiber": grams of fiber as a number,
  "serving_size": "estimated serving size description",
  "health_score": health rating from 1 to 10 as a number,
  "insight": "one brief sentence about this food's health impact"
}"""

        response = model.generate_content([prompt, image_part])
        result = _parse_json_response(response.text)

        # Validate required fields exist
        required = ['food_name', 'calories', 'protein', 'carbs', 'fat']
        for field in required:
            if field not in result:
                result[field] = 0 if field != 'food_name' else 'Unknown Food'

        return result

    except json.JSONDecodeError:
        return {'error': 'AI returned invalid data. Please try again.'}
    except Exception as e:
        return {'error': f'AI analysis failed: {str(e)}'}


def get_meal_recommendations(food_entries, calorie_goal):
    """
    Generate AI meal recommendations based on today's intake.
    Returns dict with recommendations list and daily_summary.
    """
    if not is_ai_available():
        return {'error': 'Gemini API key not configured. Add GEMINI_API_KEY to .env'}

    try:
        model = genai.GenerativeModel(MODEL_NAME)

        # Build context from today's entries
        if food_entries:
            total_cal = sum(e.get('calories', 0) for e in food_entries)
            total_pro = sum(e.get('protein', 0) for e in food_entries)
            total_carb = sum(e.get('carbs', 0) for e in food_entries)
            total_fat = sum(e.get('fat', 0) for e in food_entries)
            foods_list = ', '.join(e['food_name'] for e in food_entries)
            context = f"""Today's intake so far:
Foods eaten: {foods_list}
Total: {total_cal:.0f} cal, {total_pro:.0f}g protein, {total_carb:.0f}g carbs, {total_fat:.0f}g fat
Daily calorie goal: {calorie_goal} calories
Remaining: {max(0, calorie_goal - total_cal):.0f} calories"""
        else:
            context = f"""No food logged yet today.
Daily calorie goal: {calorie_goal} calories"""

        prompt = f"""{context}

Suggest 3 healthy meal ideas for the rest of the day. Consider nutritional balance.
Return ONLY valid JSON (no markdown):
{{
  "recommendations": [
    {{
      "meal_name": "meal name",
      "description": "brief description",
      "estimated_calories": number,
      "protein": number,
      "carbs": number,
      "fat": number,
      "why": "one sentence on why this is a good choice"
    }}
  ],
  "daily_summary": "brief assessment of nutrition today and what to focus on"
}}"""

        response = model.generate_content(prompt)
        return _parse_json_response(response.text)

    except json.JSONDecodeError:
        return {'error': 'AI returned invalid data. Please try again.'}
    except Exception as e:
        return {'error': f'AI recommendation failed: {str(e)}'}

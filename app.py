import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

# Ensure API Key is set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("⚠️ OPENAI_API_KEY is missing! Add it to your .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def generate_ai_questions(age_group, event_type, tone, num_questions):
    """
    Generate unique Bingo questions using OpenAI's GPT-3.5 Turbo API.
    """
    prompt = f"""
    Generate {num_questions} unique and fun Bingo questions for a {event_type} event.
    The participants are in the age group {age_group}.
    The tone of the questions should be {tone}.
    Each question should encourage interaction and be relevant to the event type, age group, and tone.
    Format the questions as a JSON list.
    Example:
    [
        "Find someone who loves pizza!",
        "Find someone who has a pet cat!",
        "Find someone who enjoys hiking!"
    ]
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use the newer GPT-3.5 Turbo model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Bingo questions."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,  # Increase max_tokens for more questions
            n=1,
            stop=None,
            temperature=0.7,
        )
        questions = response.choices[0].message.content.strip()
        print("Generated Questions:", questions)  # Debugging
        return json.loads(questions)  # Convert the string response to a Python list safely
    except Exception as e:
        print(f"Error generating questions: {e}")  # Debugging
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_event', methods=['POST'])
def start_event():
    data = request.json
    age_group = f"{data.get('ageFrom')}-{data.get('ageTo')}"
    event_type = data.get('eventType')
    tone = data.get('tone')
    num_questions = int(data.get('numQuestions'))

    # Generate AI-based questions
    questions = generate_ai_questions(age_group, event_type, tone, num_questions)
    if not questions:
        return jsonify({"error": "Failed to generate questions. Please try again."}), 500

    return jsonify({"questions": questions})

@app.route('/participants')
def participants():
    return render_template('participants.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use Render's PORT or default to 5000
    app.run(host='0.0.0.0', port=port)

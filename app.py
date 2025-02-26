import os
from dotenv import load_dotenv
from openai import OpenAI
from flask_socketio import join_room, leave_room
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import qrcode
from io import BytesIO
import base64
from flask_socketio import SocketIO, emit
import random
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
socketio = SocketIO(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store event data and participants
events = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Bingo questions."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.7,
        )
        questions = response.choices[0].message.content.strip()
        return eval(questions)  # Convert the string response to a Python list
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return []

@app.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')

@app.route('/start_event', methods=['POST'])
def start_event():
    try:
        data = request.json
        age_group = f"{data.get('ageFrom')}-{data.get('ageTo')}"
        event_type = data.get('eventType')
        tone = data.get('tone')
        num_questions = int(data.get('numQuestions'))

        if not all([age_group, event_type, tone, num_questions]):
            return jsonify({"error": "Missing required fields"}), 400

        questions = generate_ai_questions(age_group, event_type, tone, num_questions)
        if not questions:
            return jsonify({"error": "Failed to generate questions. Please try again."}), 500

        # Create a unique event ID
        event_id = os.urandom(8).hex()

        # Generate QR code for the event
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"{request.host_url}join/{event_id}")  # Ensure the URL is correct
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # Store event data
        events[event_id] = {
            "questions": questions,
            "num_questions": num_questions,  # Store the number of questions
            "participants": {},
            "completed": [],
            "qr_code": qr_code
        }

        logger.info(f"Event started with ID: {event_id}")
        return jsonify({
            "event_id": event_id,
            "qr_code": qr_code
        })
    except Exception as e:
        logger.error(f"Error starting event: {e}")
        return jsonify({"error": str(e)}), 500

# Add other routes and logic here...

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Use the PORT environment variable or default to 5000
    logger.info(f"Starting app on port {port}")
    socketio.run(app, host='0.0.0.0', port=port)
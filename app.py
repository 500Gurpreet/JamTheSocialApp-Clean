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
        print(f"Error generating questions: {e}")
        return []

@app.route('/')
def index():
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
            "participants": {},
            "completed": [],
            "qr_code": qr_code
        }

        return jsonify({
            "event_id": event_id,
            "qr_code": qr_code
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/join/<event_id>')
def join_event(event_id):
    if event_id not in events:
        return "Event not found.", 404
    return render_template('join.html', event_id=event_id)

@app.route('/register', methods=['POST'])
def register():
    try:
        event_id = request.form.get('event_id')
        name = request.form.get('name')
        if event_id not in events:
            return jsonify({"error": "Event not found."}), 404

        # Assign unique questions to the participant
        questions = events[event_id]["questions"]
        random.shuffle(questions)
        participant_questions = questions[:5]  # Assign 5 random questions

        # Generate QR code for the participant
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(name)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # Add participant to the event
        events[event_id]["participants"][name] = {
            "questions": participant_questions,
            "qr_code": qr_code,
            "completed": False
        }

        # Notify host about the new participant
        socketio.emit('update_participants', {
            "participants": list(events[event_id]["participants"].keys())
        }, room=event_id)

        return jsonify({
            "success": True,
            "qr_code": qr_code,
            "questions": participant_questions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Add this to the participant data structure in the /register route
events[event_id]["participants"][name] = {
    "questions": participant_questions,
    "qr_code": qr_code,
    "completed": False,
    "current_question_index": 0  # Track the current question
}

# Add a new route to handle question progress
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    try:
        data = request.json
        event_id = data.get('event_id')
        name = data.get('name')
        answer = data.get('answer')

        if event_id not in events or name not in events[event_id]["participants"]:
            return jsonify({"error": "Invalid event or participant."}), 404

        participant = events[event_id]["participants"][name]
        current_index = participant["current_question_index"]

        # Check if the answer is correct (for now, assume all answers are correct)
        # You can add logic to validate the answer if needed

        # Move to the next question
        participant["current_question_index"] += 1

        # Check if all questions are completed
        if participant["current_question_index"] >= len(participant["questions"]):
            participant["completed"] = True
            return jsonify({"success": True, "completed": True, "message": "Congratulations, Bingo!"})

        return jsonify({
            "success": True,
            "completed": False,
            "next_question": participant["questions"][participant["current_question_index"]]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/event/<event_id>')
def event_host(event_id):
    if event_id not in events:
        return "Event not found.", 404
    return render_template('host.html', event_id=event_id, participants=events[event_id]["participants"], qr_code=events[event_id]["qr_code"])

@app.route('/participant/<event_id>/<name>')
def event_participant(event_id, name):
    if event_id not in events or name not in events[event_id]["participants"]:
        return "Participant not found.", 404
    participant = events[event_id]["participants"][name]
    return render_template('participant.html', event_id=event_id, name=name, questions=participant["questions"], qr_code=participant["qr_code"])

# SocketIO events
@socketio.on('join_event')
def handle_join_event(data):
    event_id = data['event_id']
    join_room(event_id)

@socketio.on('complete_bingo')
def handle_complete_bingo(data):
    event_id = data['event_id']
    name = data['name']
    if event_id not in events or name not in events[event_id]["participants"]:
        return

    # Mark participant as completed
    events[event_id]["participants"][name]["completed"] = True
    events[event_id]["completed"].append(name)

    # Notify host about the completion
    socketio.emit('update_completed', {
        "completed": events[event_id]["completed"]
    }, room=event_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
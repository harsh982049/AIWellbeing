from flask import Flask, request, Response, stream_with_context
from config import Config
from extensions import db
from flask_migrate import Migrate
from services.auth_service import register_user, login_user
from services.tracking_service import start_tracking, stop_tracking
from services.chatbot_service import chat_with_bot, reset_session, sse_stream
from services.stress_face_service import face_health, face_predict
from flask_jwt_extended import JWTManager
from flask_cors import CORS

import os
import signal
import atexit

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# -----------------------------------------
# PID-based tracker cleanup on Flask exit
# -----------------------------------------
def kill_tracker():
    pid_file = "tracker_tray.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"✅ Tracker process (PID {pid}) terminated on Flask exit.")
            os.remove(pid_file)
        except Exception as e:
            print(f"⚠️ Error terminating tracker: {e}")

atexit.register(kill_tracker)
signal.signal(signal.SIGINT, lambda sig, frame: exit(0))  # handle Ctrl+C

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    return register_user(data)

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    return login_user(data)

@app.route("/api/start_tracking", methods=["POST"])
def start_tracking_route():
    return start_tracking()

@app.route("/api/stop_tracking", methods=["POST"])
def stop_tracking_route():
    return stop_tracking()

@app.route("/api/chatbot", methods=["POST"])
def chatbot_route():
    data = request.get_json()
    # print(data)
    return chat_with_bot(data)  # returns (json, status)

@app.route("/api/chatbot/stream", methods=["GET"])
def chatbot_stream_route():
    return Response(stream_with_context(
        sse_stream(request.args.get("session_id",""), request.args.get("message",""))
    ), headers={
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    })

@app.route("/api/chatbot/reset", methods=["POST"])
def chatbot_reset_route():
    data = request.get_json()
    return reset_session(data)

# --------------------------
# Face stress detection endpoints
# --------------------------
@app.route("/api/stress/face/health", methods=["GET"])
def stress_face_health():
    return face_health()

@app.route("/api/stress/face/predict", methods=["POST"])
def stress_face_predict():
    return face_predict(request)

if __name__ == "__main__":
    app.run(debug=True)

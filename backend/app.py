from flask import Flask, request, Response, stream_with_context, jsonify
from config import Config
from extensions import db
from flask_migrate import Migrate
from sqlalchemy import func

from services.auth_service import register_user, login_user
from services.tracking_service import start_tracking, stop_tracking
from services.stress_face_service import face_health, face_predict
from services.chatbot_service import chat_with_bot, reset_session, sse_stream

from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS

from models import Chat, ChatMessage, ChatSummary, UserMemory  # new models

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


# -------- Auth --------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    return register_user(data)

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    return login_user(data)


# -------- Keyboard tracker--------
@app.route("/api/start_tracking", methods=["POST"])
def start_tracking_route():
    return start_tracking()

@app.route("/api/stop_tracking", methods=["POST"])
def stop_tracking_route():
    return stop_tracking()


# -------- Stress Face Detection (JWT optional) --------
@app.route("/api/stress/face/health", methods=["GET"])
@jwt_required(optional=True)
def stress_face_health():
    # If you want to gate by login, switch to @jwt_required() above.
    return face_health()

@app.route("/api/stress/face/predict", methods=["POST"])
@jwt_required(optional=True)
def stress_face_predict():
    # Logged-in user id (or None if guest)
    uid = get_jwt_identity()
    # You can store per-user analytics here if desired.
    # e.g., log user id + timestamp + confidence, etc.
    return face_predict(request)  # returns (json, status)


# -------- Chat management --------
@app.route("/api/chats", methods=["POST"])
@jwt_required()  # must be logged in to create a persistent chat
def create_chat():
    uid = get_jwt_identity()
    try:
        user_id = int(uid) if uid is not None else None
    except ValueError:
        user_id = None

    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip() or None
    is_journal = bool(body.get("is_journal", False))

    if is_journal:
        # one journal per user
        existing = Chat.query.filter_by(user_id=user_id, is_journal=True).first()
        if existing:
            return jsonify({"chat_id": existing.id, "title": existing.title, "is_journal": True}), 200

    # ✅ New logic: if this is a normal chat with no provided title,
    # and the user already has an EMPTY chat (0 messages), reuse it.
    if not is_journal and title is None:
        # newest first
        candidates = (
            Chat.query
            .filter_by(user_id=user_id, is_journal=False)
            .order_by(
                func.coalesce(Chat.updated_at, Chat.created_at).desc(),
                Chat.id.desc()
            )
            .all()
        )
        for c in candidates:
            # Count messages for this chat; reuse the first empty one.
            msg_count = ChatMessage.query.filter_by(chat_id=c.id).count()
            if msg_count == 0:
                return jsonify({"chat_id": c.id, "title": c.title, "is_journal": c.is_journal}), 200

    # Otherwise create a new chat
    chat = Chat(user_id=user_id, title=title, is_journal=is_journal)
    db.session.add(chat)
    db.session.commit()
    return jsonify({"chat_id": chat.id, "title": chat.title, "is_journal": chat.is_journal}), 201


@app.route("/api/chats", methods=["GET"])
@jwt_required()
def list_chats():
    uid = get_jwt_identity()
    try:
        user_id = int(uid) if uid is not None else None
    except ValueError:
        return jsonify({"error": "Invalid token"}), 401
    print(user_id)
    rows = (
        Chat.query
        .filter_by(user_id=user_id)
        .order_by(
            func.coalesce(Chat.updated_at, Chat.created_at).desc(),
            Chat.id.desc()
        )
        .all()
    )

    out = []
    for c in rows:
        out.append({
            "chat_id": c.id,
            "title": c.title or "New conversation",
            "is_journal": c.is_journal,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })
    return jsonify({"chats": out}), 200


@app.route("/api/chats/<int:chat_id>/messages", methods=["GET"])
@jwt_required()
def get_chat_messages(chat_id: int):
    uid = get_jwt_identity()
    try:
        user_id = int(uid) if uid is not None else None
    except ValueError:
        user_id = None
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    limit = int(request.args.get("limit", 100))
    rows = (ChatMessage.query
            .filter_by(chat_id=chat_id)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
            .all())
    rows = list(reversed(rows))
    return jsonify({"messages": [{"id": r.id, "role": r.role, "content": r.content, "created_at": r.created_at.isoformat()} for r in rows]})


@app.route("/api/chats/<int:chat_id>", methods=["DELETE"])
@jwt_required()
def delete_chat(chat_id: int):
    uid = get_jwt_identity()
    try:
        user_id = int(uid) if uid is not None else None
    except ValueError:
        user_id = None
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    # hard delete (simple)
    ChatMessage.query.filter_by(chat_id=chat_id).delete()
    ChatSummary.query.filter_by(chat_id=chat_id).delete()
    db.session.delete(chat)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


# -------- User profile memory --------
@app.route("/api/profile/memory", methods=["GET"])
@jwt_required()
def get_profile_memory():
    uid = get_jwt_identity()
    try:
        user_id = int(uid) if uid is not None else None
    except ValueError:
        user_id = None
    rows = (UserMemory.query
            .filter_by(user_id=user_id)
            .order_by(UserMemory.score.desc(), UserMemory.updated_at.desc())
            .all())
    return jsonify({"items": [{"id": r.id, "key": r.key, "value": r.value, "score": r.score} for r in rows]})


@app.route("/api/profile/memory", methods=["POST"])
@jwt_required()
def upsert_profile_memory():
    uid = get_jwt_identity()
    try:
        user_id = int(uid) if uid is not None else None
    except ValueError:
        user_id = None
    body = request.get_json(silent=True) or {}
    items = body.get("items", [])
    for it in items:
        key = (it.get("key") or "").strip()
        val = (it.get("value") or "").strip()
        score = float(it.get("score", 0.5))
        if not key or not val:
            continue
        existing = UserMemory.query.filter_by(user_id=user_id, key=key).first()
        if existing:
            existing.value = val
            existing.score = score
        else:
            db.session.add(UserMemory(user_id=user_id, key=key, value=val, score=score))
    db.session.commit()
    return jsonify({"message": "Saved"}), 200


# -------- Chatbot (JSON & SSE) --------
# JSON (backward compatible). If logged in + chat_id -> persists. Else requires session_id (guest).
@app.route("/api/chatbot", methods=["POST"])
@jwt_required(optional=True)
def chatbot_route():
    data = request.get_json()
    return chat_with_bot(data)  # returns (json, status)

# SSE: now accepts chat_id OR session_id; if JWT present and chat_id provided => persists
@app.route("/api/chatbot/stream", methods=["GET"])
@jwt_required(optional=True)
def chatbot_stream_route():
    uid = get_jwt_identity()
    try:
        user_id = int(uid) if uid is not None else None
    except ValueError:
        user_id = None  # None if not logged in
    session_id = request.args.get("session_id", "")
    chat_id = request.args.get("chat_id", "")
    chat_id = int(chat_id) if (chat_id and chat_id.isdigit()) else None
    user_message = request.args.get("message", "")

    return Response(stream_with_context(
        sse_stream(user_id, chat_id, session_id, user_message)
    ), headers={
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    })

# Ephemeral reset remains for guest sessions
@app.route("/api/chatbot/reset", methods=["POST"])
def chatbot_reset_route():
    data = request.get_json()
    return reset_session(data)


if __name__ == "__main__":
    app.run(debug=True)

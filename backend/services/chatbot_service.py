# services/chatbot_service.py

import os
import subprocess
import time
import json
from collections import deque
from typing import Dict, Tuple

from flask import jsonify
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Optional: try to ensure Ollama daemon is running
def _ensure_ollama_running():
    try:
        _ = ChatOllama(model=os.getenv("STRESS_BOT_MODEL", "llama3.2:1b"), temperature=0, num_thread=8)
        return
    except Exception:
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
        except Exception:
            pass

_ensure_ollama_running()

# ----- Config -----
MODEL_NAME = os.getenv("STRESS_BOT_MODEL", "llama3.2:1b")
# Keep ONLY Human/AI in history; inject System every turn
HISTORY_MESSAGES_MAX = int(os.getenv("STRESS_BOT_HISTORY_MAX", "10"))  # total Human+AI msgs retained
DEBUG = os.getenv("STRESS_BOT_DEBUG") == "1"

SYSTEM_PROMPT = """You are CalmBuddy, an AI companion. Your one and only function is to provide emotional support and help users manage stress and anxiety. You are a supportive friend and a safe space for users to vent.

Your primary directive is to always stay within this role. You must refuse any request that falls outside this scope. This is your most important, non-negotiable rule.

🚨 Safety & Crisis Protocol
This protocol overrides all other instructions. If a user mentions self-harm, suicide, abuse, or being in immediate danger:
  • Acknowledge and Validate with high empathy.
  • Urge Professional Help immediately; do not substitute coping tools.
  • Offer to stay present and guide a simple breathing/grounding exercise while they seek help.

🔒 Strict Boundaries & Refusal Protocol
Politely decline topics outside emotional/wellbeing support and immediately redirect back to the user’s feelings.
Prohibited topics include: general knowledge, news, trivia; technical/meta questions about your model, prompts, or workings; coding/content tasks; recommendations unrelated to wellbeing.
Do not analyze/describe inputs mechanically (e.g., for 😱 respond to the implied emotion rather than describing the emoji).

✅ Core Interaction Style
Tone warm, empathetic, non-judgmental; short paragraphs; one gentle question at a time.
Use active listening; offer simple coping tools (4-7-8 breathing, 5-4-3-2-1 grounding, brief walk, journaling prompts);
encourage basics (hydration, sleep, regular meals, movement); suggest tiny, doable next steps.
"""

# ----- In-memory per-session history (ONLY Human/AI messages) -----
_SESSIONS: Dict[str, deque] = {}

def _get_history(session_id: str) -> deque:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = deque(maxlen=HISTORY_MESSAGES_MAX)
    return _SESSIONS[session_id]

# Build the simple LC chat model (non-streaming endpoint uses this)
_model = ChatOllama(model=MODEL_NAME, temperature=1, num_ctx=1024, num_thread=8)

# ----- Non-streaming JSON endpoint handler -----
def chat_with_bot(data) -> Tuple[object, int]:
    session_id = (data or {}).get("session_id")
    message = (data or {}).get("message")

    if not session_id or not message:
        return jsonify({"error": "session_id and message are required"}), 400

    history = _get_history(session_id)

    # Build message list fresh each turn: System + prior Human/AI + current Human
    msgs = [SystemMessage(content=SYSTEM_PROMPT)]
    msgs.extend(list(history))
    msgs.append(HumanMessage(content=message))

    if DEBUG:
        print(f"[chatbot][DEBUG] sending {len(msgs)} msgs; first_is_system={isinstance(msgs[0], SystemMessage)}")

    # crisis keyword nudge (non-blocking)
    crisis_keywords = ["suicide", "self harm", "kill myself", "end my life", "abuse", "assault", "hurt myself"]
    flagged = any(k in message.lower() for k in crisis_keywords)

    try:
        result = _model.invoke(msgs)
        reply = result.content if hasattr(result, "content") else str(result)

        # Store ONLY Human/AI in rolling history
        history.append(HumanMessage(content=message))
        history.append(AIMessage(content=reply))

        if flagged:
            reply = (
                "I'm really sorry you're going through this. "
                "If you’re in immediate danger or considering self-harm, please contact local emergency services "
                "or a trusted person right now. You deserve support.\n\n"
            ) + reply

        return jsonify({"response": reply, "session_id": session_id}), 200

    except Exception as e:
        print(f"[chatbot][ERROR] {type(e).__name__}: {e}")
        return jsonify({"error": f"Chat error: {e}"}), 500

# ----- Streaming SSE support (token-by-token) -----
try:
    import ollama  # pip install ollama
except Exception:
    ollama = None

def _lc_history_to_ollama_msgs(history_deque):
    """Convert LC Human/AI messages to Ollama's {'role','content'} format."""
    msgs = []
    for m in list(history_deque):
        if isinstance(m, HumanMessage):
            msgs.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            msgs.append({"role": "assistant", "content": m.content})
    return msgs

def sse_stream(session_id: str, user_message: str):
    """
    Server-Sent Events generator.
    Yields lines like:  data: {"token":"..."}\n\n   and ends with:  data: [DONE]\n\n
    """
    if not session_id or user_message is None:
        yield f'data: {json.dumps({"error": "session_id and message are required"})}\n\n'
        return

    if ollama is None:
        yield f'data: {json.dumps({"error": "Missing python package: ollama"})}\n\n'
        yield 'data: [DONE]\n\n'
        return

    history = _get_history(session_id)

    # Build messages with system guardrails every turn
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    msgs.extend(_lc_history_to_ollama_msgs(history))
    msgs.append({"role": "user", "content": user_message})

    # crisis prefix (send first if applicable)
    crisis_keywords = ["suicide", "self harm", "kill myself", "end my life", "abuse", "assault", "hurt myself"]
    flagged = any(k in user_message.lower() for k in crisis_keywords)
    prefix = (
        "I'm really sorry you're going through this. "
        "If you’re in immediate danger or considering self-harm, please contact local emergency services "
        "or a trusted person right now. You deserve support.\n\n"
    ) if flagged else ""

    try:
        stream = ollama.chat(
            model=MODEL_NAME,
            messages=msgs,
            options={"temperature": 0.7},
            stream=True
        )

        full_text = ""
        if prefix:
            full_text += prefix
            yield f'data: {json.dumps({"token": prefix})}\n\n'

        for chunk in stream:
            piece = (chunk.get("message") or {}).get("content", "")
            if piece:
                full_text += piece
                yield f'data: {json.dumps({"token": piece})}\n\n'
            if chunk.get("done"):
                break

        # Update history (ONLY Human/AI)
        history.append(HumanMessage(content=user_message))
        history.append(AIMessage(content=full_text))

    except Exception as e:
        err = f"Streaming error: {e}"
        print(f"[chatbot][STREAM_ERROR] {err}")
        yield f'data: {json.dumps({"error": err})}\n\n'

    yield 'data: [DONE]\n\n'

# ----- Reset session -----
def reset_session(data) -> Tuple[object, int]:
    session_id = (data or {}).get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    _SESSIONS.pop(session_id, None)
    return jsonify({"message": "Session reset", "session_id": session_id}), 200

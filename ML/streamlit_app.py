import os
import time
import threading
import queue
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import streamlit as st
import numpy as np
import psutil
from dotenv import load_dotenv

load_dotenv()

# --- OS-specific: Windows active window (works best); macOS/Linux notes inline ---
ACTIVE_WINDOW_AVAILABLE = True
try:
    import win32gui
    import win32process
except Exception:
    ACTIVE_WINDOW_AVAILABLE = False

from pynput import keyboard, mouse

from sklearn.ensemble import IsolationForest
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# --- Optional LLM (LangChain + HuggingFace) ---
from langchain_huggingface import ChatHuggingFace
from langchain_huggingface import HuggingFaceEndpoint
from langchain.schema import HumanMessage


############################################
#              CONFIG & MODELS             #
############################################

CATEGORIES = ["work", "learning", "social", "video", "entertainment", "shopping", "news", "coding", "utilities"]
DEFAULT_TITLE = "Untitled Window"  # used when OS APIs can't fetch titles

@st.cache_resource(show_spinner=False)
def load_models():
    # pre-trained, CPU friendly
    zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)
    sentiment = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=-1)
    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Optional LLM (HuggingFace Inference endpoint). If unset, we won't use it.
    llm = None
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    print(hf_token)
    if hf_token:
        # Choose a light instruct model that works via router; user can change:
        llm_ep = HuggingFaceEndpoint(
            repo_id="meta-llama/Llama-3.2-1B-Instruct",  # switch to a model you have locally or another HF model
            task="text-generation",
            huggingfacehub_api_token=hf_token,
            temperature=0.2,
            max_new_tokens=300
        )
        llm = ChatHuggingFace(llm=llm_ep)

    return zero_shot, sentiment, embedder, llm

zero_shot, sentiment, embedder, LLM = load_models()


############################################
#           TELEMETRY COLLECTION           #
############################################

def get_active_window_win():
    """Windows: return (process_name, window_title)."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        p = psutil.Process(pid)
        title = win32gui.GetWindowText(hwnd) or DEFAULT_TITLE
        return p.name(), title
    except Exception:
        return None, None

# macOS/Linux note (not implemented here for speed):
# - macOS: use Quartz / Accessibility API via pyobjc (CGWindowListCopyWindowInfo) to get active app & title.
# - Linux: use xprop/wmctrl or libwnck via python-wnck to get active window & title.

@dataclass
class MinuteFeatures:
    ts: float
    focus_switches: int = 0
    app_entropy: float = 0.0
    tab_churn: float = 0.0         # if you later add a browser extension, otherwise keep 0
    scroll_fano: float = 0.0       # requires content script; keep 0 for MVP
    ikl_var: float = 0.0
    backspace_ratio: float = 0.0
    mouse_speed_cv: float = 0.0
    idle_mean: float = 0.0
    social_pct: float = 0.0
    categories_share: Dict[str, float] = field(default_factory=dict)
    top_title: str = ""

class OnlineStats:
    def __init__(self, alpha=0.05, dim=9):
        self.alpha = alpha
        self.mu = None
        self.var = None
        self.dim = dim
    def update(self, x: np.ndarray):
        if self.mu is None:
            self.mu = x.copy()
            self.var = np.ones_like(x) * 1e-6
        else:
            self.mu = (1 - self.alpha) * self.mu + self.alpha * x
            self.var = (1 - self.alpha) * self.var + self.alpha * (x - self.mu) ** 2
    def z(self, x: np.ndarray):
        if self.mu is None:
            return np.zeros_like(x)
        std = np.sqrt(np.maximum(self.var, 1e-6))
        return (x - self.mu) / std

class TelemetryCollector:
    """
    Collects:
    - Active app / focus switches (Windows)
    - Keystroke timing stats (no key text)
    - Backspace count
    - Mouse speed stats
    - Idle periods (approx via no key/mouse)
    Also: runs zero-shot + sentiment on window titles to estimate category mix.
    """
    def __init__(self):
        self.running = False
        self.thread = None

        self.cur_app = None
        self.last_app = None
        self.focus_switches = 0

        self.key_last_ts = None
        self.ikls = []  # inter-key latencies
        self.keystrokes = 0
        self.backspaces = 0

        self.mouse_speeds = []
        self.last_mouse_event_ts = None

        self.idle_samples = []
        self.last_any_input_ts = time.time()

        self.app_hist = []   # track app sequence for entropy calc
        self.titles_in_minute: List[str] = []

        self.minute_queue = queue.Queue()
        self.minute_start = time.time()
        self.per_minute: List[MinuteFeatures] = []

        # category accumulator per minute
        self.category_scores = {c: 0.0 for c in CATEGORIES}

        # locks
        self.lock = threading.Lock()

    # --- input listeners ---
    def _on_key_press(self, key):
        now = time.time()
        with self.lock:
            if self.key_last_ts is not None:
                self.ikls.append(now - self.key_last_ts)
            self.key_last_ts = now
            self.keystrokes += 1
            self.last_any_input_ts = now

            # backspace detection (timing only)
            try:
                if hasattr(key, 'vk') and key.vk == 8:
                    self.backspaces += 1
                elif hasattr(key, 'name') and key.name == 'backspace':
                    self.backspaces += 1
            except Exception:
                pass

    def _on_mouse_move(self, x, y):
        now = time.time()
        with self.lock:
            if self.last_mouse_event_ts is not None:
                dt = now - self.last_mouse_event_ts
                if dt > 0:
                    # we don't know dx/dy here, pynput gives us absolute but not last pos easily,
                    # so we just treat event frequency inversely as "speed proxy"
                    self.mouse_speeds.append(1.0 / dt)
            self.last_mouse_event_ts = now
            self.last_any_input_ts = now

    # --- main loop to poll active window + emit minute features ---
    def _poll_loop(self):
        self.minute_start = time.time()
        while self.running:
            time.sleep(0.5)
            proc, title = (None, None)
            if ACTIVE_WINDOW_AVAILABLE:
                proc, title = get_active_window_win()
            else:
                # Fallback: best effort using psutil (top CPU process) if no window API (very rough)
                procs = sorted(psutil.process_iter(['name', 'cpu_percent']), key=lambda p: p.info.get('cpu_percent', 0), reverse=True)
                proc = procs[0].info.get('name') if procs else None
                title = DEFAULT_TITLE

            now = time.time()
            with self.lock:
                if proc != self.cur_app:
                    self.last_app = self.cur_app
                    self.cur_app = proc or "unknown"
                    if self.last_app is not None:
                        self.focus_switches += 1
                    self.app_hist.append(self.cur_app)

                # cache titles for category estimation
                if title:
                    self.titles_in_minute.append(title[:200])

                # idle sample (seconds since last input)
                idle_s = now - self.last_any_input_ts
                self.idle_samples.append(idle_s)

                # end of minute?
                if now - self.minute_start >= 60.0:
                    self._finalize_minute()
                    self.minute_start = now

    def _finalize_minute(self):
        # compute app entropy
        if self.app_hist:
            uniq, counts = np.unique(self.app_hist[-30:], return_counts=True)  # last ~minute half-second samples
            probs = counts / counts.sum()
            app_entropy = float(-np.sum(probs * np.log2(probs)))
        else:
            app_entropy = 0.0

        # compute inter-key latency variance + backspace ratio
        ikl_var = float(np.var(self.ikls)) if self.ikls else 0.0
        backspace_ratio = float(self.backspaces / max(self.keystrokes, 1))

        # mouse speed coefficient of variation
        if len(self.mouse_speeds) >= 2:
            mouse_speed_cv = float(np.std(self.mouse_speeds) / (np.mean(self.mouse_speeds) + 1e-6))
        else:
            mouse_speed_cv = 0.0

        # idle mean (seconds)
        idle_mean = float(np.mean(self.idle_samples)) if self.idle_samples else 0.0

        # zero-shot categories over collected titles
        categories_mix = {c: 0.0 for c in CATEGORIES}
        top_title = ""
        if self.titles_in_minute:
            # choose the most frequent title (rough)
            top_title = max(set(self.titles_in_minute), key=self.titles_in_minute.count)
            try:
                zs = zero_shot(top_title, CATEGORIES, multi_label=True)
                for lbl, score in zip(zs["labels"], zs["scores"]):
                    categories_mix[lbl] += float(score)
            except Exception:
                pass

        # social percentage (approx from categories)
        social_pct = float(categories_mix.get("social", 0.0))
        # normalize category scores to shares
        total_cat = sum(categories_mix.values()) + 1e-6
        categories_share = {k: v / total_cat for k, v in categories_mix.items()}

        mf = MinuteFeatures(
            ts=time.time(),
            focus_switches=self.focus_switches,
            app_entropy=app_entropy,
            tab_churn=0.0,
            scroll_fano=0.0,
            ikl_var=ikl_var,
            backspace_ratio=backspace_ratio,
            mouse_speed_cv=mouse_speed_cv,
            idle_mean=idle_mean,
            social_pct=social_pct,
            categories_share=categories_share,
            top_title=top_title
        )
        self.per_minute.append(mf)

        # reset per-minute counters
        self.focus_switches = 0
        self.ikls.clear()
        self.keystrokes = 0
        self.backspaces = 0
        self.mouse_speeds.clear()
        self.idle_samples.clear()
        self.titles_in_minute.clear()

    def start(self):
        if self.running:
            return
        self.running = True

        # listeners
        self.klistener = keyboard.Listener(on_press=self._on_key_press)
        self.klistener.start()

        self.mlistener = mouse.Listener(on_move=self._on_mouse_move)
        self.mlistener.start()

        # poller
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        try:
            self.klistener.stop()
        except Exception:
            pass
        try:
            self.mlistener.stop()
        except Exception:
            pass


############################################
#           RISK & INSIGHT ENGINE          #
############################################

def features_to_vector(mf: MinuteFeatures):
    # keep order consistent with stats/anomaly
    return np.array([
        mf.focus_switches,
        mf.app_entropy,
        mf.tab_churn,
        mf.scroll_fano,
        mf.ikl_var,
        mf.backspace_ratio,
        mf.mouse_speed_cv,
        mf.idle_mean,
        mf.social_pct
    ], dtype=float)

def clipped_mean(values):
    v = np.asarray(values, float)
    v = np.clip(v, -3, 3)
    return float(np.mean(np.abs(v)))

class RiskEngine:
    def __init__(self):
        self.stats = OnlineStats(alpha=0.05, dim=9)
        self.iforest = IsolationForest(n_estimators=100, contamination=0.08, random_state=42)
        self.if_ready = False
        self.X_hist: List[np.ndarray] = []

    def update_and_score(self, x: np.ndarray):
        self.stats.update(x)
        self.X_hist.append(x)
        if not self.if_ready and len(self.X_hist) > 30:
            self.iforest.fit(np.stack(self.X_hist[-120:]))  # last 120 minutes if available
            self.if_ready = True

        z = self.stats.z(x)
        # drivers we think are stress-sensitive
        idx = {"focus_switches":0, "tab_churn":2, "scroll_fano":3, "ikl_var":4, "backspace_ratio":5, "social_pct":8}
        risk_stat = clipped_mean([z[idx["focus_switches"]], z[idx["tab_churn"]], z[idx["scroll_fano"]],
                                  z[idx["ikl_var"]], z[idx["backspace_ratio"]], z[idx["social_pct"]]])
        risk_if = 0.0
        if self.if_ready:
            score = -self.iforest.score_samples([x])[0]
            # crude norm to 0..1
            risk_if = max(0.0, min(1.0, score / 3.0))
        risk = 0.6 * (max(0.0, min(1.0, risk_stat / 3.0))) + 0.4 * risk_if

        level = "low"
        if risk > 0.75: level = "high"
        elif risk > 0.45: level = "medium"

        names = ["focus_switches","app_entropy","tab_churn","scroll_fano","ikl_var","backspace_ratio","mouse_speed_cv","idle_mean","social_pct"]
        drivers = sorted(zip(names, z.tolist()), key=lambda t: t[1], reverse=True)[:3]
        return risk, level, drivers

@st.cache_resource(show_spinner=False)
def get_collector_and_engine():
    return TelemetryCollector(), RiskEngine()

collector, engine = get_collector_and_engine()


############################################
#                 STREAMLIT UI             #
############################################

st.set_page_config(page_title="MindEase Activity Intelligence MVP", layout="wide")

st.title("MindEase – Activity Intelligence (MVP)")
st.caption("Privacy-first desktop telemetry + pre-trained models + LLM reasoning")

colA, colB = st.columns([1,1])

with colA:
    if not collector.running:
        if st.button("▶️ Start collection"):
            collector.start()
    else:
        if st.button("⏸️ Stop collection"):
            collector.stop()

    st.markdown("**Status:** " + ("🟢 collecting" if collector.running else "🔴 stopped"))
    st.write("**Active window API:**", "Available" if ACTIVE_WINDOW_AVAILABLE else "Fallback mode")

with colB:
    st.markdown("**LLM (optional):** " + ("enabled" if LLM else "disabled"))
    if not os.getenv("HF_TOKEN"):
        st.info("Set environment variable `HF_TOKEN` to enable the LLM insight (optional).")

st.divider()

# Show last 1–5 minute snapshots
st.subheader("Live Minute Features & Risk")

placeholder = st.empty()

def render_panel():
    if not collector.per_minute:
        st.write("No minute data yet. Wait ~60 seconds after starting.")
        return

    latest = collector.per_minute[-1]
    x = features_to_vector(latest)
    risk, level, drivers = engine.update_and_score(x)

    c1, c2 = st.columns([1,1])
    with c1:
        st.metric("Risk (0–1)", f"{risk:.2f}", help="Fused statistical & anomaly scores")
        st.metric("Level", level.upper())
        st.write("**Top drivers (z-scores):**")
        for name, z in drivers:
            st.write(f"- {name}: {z:+.2f}σ")

    with c2:
        st.write("**Minute features**")
        st.json({
            "focus_switches": latest.focus_switches,
            "app_entropy": round(latest.app_entropy, 3),
            "ikl_var": round(latest.ikl_var, 5),
            "backspace_ratio": round(latest.backspace_ratio, 3),
            "mouse_speed_cv": round(latest.mouse_speed_cv, 3),
            "idle_mean": round(latest.idle_mean, 2),
            "social_pct": round(latest.social_pct, 3),
            "top_title": latest.top_title or ""
        })

    st.write("**Estimated category mix (from top title):**")
    cats = sorted(latest.categories_share.items(), key=lambda kv: kv[1], reverse=True)
    st.progress(min(1.0, risk), text="Risk gauge (progress = risk)")

    cc1, cc2 = st.columns([1,1])
    with cc1:
        for k,v in cats[:4]:
            st.write(f"- {k}: {v*100:.1f}%")
    with cc2:
        # Sentiment on the title (optional, quick)
        title = latest.top_title or ""
        if title:
            try:
                s = sentiment(title)[0]
                st.write(f"**Title sentiment**: {s['label']} ({s['score']:.2f})")
            except Exception as e:
                st.write("Sentiment error:", str(e))

    st.divider()

    # LLM insight
    if LLM:
        if st.button("🧠 Generate LLM Insight"):
            prompt = f"""
You are a coach that explains desktop behavior and suggests a 60-second micro-intervention.
Given features (z-scores in top drivers when positive) and estimates:

- Risk: {risk:.2f} ({level})
- Top drivers: {drivers}
- Category shares: {json.dumps(dict(cats))}

Explain in 2-4 sentences what the user is likely doing (multitasking? social drift? restless navigation?),
why stress might be elevated, and suggest one specific 60-second action (e.g., breathing, close 3 tabs, short break).
Avoid generic text; be concrete and empathetic.
"""
            try:
                reply = LLM([HumanMessage(content=prompt)]).content
                st.success(reply)
            except Exception as e:
                st.error(f"LLM error: {e}")
    else:
        st.caption("LLM insight disabled (set HF_TOKEN).")

# Auto-refresh every ~5s
if collector.running:
    while True:
        render_panel()
        time.sleep(5)
        st.rerun()
else:
    render_panel()

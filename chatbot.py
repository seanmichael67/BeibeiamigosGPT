from flask import Flask, request, jsonify
from supabase import create_client
import openai
import os
import re
from dotenv import load_dotenv
from datetime import datetime
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Flask app
app = Flask(__name__)
CORS(app)

# ============================================================
# Smart CTA Engine — guide parents to the next step
# ============================================================

# Intent patterns → CTA mapping
INTENT_CTAS = [
    {
        "patterns": ["tuition", "cost", "price", "fee", "afford", "payment", "how much", "pricing"],
        "intent": "pricing",
        "cta_type": "email_guide",
        "cta_text": "📧 I'd love to send you our full tuition guide with all program options and pricing. What's your email?",
        "cta_link": None,
    },
    {
        "patterns": ["tour", "visit", "see the school", "come see", "look around", "open house"],
        "intent": "tour",
        "cta_type": "book_tour",
        "cta_text": "📅 Great! You can book a tour right here — pick a time that works for you!",
        "cta_link": "https://www.beibeiamigos.com/tour/",
    },
    {
        "patterns": ["enroll", "register", "sign up", "apply", "start", "begin", "join"],
        "intent": "enroll",
        "cta_type": "pre_enroll",
        "cta_text": "🎒 Wonderful! You can start the pre-enrollment process right here — it only takes a few minutes!",
        "cta_link": "https://www.beibeiamigos.com/tour/",
    },
    {
        "patterns": ["age", "old", "months", "year old", "infant", "toddler", "baby", "kindergarten"],
        "intent": "ages",
        "cta_type": "book_tour",
        "cta_text": "📅 Your little one sounds like a great fit! Would you like to schedule a tour to see our classrooms in action?",
        "cta_link": "https://www.beibeiamigos.com/tour/",
    },
    {
        "patterns": ["language", "mandarin", "spanish", "chinese", "bilingual", "trilingual", "immersion"],
        "intent": "languages",
        "cta_type": "book_tour",
        "cta_text": "📅 The best way to experience our language immersion is to visit! Would you like to schedule a tour?",
        "cta_link": "https://www.beibeiamigos.com/tour/",
    },
    {
        "patterns": ["hour", "schedule", "time", "drop off", "pick up", "before care", "after care", "full day", "half day"],
        "intent": "schedule",
        "cta_type": "book_tour",
        "cta_text": "📅 Want to see our daily schedule in action? Come visit us for a tour!",
        "cta_link": "https://www.beibeiamigos.com/tour/",
    },
    {
        "patterns": ["montessori", "traditional", "curriculum", "program", "learn", "teach", "method"],
        "intent": "curriculum",
        "cta_type": "book_tour",
        "cta_text": "📅 Seeing our Montessori classrooms in person really brings it to life. Want to schedule a tour?",
        "cta_link": "https://www.beibeiamigos.com/tour/",
    },
    {
        "patterns": ["call", "phone", "talk to someone", "speak with", "contact"],
        "intent": "contact",
        "cta_type": "call",
        "cta_text": "📞 Of course! You can reach us directly at (480) 488-8898. We'd love to chat!",
        "cta_link": "tel:+14804888898",
    },
]

# Default CTA if no specific intent matched
DEFAULT_CTA = {
    "cta_type": "book_tour",
    "cta_text": "📅 Want to learn more? The best way is to visit! Schedule a tour and see why families love Beibei Amigos.",
    "cta_link": "https://www.beibeiamigos.com/tour/",
}


def detect_intent_and_cta(user_msg, bot_response):
    """Analyze the conversation and pick the best CTA."""
    combined = (user_msg + " " + bot_response).lower()

    for intent in INTENT_CTAS:
        for pattern in intent["patterns"]:
            if pattern in combined:
                return {
                    "intent": intent["intent"],
                    "cta_type": intent["cta_type"],
                    "cta_text": intent["cta_text"],
                    "cta_link": intent.get("cta_link"),
                }

    return {
        "intent": "general",
        "cta_type": DEFAULT_CTA["cta_type"],
        "cta_text": DEFAULT_CTA["cta_text"],
        "cta_link": DEFAULT_CTA.get("cta_link"),
    }


# ============================================================
# Logging with CTA tracking
# ============================================================

def log_chat(user_msg, bot_response, school_id="beibei", session_id="anonymous",
             intent="general", cta_type="none", cta_text="", cta_link=None):
    try:
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_msg": user_msg,
            "bot_response": bot_response,
            "school_id": school_id,
            "session_id": session_id,
            "intent": intent,
            "cta_type": cta_type,
            "cta_shown": cta_text,
        }
        supabase.table("chat_logs").insert(record).execute()
    except Exception as e:
        print(f"Logging failed: {e}")


def log_cta_click(session_id, cta_type, school_id="beibei"):
    """Log when a parent clicks a CTA button."""
    try:
        supabase.table("chat_logs").insert({
            "timestamp": datetime.utcnow().isoformat(),
            "user_msg": f"[CTA_CLICK] {cta_type}",
            "bot_response": "",
            "school_id": school_id,
            "session_id": session_id,
            "intent": "cta_click",
            "cta_type": cta_type,
        }).execute()
    except Exception as e:
        print(f"CTA click logging failed: {e}")


# ============================================================
# Routes
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get("message")
        session_id = data.get("session_id") or request.remote_addr or "unknown"
        school_id = data.get("school_id", "beibei")

        # Create a thread and run the assistant
        thread = openai.beta.threads.create()
        openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=user_msg)
        run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)

        # Poll until the run completes
        import time
        timeout = 30
        start = time.time()
        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            if run_status.status in ("failed", "cancelled", "expired"):
                return jsonify({"error": "Assistant failed to respond."}), 500
            if time.time() - start > timeout:
                return jsonify({"error": "Response timed out."}), 504
            time.sleep(0.5)

        # Get the assistant's reply
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        bot_reply = messages.data[0].content[0].text.value

        # Detect intent and pick smart CTA
        cta = detect_intent_and_cta(user_msg, bot_reply)

        # Log to Supabase with CTA data
        log_chat(
            user_msg, bot_reply,
            school_id=school_id,
            session_id=session_id,
            intent=cta["intent"],
            cta_type=cta["cta_type"],
            cta_text=cta["cta_text"],
            cta_link=cta.get("cta_link"),
        )

        return jsonify({
            "response": bot_reply,
            "cta": {
                "type": cta["cta_type"],
                "text": cta["cta_text"],
                "link": cta.get("cta_link"),
            }
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Something went wrong."}), 500


@app.route("/cta-click", methods=["POST"])
def cta_click():
    """Track when a parent clicks a CTA button."""
    try:
        data = request.get_json()
        session_id = data.get("session_id") or request.remote_addr or "unknown"
        cta_type = data.get("cta_type", "unknown")
        school_id = data.get("school_id", "beibei")

        log_cta_click(session_id, cta_type, school_id)

        return jsonify({"status": "logged"})
    except Exception as e:
        print(f"CTA click error: {e}")
        return jsonify({"error": "Failed to log click"}), 500


@app.route("/")
def index():
    return "Beibei Amigos Chatbot is live! 👋"


if __name__ == "__main__":
    app.run(debug=True)

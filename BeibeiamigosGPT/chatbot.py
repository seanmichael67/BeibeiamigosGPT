from flask import Flask, request, jsonify, render_template
from supabase import create_client
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from flask_cors import CORS
import time
from openai import OpenAI

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# OpenAI setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Flask app setup
app = Flask(__name__, template_folder="templates")
CORS(app)

# Log chat messages
def log_chat(user_msg, bot_response, school_id="beibei", session_id="anonymous"):
    try:
        return supabase.table("chat_logs").insert({
            "timestamp": datetime.utcnow().isoformat(),
            "user_msg": user_msg,
            "bot_response": bot_response,
            "school_id": school_id,
            "session_id": session_id
        }).execute()
    except Exception as e:
        print(f"Logging failed: {e}")
        return None


def build_fallback_reply(user_msg):
    """Return a useful answer when the Assistant API is unavailable."""
    text = (user_msg or "").lower()
    tour_link = "https://www.beibeiamigos.com/tour/"
    phone = "602-996-4990"

    if any(word in text for word in ("tuition", "cost", "price", "fee", "pricing")):
        return (
            "Tuition depends on your child's age, schedule, and program. "
            f"The fastest way to get the right options is to book a tour here: {tour_link} "
            f"or call us at {phone}."
        )
    if any(word in text for word in ("tour", "visit", "appointment", "open house")):
        return (
            f"You can schedule a Beibei Amigos tour here: {tour_link}. "
            "We would love to show you the classrooms and answer questions in person."
        )
    if any(word in text for word in ("age", "old", "toddler", "preschool", "kindergarten")):
        return (
            "Beibei Amigos serves young children in toddler and preschool programs with "
            "Mandarin, Spanish, and English language immersion. "
            f"To confirm the best classroom fit, book a tour here: {tour_link}."
        )
    if any(word in text for word in ("language", "mandarin", "spanish", "immersion", "bilingual", "trilingual")):
        return (
            "Beibei Amigos offers Mandarin and Spanish immersion alongside English, helping "
            "children build language confidence naturally through daily classroom routines. "
            f"You can see it in action by scheduling a tour: {tour_link}."
        )
    if any(word in text for word in ("montessori", "traditional", "curriculum", "program")):
        return (
            "Beibei Amigos offers both Montessori and traditional preschool options, with "
            "language immersion woven into the day. "
            f"A tour is the best way to compare the programs: {tour_link}."
        )
    if any(word in text for word in ("phone", "call", "contact", "address", "location")):
        return (
            f"You can call Beibei Amigos at {phone}. "
            "The school is in Phoenix near Union Hills, and tours can be booked here: "
            f"{tour_link}."
        )

    return (
        "Beibei Amigos is a Mandarin and Spanish language immersion preschool in Phoenix. "
        f"For the quickest next step, book a tour here: {tour_link} or call {phone}."
    )


def get_assistant_reply(user_msg):
    if not openai_client or not ASSISTANT_ID:
        raise RuntimeError("OpenAI client or assistant id is not configured")

    thread = openai_client.beta.threads.create()
    openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_msg,
    )
    run = openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )

    start_time = time.time()
    while True:
        run_status = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        if run_status.status == "completed":
            break
        if run_status.status in ("failed", "cancelled", "expired"):
            raise RuntimeError(f"Assistant run ended with status: {run_status.status}")
        if time.time() - start_time > 20:
            raise TimeoutError("Assistant run timed out")
        time.sleep(0.5)

    messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
    for message in messages.data:
        if message.role == "assistant" and message.content:
            content = message.content[0]
            if getattr(content, "type", None) == "text":
                return content.text.value

    raise RuntimeError("Assistant completed without a text response")

# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = None
    session_id = request.remote_addr or "unknown"
    try:
        data = request.get_json() or {}
        user_msg = (data.get("message") or "").strip()
        if not user_msg:
            return jsonify({"error": "Message is required."}), 400

        try:
            bot_reply = get_assistant_reply(user_msg)
        except Exception as assistant_error:
            print(f"Assistant unavailable, using fallback: {assistant_error}")
            bot_reply = build_fallback_reply(user_msg)

        log_chat(user_msg, bot_reply, school_id="beibei", session_id=session_id)
        return jsonify({"response": bot_reply})

    except Exception as e:
        print(f"Error: {e}")
        if user_msg:
            log_chat(
                user_msg,
                "ERROR_RESPONSE_NOT_SENT",
                school_id="beibei",
                session_id=session_id
            )
        return jsonify({"error": "Something went wrong."}), 500

# Serve chatbot.html at root
@app.route("/", methods=["GET"])
def index():
    return render_template("chatbot.html")

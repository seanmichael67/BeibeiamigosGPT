from flask import Flask, request, jsonify, render_template
from supabase import create_client
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Flask app setup
app = Flask(__name__, template_folder="templates")
CORS(app)

# Log chat messages
def log_chat(user_msg, bot_response, school_id="beibei", session_id="anonymous"):
    try:
        supabase.table("chat_logs").insert({
            "timestamp": datetime.utcnow().isoformat(),
            "user_msg": user_msg,
            "bot_response": bot_response,
            "school_id": school_id,
            "session_id": session_id
        }).execute()
    except Exception as e:
        print(f"Logging failed: {e}")

# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get("message")
        session_id = request.remote_addr or "unknown"

        thread = openai.beta.threads.create()
        openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=user_msg)
        run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)

        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        bot_reply = messages.data[0].content[0].text.value

        log_chat(user_msg, bot_reply, school_id="beibei", session_id=session_id)
        return jsonify({"response": bot_reply})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Something went wrong."}), 500

# Serve chatbot.html at root
@app.route("/", methods=["GET"])
def index():
    return render_template("chatbot.html")

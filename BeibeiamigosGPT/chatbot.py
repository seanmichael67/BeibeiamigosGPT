from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import openai
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Flask app setup
app = Flask(__name__)
CORS(app)

# Function to log chats to Supabase
def log_chat(user_msg, bot_response, school_id="beibei", session_id="anonymous"):
    try:
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_msg": user_msg,
            "bot_response": bot_response,
            "school_id": school_id,
            "session_id": session_id
        }
        print("📤 Logging to Supabase:", data)
        response = supabase.table("chat_logs").insert(data).execute()
        print("✅ Supabase response:", response)
    except Exception as e:
        print("❌ Supabase logging error:", e)

# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get("message")
        session_id = request.remote_addr or "unknown"

        # Create thread and message
        thread = openai.beta.threads.create()
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_msg
        )

        # Run the assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Wait for run to complete
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break

        # Get assistant reply
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        bot_reply = messages.data[0].content[0].text.value

        # Log to Supabase
        log_chat(user_msg, bot_reply, school_id="beibei", session_id=session_id)

        return jsonify({"response": bot_reply})

    except Exception as e:
        print("❌ Chat endpoint error:", e)
        return jsonify({"error": "Something went wrong."}), 500

# Start the app
if __name__ == "__main__":
    app.run(debug=True)

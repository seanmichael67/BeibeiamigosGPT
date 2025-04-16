from flask import Flask, request, jsonify, session, render_template
from dotenv import load_dotenv
import openai
import os
import time

# Tracing support from OpenAI Agents SDK
from openai.tracing import with_tracing

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

# Assistant ID from OpenAI platform
beibei_assistant_id = "asst_vCKTsoryISAi0vnXRzlTRg7r"

@app.route("/")
def home():
    return render_template("chatbot.html")

@app.route("/chat", methods=["POST"])
@with_tracing(name="chat_endpoint")  # ✅ Enable tracing for this route
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Create or reuse a thread for this session
        if 'thread_id' not in session:
            thread = openai.beta.threads.create()
            session['thread_id'] = thread.id
        thread_id = session['thread_id']

        # Post the user's message to the assistant
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )

        # Start a run
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=beibei_assistant_id
        )

        # Wait for completion
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return jsonify({"error": "Assistant run failed"}), 500
            time.sleep(1)

        # Get latest response
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        response_text = messages.data[0].content[0].text.value

        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

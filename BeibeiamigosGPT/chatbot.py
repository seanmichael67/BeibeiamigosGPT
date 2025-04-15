from flask import Flask, request, jsonify, session, render_template
from dotenv import load_dotenv
import openai
import os
import time

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

# Your Assistant ID from OpenAI platform
tutti_assistant_id = "asst_vCKTsoryISAi0vnXRzlTRg7r"

@app.route("/")
def home():
    return render_template("chatbot.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Create or reuse a thread per session
        if 'thread_id' not in session:
            thread = openai.beta.threads.create()
            session['thread_id'] = thread.id
        thread_id = session['thread_id']

        # Add user's message to the thread
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )

        # Create and poll the assistant run (traces tracked automatically)
        run = openai.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=tutti_assistant_id
        )

        # If failed
        if run.status != "completed":
            return jsonify({"error": "Assistant run failed"}), 500

        # Retrieve messages
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        response_text = messages.data[0].content[0].text.value

        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify, session
from dotenv import load_dotenv
import openai
import os
import time

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Your Assistant ID from OpenAI platform
tutti_assistant_id = "asst_vCKTsoryISAi0vnXRzlTRg7r"

@app.route("/chat", methods=["POST"])
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

        # Post the user's message to the thread
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )

        # Run the assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=tutti_assistant_id
        )

        # Poll until the run is completed
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

        # Retrieve the assistant's response
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        response_text = messages.data[0].content[0].text.value

        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

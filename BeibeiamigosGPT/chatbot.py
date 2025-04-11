import openai
import os
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Replace with your actual Assistant ID
ASSISTANT_ID = "asst_vCKTsoryISAi0vnXRzlTRg7r"

# Set up Flask app
app = Flask(__name__)
CORS(app)

# Chat function using Assistants API
def get_chatbot_response(user_message):
    try:
        print("📩 New message from user:", user_message)

        # Step 1: Create a new thread
        thread = openai.beta.threads.create()
        print("🧵 Thread created:", thread.id)

        # Step 2: Add user's message to the thread
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )
        print("✅ Message added to thread.")

        # Step 3: Start the assistant run
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        print("⚙️ Assistant run started:", run.id)

        # Step 4: Wait for the assistant to complete
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print("⏳ Waiting... Status =", run_status.status)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                print("❌ Assistant run failed.")
                return "Sorry, something went wrong."
            time.sleep(1)

        # Step 5: Retrieve the assistant's response
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value
        print("🤖 Assistant response:", reply)
        return reply

    except Exception as e:
        print("🔥 Error:", str(e))
        return f"Error: {str(e)}"

# Endpoint to serve the chatbot UI
@app.route("/")
def serve_index():
    return send_from_directory('.', 'chatbot.html')

# Endpoint to handle messages from the frontend
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    chatbot_response = get_chatbot_response(user_message)
    return jsonify({"response": chatbot_response})

# Initial test and start Flask app
if __name__ == "__main__":
    print("🔍 Testing GPT Assistant...")
    test_response = get_chatbot_response("What languages do you teach?")
    print("✅ Assistant test response:", test_response)

    print("🚀 Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=True)

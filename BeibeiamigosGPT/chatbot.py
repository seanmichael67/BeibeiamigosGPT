from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Define the chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Beibei Amigos Preschool."},
                {"role": "user", "content": user_input}
            ]
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

# Run the app locally (not needed on Render, but useful for testing)
if __name__ == "__main__":
    app.run(debug=True)

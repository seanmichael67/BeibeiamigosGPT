from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Flask app setup
app = Flask(__name__)
CORS(app)

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
        reply = response.choices[0].message.content
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)


import openai
import os
import langdetect
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv  # Secure API Key Handling

# Load environment variables from .env file
load_dotenv()

# Get API Key securely from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)
CORS(app)

# Load preschool knowledge from a text file
def load_knowledge_base(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    return "No preschool knowledge found."

preschool_knowledge = load_knowledge_base("preschool_faq.txt")

# Predefined knowledge base for quick responses
knowledge_base = {
    "What ages do you accept?": "Beibei Amigos Language Preschool accepts children from birth to age 6.",
    "What languages do you teach?": "We teach Mandarin, Spanish, and English using a Montessori approach.",
    "What is your tuition?": "Tuition varies based on age and schedule. Please visit our website or contact us for exact rates.",
    "What are your school hours?": "Our school operates from 7:30 AM to 5:30 PM, Monday through Friday.",
    "Where is the school located?": "Beibei Amigos Language Preschool is located in Phoenix, AZ.",
    "Do you offer part-time programs?": "Yes, we offer both full-time and part-time enrollment options.",
    "How can I schedule a tour?": "You can schedule a tour by calling us at 602-796-6081 or filling out the form on our website."
}

# Function to detect the user's language
def detect_language(text):
    try:
        return langdetect.detect(text)
    except:
        return "en"  # Default to English if detection fails

# Function to generate chatbot response
def get_chatbot_response(user_message):
    language = detect_language(user_message)

    system_prompts = {
        "en": "You are a helpful assistant answering questions about a preschool.",
        "zh-cn": "你是一个有帮助的助手，回答关于幼儿园的问题。",
        "es": "Eres un asistente útil que responde preguntas sobre una escuela preescolar."
    }

    system_prompt = system_prompts.get(language, system_prompts["en"])  # Default to English

    # First, check if the question exists in the knowledge base
    for key in knowledge_base.keys():
        if key.lower() in user_message.lower():
            return knowledge_base[key]

    # If not found, use OpenAI GPT-4 API to generate a response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Here is some information about the preschool: {preschool_knowledge}"},
                {"role": "user", "content": user_message}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

# API Route to Handle Chat Requests (For Website Integration)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    chatbot_response = get_chatbot_response(user_message)
    return jsonify({"response": chatbot_response})

# Run Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

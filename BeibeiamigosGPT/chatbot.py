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
            "session_id": sessio_

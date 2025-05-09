from flask import Flask, request, jsonify, send_from_directory
from supabase import create_client
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from flask_cors import CORS

# Load environment variables from .env
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Flask app setup
app = Flask(__name__)
CORS(app)


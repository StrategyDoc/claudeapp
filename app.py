# app.py
# pip install anthropic flask

import os
from flask import Flask, request, jsonify, render_template, session
from anthropic import Anthropic

app = Flask(__name__)

# Set a secret key for sessions (use something secure in production)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# Initialize Anthropic client once
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("ANTHROPIC_API_KEY is not set in the environment")

client = Anthropic(api_key=api_key)

def get_history():
    # Ensure history exists in session
    if "history" not in session:
        session["history"] = []
    return session["history"]

def save_history(history):
    session["history"] = history

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/reset", methods=["POST"])
def reset():
    session["history"] = []
    return jsonify({"ok": True})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Load existing history for this session
    history = get_history()

    # Append the new user message
    history.append({"role": "user", "content": user_message})

    try:
        # Call Claude with full history
        message = client.messages.create(
            model="claude-opus-4-8",
            system="You are an experienced business strategy professor. The user is a student of business strategy. Your goal is to provide the user with insightful analysis and support your analysis by drawing on recognized academic frameworks. Ask the student to present the business situation. Ask three questions of the user to determine their level of knowledge about the situation. After each question present the user with an academic insight into the situation. At end, summarise the learning for the user. Use narrative throughout, not bullet points",
            max_tokens=1024,  # you can tune this
            messages=history,
        )

        # Extract text blocks into one string
        parts = []
        for block in message.content:
            if block.type == "text":
                parts.append(block.text)
        reply_text = "\n".join(parts)

        # Append assistant reply to history
        history.append({"role": "assistant", "content": reply_text})
        save_history(history)

        return jsonify({"reply": reply_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=None)


def load_local_env():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_fallback_chat_response(message):
    return (
        "Demo mode response:\n\n"
        "Hi! I'm your AI Business Assistant, created by Shanmugapriyan J. "
        "I can help you draft professional replies, summarize business ideas, and "
        "prepare customer-facing communication. Your request was:\n"
        f"\"{message}\"\n\n"
        "Add an OpenAI API key later to get live AI-generated answers."
    )


def generate_fallback_email(email_type, tone, prompt):
    return (
        f"Subject: {email_type.title()} for Business Communication\n\n"
        f"Hello,\n\n"
        f"This is a {tone} {email_type} created in demo mode.\n\n"
        f"Main purpose:\n{prompt}\n\n"
        "Suggested message:\n"
        "Thank you for your time and attention. I wanted to reach out regarding the "
        "matter above and share a clear next step. Please review the details and let "
        "me know if you would like to schedule a call or discuss this further.\n\n"
        "Best regards,\n"
        "Your Business Team"
    )


def generate_fallback_product_description(product_name, features):
    feature_list = [item.strip() for item in features.split(",") if item.strip()]
    bullets = "\n".join(f"- {item}" for item in feature_list[:5])
    if not bullets:
        bullets = "- Reliable performance\n- Easy to use\n- Business-ready value"

    return (
        f"{product_name}: Built for smarter business growth\n\n"
        f"{product_name} is a practical solution designed to help teams work faster, "
        "stay organized, and deliver a better customer experience. It combines ease "
        "of use with valuable business features so companies can improve efficiency "
        "without adding complexity.\n\n"
        "Key benefits:\n"
        f"{bullets}\n\n"
        "This is a demo description. Add an OpenAI API key for richer AI-written marketing copy."
    )


def generate_ai_response(system_prompt, user_prompt, history=None):
    client = get_openai_client()
    if client is None:
        return None

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        for item in history[-8:]:
            role = item.get("role")
            content = item.get("content", "").strip()
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_prompt})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[OpenAI error] {exc}")
        return None


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def style():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def script():
    return send_from_directory(BASE_DIR, "script.js")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json() or {}
        message = (data.get("message") or "").strip()
        history = data.get("history", [])

        if not message:
            return jsonify({"error": "Message cannot be empty."}), 400

        system_prompt = (
            "You are a professional AI personal assistant for business, "
            "created by Shanmugapriyan J. If anyone asks who made you or who your "
            "creator is, always say you were created by Shanmugapriyan J. "
            "Give practical, concise, helpful answers for business communication, "
            "sales support, customer service, workflow help, and productivity."
        )

        reply = generate_ai_response(system_prompt, message, history=history)
        if reply is None:
            reply = generate_fallback_chat_response(message)
        return jsonify({"reply": reply})
    except Exception:
        return jsonify(
            {"error": "Unable to generate a chat response right now. Please try again."}
        ), 500


@app.route("/generate-email", methods=["POST"])
def generate_email():
    try:
        data = request.get_json() or {}
        email_type = (data.get("email_type") or "").strip()
        tone = (data.get("tone") or "").strip()
        prompt = (data.get("prompt") or "").strip()

        if not prompt:
            return jsonify({"error": "Email instructions cannot be empty."}), 400

        system_prompt = (
            "You are an expert business writing assistant. Write polished emails for "
            "professional use. Keep the structure clear and actionable."
        )
        user_prompt = (
            f"Write a {tone} {email_type}.\n"
            f"Request details: {prompt}\n"
            "Format the output with a subject line and a complete email body."
        )

        email = generate_ai_response(system_prompt, user_prompt)
        if email is None:
            email = generate_fallback_email(email_type, tone, prompt)
        return jsonify({"email": email})
    except Exception:
        return jsonify(
            {"error": "Unable to generate the email right now. Please try again."}
        ), 500


@app.route("/product-description", methods=["POST"])
def product_description():
    try:
        data = request.get_json() or {}
        product_name = (data.get("product_name") or "").strip()
        features = (data.get("features") or "").strip()

        if not product_name or not features:
            return jsonify({"error": "Product name and features are required."}), 400

        system_prompt = (
            "You are a creative product marketing assistant for businesses. "
            "Write attractive, easy-to-read product descriptions that highlight value "
            "and benefits clearly."
        )
        user_prompt = (
            f"Create a compelling product description for {product_name}.\n"
            f"Key features: {features}\n"
            "Include a short headline, a persuasive description, and a few benefit-focused bullet points."
        )

        description = generate_ai_response(system_prompt, user_prompt)
        if description is None:
            description = generate_fallback_product_description(product_name, features)
        return jsonify({"description": description})
    except Exception:
        return jsonify(
            {
                "error": "Unable to generate the product description right now. Please try again."
            }
        ), 500


if __name__ == "__main__":
    app.run(debug=True)

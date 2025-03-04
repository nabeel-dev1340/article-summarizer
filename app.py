from flask import Flask, request, jsonify
import os
from openai import OpenAI
from fetch_article import extract_article
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@app.route("/ping", methods=["GET"])
def ping():
    """Simple endpoint to check if the API is running"""
    return jsonify({"status": "ok", "message": "API is running"}), 200


@app.route("/extract", methods=["POST"])
def extract():
    """Endpoint to extract article content from a URL"""
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    url = data["url"]
    try:
        article_content = extract_article(url)
        return jsonify({"url": url, "content": article_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/summarize", methods=["POST"])
def summarize():
    """Endpoint to extract and summarize article content from a URL"""
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    url = data["url"]
    try:
        # Extract the article content
        article_content = extract_article(url)

        # Check if we have content to summarize
        if not article_content or article_content.startswith("Failed to"):
            return jsonify({"error": "Could not extract article content"}), 400

        # Summarize the content using OpenAI
        summary = summarize_with_openai(article_content)

        return jsonify({"url": url, "content": article_content, "summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def summarize_with_openai(text):
    """Use OpenAI's GPT to summarize the article text"""
    prompt = f"""
    I'll provide the text of an article below. Please create a comprehensive yet concise summary that:

    1. Captures the main points, key arguments, and essential information
    2. Maintains the original tone and intent of the article
    3. Includes the most important statistics, quotes, or findings if present
    4. Organizes information logically with appropriate structure
    5. Is approximately [desired length - e.g., 250 words or 3-5 paragraphs]

    Please avoid:
    - Adding your own opinions or analysis not found in the original
    - Including minor details that aren't central to the main message
    - Repeating information unnecessarily

    Here is the article:
        {text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # You can change to gpt-4 for better results
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes articles accurately and concisely.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Failed to generate summary: {str(e)}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

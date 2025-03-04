import requests
from bs4 import BeautifulSoup
from newspaper import Article
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_proxy():
    """
    Returns proxy configuration from environment variables.
    Expected format in environment: PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASSWORD
    """
    proxy_host = os.environ.get("PROXY_HOST")
    proxy_port = os.environ.get("PROXY_PORT")
    proxy_user = os.environ.get("PROXY_USER")
    proxy_password = os.environ.get("PROXY_PASSWORD")

    # If proxy settings are not configured, return None
    if not all([proxy_host, proxy_port, proxy_user, proxy_password]):
        logging.warning(
            "Proxy settings not configured completely. Will try without proxy."
        )
        return None

    # Clean up password if it has v3= prefix
    if proxy_password.startswith("v3="):
        proxy_password = proxy_password[3:]

    return {
        "http": f"http://{proxy_user}:{proxy_password}@{proxy_host}:{proxy_port}",
        "https": f"https://{proxy_user}:{proxy_password}@{proxy_host}:{proxy_port}",
    }


def extract_article(url):
    """
    Extract article text from a given URL using newspaper3k or BeautifulSoup as fallback.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Validate URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        # First attempt: Use newspaper3k for extraction
        article = Article(url)
        article.download()
        article.parse()

        if article.text:
            return article.text.strip()
        logging.info("Newspaper3k returned empty text. Trying BeautifulSoup...")
    except Exception as e:
        logging.warning(f"Newspaper3k failed: {e}. Trying BeautifulSoup...")

    try:
        # Fallback: Use requests and BeautifulSoup with proxies
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Get proxy configuration
        proxy = get_proxy()

        # Make request with or without proxy based on availability
        if proxy:
            logging.info(
                f"Using proxy: {proxy['http'].split('@')[1]}"
            )  # Log only the host:port part
            response = requests.get(url, headers=headers, proxies=proxy, timeout=15)
        else:
            logging.info("Making request without proxy")
            response = requests.get(url, headers=headers, timeout=15)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract article content
        article_tag = soup.find("article")
        paragraphs = article_tag.find_all("p") if article_tag else soup.find_all("p")

        article_text = "\n\n".join(
            [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        )

        return article_text if article_text else "Failed to extract article content."
    except requests.exceptions.RequestException as e:
        return f"Failed to retrieve the article: {e}"
    except Exception as e:
        return f"Failed to extract article: {e}"

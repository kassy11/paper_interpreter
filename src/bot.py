from logzero import logger
import urllib.request


def add_mention(user_id, text):
    return f"<@{user_id}>\n{text}"


def read_format_prompt(url, slack_bot_token):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {slack_bot_token}")
    prompt = ""
    logger.info(f"Downloading format text from {url}...")
    try:
        with urllib.request.urlopen(req) as web_file:
            prompt = web_file.read().decode("utf-8").strip
    except Exception as e:
        logger.warning(f"Failed to download format text from {url}.")
        logger.warning(f"Exception: {str(e)}")
    return prompt

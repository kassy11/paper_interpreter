from logzero import logger
import urllib.request


def add_mention(user_id, text):
    return f"<@{user_id}>\n{text}"


def build_image_blocks(figure_paths):
    blocks = []
    for figure_path in figure_paths:
        blocks.append(
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": "Please enjoy this photo of a kitten",
                },
                "image_url": figure_path,
                # TODO: テキストを追加
                "alt_text": "An incredibly cute kitten.",
            },
        )
    return blocks


def read_format_prompt(url, slack_bot_token):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {slack_bot_token}")
    prompt = ""
    logger.info(f"Downloading format text from {url}...")
    try:
        with urllib.request.urlopen(req) as web_file:
            prompt = web_file.read().decode("utf-8").strip()
    except Exception as e:
        logger.warning(f"Failed to download format text from {url}.")
        logger.warning(f"Exception: {str(e)}")
    return prompt

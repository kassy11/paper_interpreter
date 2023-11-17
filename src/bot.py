from logzero import logger
import urllib.request
from slack_sdk import WebClient
import os
from .utils import load_env

load_env()
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")


def add_mention(user_id, text):
    return f"<@{user_id}>\n{text}"


def _upload_images(image_paths, channel_id, thread_id):
    client = WebClient(SLACK_BOT_TOKEN)
    upload_image_paths = []
    logger.info(f"Uploading images in slack channel {channel_id}....")
    for image in image_paths:
        result = client.files_upload_v2(
            channel=channel_id, thread_ts=thread_id, file=image
        )
        upload_image_paths.append(result["file"]["permalink_public"])
    return upload_image_paths


def build_image_blocks(image_paths, channel_id, thread_id):
    upload_images = _upload_images(image_paths, channel_id, thread_id)
    blocks = []
    for image in upload_images:
        blocks.append(
            {
                "type": "image",
                "image_url": image,
                "alt_text": "figure in the paper",
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

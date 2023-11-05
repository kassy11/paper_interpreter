from dotenv import load_dotenv
from os.path import join, dirname
import urllib.request
from logzero import logger
import os


def load_env():
    load_dotenv(verbose=True)
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)


def read_format_prompt(url, slack_bot_token):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {slack_bot_token}")
    prompt = ""
    logger.info(f"Downloading format text from {url}...")
    try:
        with urllib.request.urlopen(req) as web_file:
            prompt = web_file.read().decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to download format text from {url}.")
        logger.warning(f"Exception: {str(e)}")
    return prompt


def remove(tmp_file_name, figures):
    os.remove(tmp_file_name)
    if figures:
        for figure in figures:
            os.remove(figure)

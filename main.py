import os
from os.path import join, dirname
import re
from logging import getLogger, StreamHandler, DEBUG
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from util import create_prompt, generate
from dotenv import load_dotenv

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

app = App(token=SLACK_BOT_TOKEN)

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


@app.event("app_mention")
def respond_to_mention(event, say):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    url_list = re.findall(pattern, event["text"])
    thread_id = event["ts"]
    user_id = event["user"]
    channel_id = event["channel"]

    if not url_list:
        logger.warn("User does'nt specify arxiv url.")
        say(
            text=f"<@{user_id}> arxivのURLを指定してください。",
            thread_ts=thread_id,
            channel=channel_id,
        )
    response = ""
    for url in url_list:
        if "arxiv.org" in url:
            prompt = create_prompt(url)
            response += f"<@{user_id}> {url} の要約です。\n"
            answer = generate(prompt)
            response += f"{answer}\n\n"
            logger.info(f"Successfully generate paper summary from {url}.")
        else:
            logger.warn("User does'nt specify arxiv url.")
            response = f"<@{user_id}> {url} はarxivのURLではありません。\narxivのURLを指定してください。\n\n"
    say(text=response, thread_ts=thread_id, channel=channel_id)


# ロギング
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()

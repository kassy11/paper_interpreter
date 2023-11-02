import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from util import create_prompt, generate

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]

app = App(token=SLACK_BOT_TOKEN)


@app.event("app_mention")
def respond_to_mention(event, say):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    url_list = re.findall(pattern, event["text"])
    if not url_list:
        say("arxivのURLを指定してください。")
    response = ""
    url_size = len(url_list)
    for url in url_list:
        print(url)
        prompt = create_prompt(url)
        response += f"{url} の要約です。\n"
        answer = generate(prompt)
        response += f"{answer}"
        if url_size >= 2:
            response += "-------------"
    say(response)


# ロギング
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)


SocketModeHandler(app, SLACK_APP_TOKEN).start()

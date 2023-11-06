import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from src.paper import download_pdf, read
from src.gpt import generate, create_prompt
from logzero import logger
from src.utils import load_env
from src.bot import add_mention, read_format_prompt
import datetime

load_env()
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

app = App(token=SLACK_BOT_TOKEN)


@app.event("message")
@app.event("app_mention")
def respond_to_mention(event, say):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    url_list = re.findall(pattern, event["text"])
    user_text = re.sub(r"<[^>]*>", "", event["text"])
    thread_id = event["ts"]
    user_id = event["user"]
    channel_id = event["channel"]

    if not url_list:
        logger.warning("User does'nt specify url.")
        say(
            text=add_mention(user_id, "論文PDFのURLを指定してください。"),
            thread_ts=thread_id,
            channel=channel_id,
        )

    # format prompt for summary
    format_prompt = ""
    if "files" in event and len(event["files"]) > 0:
        for file in event["files"]:
            if file["mimetype"] == "text/plain" or file["mimetype"] == "text/markdown":
                format_prompt = read_format_prompt(
                    file["url_private_download"], SLACK_BOT_TOKEN
                )
                logger.info(f"User send format prompt by file.")
                break
    elif user_text:
        format_prompt = user_text
        logger.info(f"User send format prompt.")

    response = ""
    for url in url_list:
        prefix = str(datetime.datetime.now()).strip()
        tmp_file_name = f"tmp_{prefix}_{os.path.basename(url)}"
        say(
            text=add_mention(user_id, f"{url} から論文を読み取っています。"),
            thread_ts=thread_id,
            channel=channel_id,
        )

        try:
            os.remove("tmp*.pdf")
        except:
            pass
        is_success = download_pdf(url, tmp_file_name)

        if is_success:
            paper_text = read(tmp_file_name)
            prompt = create_prompt(format_prompt, paper_text)
            say(
                text=add_mention(user_id, "要約を生成中です。\n1~5分ほどかかります。\n"),
                thread_ts=thread_id,
                channel=channel_id,
            )
            answer = generate(prompt)
            response += add_mention(user_id, f"{url} の要約です。\n{answer}\n\n")
            logger.info(f"Successfully generate summary from {url}.")
        else:
            response += add_mention(
                user_id, f"{url} から論文を読み取ることができませんでした。\n論文PDFのURLを指定してください。"
            )
    say(text=response, thread_ts=thread_id, channel=channel_id)


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()

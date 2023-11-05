import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import src.paper
import src.gpt
from logzero import logger
from src.utils import load_env
import datetime
from src.utils import read_format_prompt, remove
import slack

load_env()
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

app = App(token=SLACK_BOT_TOKEN)


@app.event("message")
@app.event("app_mention")
def respond_to_mention(event, say):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    # extract url from user input
    url_list = re.findall(pattern, event["text"])
    user_text = re.sub(r"<[^>]*>", "", event["text"])
    thread_id = event["ts"]
    user_id = event["user"]
    channel_id = event["channel"]

    if not url_list:
        logger.warning("User does'nt specify url.")
        say(
            text=slack.add_mention(user_id, "論文PDFのURLを指定してください。"),
            thread_ts=thread_id,
            channel=channel_id,
        )
        return

    # format prompt for summary
    format_prompt = ""
    if "files" in event and len(event["files"]) > 0:
        for file in event["files"]:
            if file["mimetype"] == "text/plain":
                format_prompt = read_format_prompt(
                    file["url_private_download"], SLACK_BOT_TOKEN
                )
                logger.info(
                    f"Used send .txt file for format prompt.\nprompt = {format_prompt}"
                )
                break
    elif user_text:
        format_prompt = user_text
        logger.info(f"User seand format prompt.\nprompt = {format_prompt}")

    response = ""
    figure_paths = []
    for url in url_list:
        prefix = str(datetime.datetime.now()).strip()
        tmp_file_name = f"tmp_{prefix}_{os.path.basename(url)}"
        say(
            text=slack.add_mention(user_id, f"{url} から論文を読み取っています。"),
            thread_ts=thread_id,
            channel=channel_id,
        )
        is_success = paper.download_pdf(url, tmp_file_name)

        if is_success:
            paper_text, figure_paths = paper.get_content(tmp_file_name)
            prompt = gpt.create_prompt(
                format_prompt, paper_text[paper.PAPER_TEXT_KEYS.TEXT]
            )
            say(
                text=slack.add_mention(user_id, "要約を生成中です。\n1~5分ほどかかります。\n"),
                thread_ts=thread_id,
                channel=channel_id,
            )
            answer = gpt.generate(prompt)
            response += slack.add_mention(
                user_id,
                f"{url} の要約です。\n論文名: {paper_text[paper.PAPER_TEXT_KEYS.TITLE]}\n著者：{paper.PAPER_TEXT_KEYS.AUTHOR}\n{answer}\n\n",
            )
        else:
            response += slack.add_mention(
                user_id, f"{url} から論文を読み取ることができませんでした。\n論文PDFのURLを指定してください。"
            )
    say(text=response, thread_ts=thread_id, channel=channel_id)
    if figure_paths:
        say(
            blocks=slack.build_image_blocks(figure_paths),
            thread_ts=thread_id,
            channel=channel_id,
        )
    # remove tmp files
    remove(tmp_file_name, figure_paths)
    return


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()

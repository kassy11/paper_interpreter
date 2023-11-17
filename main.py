import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from src.paper import download_pdf, read
from src.gpt import create_prompt, generate
from logzero import logger
from src.utils import remove_tmp_files
from src.bot import (
    add_mention,
    read_format_prompt,
    build_image_blocks,
    SLACK_BOT_TOKEN,
    SLACK_APP_TOKEN,
)
import datetime

app = App(token=SLACK_BOT_TOKEN)


@app.event("message")
@app.event("app_mention")
def respond_to_mention(event, say):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    url_list = []
    urls = re.findall(pattern, event["text"])
    if urls:
        for url in urls:
            url_list.append({"url": url, "is_slack_upload": False})

    user_text = re.sub(r"<[^>]*>", "", event["text"]).strip()
    thread_id = event["ts"]
    user_id = event["user"]
    channel_id = event["channel"]

    # read user input and upload files
    format_prompt = ""
    if "files" in event and len(event["files"]) > 0:
        for file in event["files"]:
            mimetype = file["mimetype"]
            if mimetype == "text/plain" or mimetype == "text/markdown":
                format_prompt = read_format_prompt(
                    file["url_private_download"], SLACK_BOT_TOKEN
                )
                logger.info("User send format prompt by file.")
            elif mimetype == "application/pdf":
                url_list.append(
                    {"url": file["url_private_download"], "is_slack_upload": True}
                )
    elif user_text:
        format_prompt = user_text
        logger.info("User send format prompt.")

    if not url_list:
        logger.warning("User does'nt specify url.")
        say(
            text=add_mention(user_id, "論文PDFのURLを指定してください。"),
            thread_ts=thread_id,
            channel=channel_id,
        )

    response = ""
    paper_images = []
    for url_dic in url_list:
        prefix = str(datetime.datetime.now()).strip()
        tmp_file_name = f'tmp_{prefix}_{os.path.basename(url_dic["url"])}'
        say(
            text=add_mention(user_id, f'{url_dic["url"]} から論文を読み取っています。'),
            thread_ts=thread_id,
            channel=channel_id,
        )

        is_success = download_pdf(url_dic, tmp_file_name, SLACK_BOT_TOKEN)

        if is_success:
            paper_text, paper_images = read(tmp_file_name)
            prompt = create_prompt(format_prompt, paper_text)
            say(
                text=add_mention(
                    user_id, "要約を生成中です。\n1~5分ほどかかります。\n"
                ),
                thread_ts=thread_id,
                channel=channel_id,
            )
            answer = generate(prompt)
            response += add_mention(
                user_id, f'{url_dic["url"]} の要約です。\n{answer}\n\n'
            )
            logger.info(f'Successfully generate summary from {url_dic["url"]}.')
        else:
            response += add_mention(
                user_id,
                f'{url_dic["url"]} から論文を読み取ることができませんでした。\n論文PDFのURLを指定してください。',
            )
    say(text=response, thread_ts=thread_id, channel=channel_id)
    if paper_images:
        say(
            text=add_mention(user_id, "以下が論文中の図表です。"),
            thread_ts=thread_id,
            channel=channel_id,
        )
        say(
            blocks=build_image_blocks(paper_images, channel_id, thread_id),
            thread_ts=thread_id,
            channel=channel_id,
        )
    remove_tmp_files(tmp_file_name, paper_images)
    logger.info("Successfully send response.")


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()

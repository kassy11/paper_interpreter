import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from src.paper import download_pdf, read
from src.gpt import create_prompt, generate
from logzero import logger
from src.utils import remove_tmp_files
from src.bot import (
    read_format_prompt,
    build_image_blocks,
    SLACK_BOT_TOKEN,
    SLACK_APP_TOKEN,
    respond,
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
        respond(
            say, user_id, channel_id, thread_id, text="論文PDFのURLを指定してください。"
        )

    response = ""
    paper_images = []
    for url_dic in url_list:
        prefix = str(datetime.datetime.now()).strip()
        tmp_file_name = f'tmp_{prefix}_{os.path.basename(url_dic["url"])}'
        respond(
            say,
            user_id,
            channel_id,
            thread_id,
            text=f'{url_dic["url"]} から論文を読み取っています。',
        )

        is_success = download_pdf(url_dic, tmp_file_name, SLACK_BOT_TOKEN)

        if is_success:
            paper_text, paper_images = read(tmp_file_name)
            prompt = create_prompt(format_prompt, paper_text)
            respond(
                say,
                user_id,
                channel_id,
                thread_id,
                text="要約を生成中です。\n1~5分ほどかかります。\n",
            )
            answer = generate(prompt)
            response += f'{url_dic["url"]} の要約です。\n{answer}\n\n'

            logger.info(f'Successfully generate summary from {url_dic["url"]}.')
        else:
            response += f'{url_dic["url"]} から論文を読み取ることができませんでした。\n論文PDFのURLを指定してください。'
    respond(say, user_id, channel_id, thread_id, text=response)
    if paper_images:
        respond(
            say,
            user_id,
            channel_id,
            thread_id,
            text="論文中の図表です。\n（うまく切り出せない場合もあります:man-bowing:）",
        )
        respond(
            say,
            user_id,
            channel_id,
            thread_id,
            blocks=build_image_blocks(paper_images, channel_id, thread_id),
        )
    remove_tmp_files(tmp_file_name, paper_images)
    logger.info("Successfully send response.")


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()

import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import paper
import gpt
from logzero import logger
from utils import load_env

load_env()
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

app = App(token=SLACK_BOT_TOKEN)


@app.event("message")
@app.event("app_mention")
def respond_to_mention(event, say):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    url_list = re.findall(pattern, event["text"])
    thread_id = event["ts"]
    user_id = event["user"]
    channel_id = event["channel"]

    if not url_list:
        logger.warning("User does'nt specify paper url.")
        say(
            text=f"<@{user_id}> 論文のURLを指定してください。",
            thread_ts=thread_id,
            channel=channel_id,
        )
    response = ""
    pdf_url = ""
    for url in url_list:
        is_pdf = paper.is_pdf(url)
        is_arxiv = "arxiv.org" in url

        if is_arxiv and not is_pdf:
            pdf_url = paper.get_arxiv_pdf_url(url)
        elif is_pdf:
            pdf_url = url

        if pdf_url:
            tmp_file_name = f"tmp_{os.path.basename(pdf_url)}"
            is_success = paper.download_pdf(pdf_url, tmp_file_name)

            if is_success:
                paper_text = paper.read(tmp_file_name)
                prompt = gpt.create_prompt(paper_text)
                say(
                    text="要約を生成中です。\n1~5分ほどかかります。\n",
                    thread_ts=thread_id,
                    channel=channel_id,
                )
                answer = gpt.generate(prompt)
                response += f"<@{user_id}> {url} の要約です。\n{answer}\n\n"
                logger.info(f"Successfully response from {url}.")
            else:
                response = f"{pdf_url} からの論文を読み取ることができませんでした。\n別の論文を指定してください。"
        else:
            logger.warning("User does'nt specify arxiv url or paper pdf url.")
            response = f"<@{user_id}> {url} はarxivのURLもしくは論文PDFのURLではありません。\n正しくURLを指定してください。\n\n"
    say(text=response, thread_ts=thread_id, channel=channel_id)


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()

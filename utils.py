import os
from os.path import join, dirname
import arxiv
import urllib.request
from pypdf import PdfReader
import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import random
from logging import getLogger, StreamHandler, DEBUG

random.seed(42)


load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

# max tokensの大きいモデルを使う
# https://platform.openai.com/docs/models
# 2023/11現在, gpt-4-32kはAPIから利用できないので注意
# https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4
MODEL_NAME = {"GPT3": "gpt-3.5-turbo-16k", "GPT4": "gpt-4-32k"}
MODEL_MAX_TOKENS = {"GPT3": 16000, "GPT4": 32000}
RESPONSE_MAX_TOKENS = 1000
MODEL = os.environ.get("MODEL")
openai.api_key = os.environ.get("OPENAI_API_KEY")

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


def is_pdf(url):
    _, ext = os.path.splitext(url)
    if ext == ".pdf":
        return True
    else:
        return False


def get_arxiv_pdf_url(arxiv_url):
    client = arxiv.Client()

    id = _extract_id(arxiv_url)
    search = arxiv.Search(id_list=[id])
    results = list(client.results(search))
    pdf_url = results[0].pdf_url
    return pdf_url


def _extract_id(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    directories = path.split("/")
    id = directories[-1]
    return id


def _read_paper(pdf_url):
    # PDFを一時的にダウンロード
    pdf_file_name = os.path.basename(pdf_url)
    num = random.randint(50, 100)
    file_name = f"tmp_{num}_{pdf_file_name}"
    logger.info(f"Downloding pdf from {pdf_url}...")
    urllib.request.urlretrieve(pdf_url, file_name)

    reader = PdfReader(file_name)
    paper_text = ""
    logger.info(f"Reading pdf text from {file_name}...")
    for page in reader.pages:
        paper_text += str(page.extract_text())

    # 参考文献以降を削除
    reference_pos = max(paper_text.find("References"), paper_text.find("REFERENCES"))
    paper_text = paper_text[:reference_pos].strip()
    # 論文PDFを削除
    logger.info(f"Delete paper pdf from {pdf_url}.")
    os.remove(file_name)
    return paper_text


def create_prompt(pdf_url):
    logger.info("Creating prompt...")
    paper_text = _read_paper(pdf_url)
    with open("./format.txt") as f:
        system_prompt = f.read()

    prompt = f"{system_prompt}\n\n{paper_text}\n\n"
    return prompt


def generate(prompt):
    chat = ChatOpenAI(
        model_name=MODEL_NAME[MODEL],
        temperature=0,
        max_tokens=RESPONSE_MAX_TOKENS,
        request_timeout=20,
    )

    CHARACTER_PROMPT = "あなたはAIに関する研究を行っている専門家です。"
    messages = [
        SystemMessage(content=CHARACTER_PROMPT),
        HumanMessage(content=prompt),
    ]

    token_size = chat.get_num_tokens_from_messages(messages=messages)
    token_limit = MODEL_MAX_TOKENS[MODEL] - RESPONSE_MAX_TOKENS

    logger.info(f"Generating summary by {MODEL_NAME[MODEL]}...")
    if token_size <= token_limit:
        logger.info(
            f"The token size of the input to {MODEL_NAME[MODEL]} is {token_size}."
        )
        try:
            response = chat(messages)
            response = response.content
        except Exception as e:
            logger.error("Failed to request to ChatGPT!")
            logger.error(f"Exception: {str(e)}")
            response = "ChatGPTへのリクエストが失敗しました。\nOpenAI APIのRateLimitに引っかかっている可能性があるため、少し待ってから論文URLを再送してみてください。"
    else:
        logger.warning("The token size is too large, so the tail is cut off.")
        response = "論文の文章量が大きすぎたため、要約できませんでした。"
    return response

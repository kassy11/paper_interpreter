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

# TODO: loggingを追加

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

# https://platform.openai.com/docs/models
# max tokensの大きいモデルを使う
MODEL_NAME = {"GPT3": "gpt-3.5-turbo-16k", "GPT4": "gpt-4-32k"}
MAX_TOKENS = {"GPT3": 16000, "GPT4": 32000}
MODEL = os.environ.get("MODEL")
openai.api_key = os.environ.get("OPENAI_API_KEY")

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


def _extract_id(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    directories = path.split("/")
    id = directories[-1]
    return id


def _read_paper(arxiv_url):
    client = arxiv.Client()

    id = _extract_id(arxiv_url)
    search = arxiv.Search(id_list=[id])
    results = list(client.results(search))
    pdf_url = results[0].pdf_url

    # PDFを一時的にダウンロード
    file_suffix = id.replace(".", "-")
    file_name = f"temp{file_suffix}.pdf"
    logger.info(f"downloding pdf from {pdf_url}...")
    urllib.request.urlretrieve(pdf_url, file_name)

    reader = PdfReader(file_name)
    paper_text = ""
    logger.info(f"reading pdf text from {file_name}...")
    for page in reader.pages:
        paper_text += str(page.extract_text())
    # 参考文献以降を削除
    paper_text = paper_text[: paper_text.find("References")].strip()
    # 論文PDFを削除
    os.remove(file_name)
    return paper_text


def create_prompt(arxiv_url):
    paper_text = _read_paper(arxiv_url)
    with open("./question_template.txt") as f:
        system_prompt = f.read()

    prompt = f"{system_prompt}\n\n{paper_text}\n\n"
    return prompt


def generate(prompt):
    chat = ChatOpenAI(
        model_name=MODEL_NAME[MODEL],
        temperature=0,
    )

    messages = [
        SystemMessage(content="あなたはAIに関する研究を行っている専門家です。"),
        HumanMessage(content=prompt),
    ]

    # TODO: tiktokenでトークンサイズを調べて、GPTモデルのサイズ以上なら区切る
    response = chat(messages)
    return response.content

import os
import arxiv
import urllib.request
from pypdf import PdfReader
import openai
import os
from urllib.parse import urlparse

# TODO: loggingを追加

# https://platform.openai.com/docs/models
# max tokensの大きいモデルを使う
MODELS = {"GPT3": "gpt-3.5-turbo-16k", "GPT4": "gpt-4-32k"}
MAX_TOKENS = {"GPT3": 16000, "GPT4": 32000}


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
    urllib.request.urlretrieve(pdf_url, file_name)

    reader = PdfReader(file_name)
    paper_text = ""
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

    prompt = system_prompt + paper_text
    return prompt


def generate(prompt):
    model_name = os.environ.get("MODEL")
    messages = [
        {"role": "system", "content": "あなたはAIに関する研究を行っている専門家です。"},
        {"role": "user", "content": prompt},
    ]
    # TODO: tiktokenでトークンサイズを調べて、GPTモデルのサイズ以上なら区切る
    response = openai.ChatCompletion.create(
        model=MODELS[model_name],
        messages=messages,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.7,
        top_p=1,
    )
    return response.choices[0].message.content.strip()

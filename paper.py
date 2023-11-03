import os
import arxiv
import urllib.request
from pypdf import PdfReader
import os
from urllib.parse import urlparse
from logzero import logger
from utils import load_env

load_env()


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


def download_pdf(pdf_url, tmp_file_name):
    is_success = True
    logger.info(f"Downloding pdf from {pdf_url}...")
    try:
        with urllib.request.urlopen(pdf_url) as web_file:
            with open(tmp_file_name, "wb") as local_file:
                local_file.write(web_file.read())
    except Exception as e:
        logger.warning(f"Failed to download pdf from {pdf_url}.")
        logger.warning(f"Exception: {str(e)}")
        is_success = False
    return is_success


def read(tmp_file_name):
    reader = PdfReader(tmp_file_name)
    paper_text = ""
    logger.info(f"Reading pdf text from {tmp_file_name}...")
    for page in reader.pages:
        paper_text += str(page.extract_text())

    # 参考文献以降を削除
    reference_pos = max(paper_text.find("References"), paper_text.find("REFERENCES"))
    paper_text = paper_text[:reference_pos].strip()
    # 論文PDFを削除
    logger.info(f"Delete paper {tmp_file_name}.")
    os.remove(tmp_file_name)
    return paper_text

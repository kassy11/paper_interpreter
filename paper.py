import os
import urllib.request
import os
from logzero import logger
from pdfminer.high_level import extract_text
from utils import load_env

load_env()


def _is_pdf(http_response_obj):
    return http_response_obj.getheader("Content-Type") == "application/pdf"


def download_pdf(url, tmp_file_name):
    logger.info(f"Downloading pdf from {url}...")
    try:
        with urllib.request.urlopen(url) as web_file:
            if not _is_pdf(web_file):
                return False
            with open(tmp_file_name, "wb") as local_file:
                local_file.write(web_file.read())
    except Exception as e:
        logger.warning(f"Failed to download pdf from {url}.")
        logger.warning(f"Exception: {str(e)}")
        return False
    return True


def read(tmp_file_name):
    logger.info(f"Reading pdf text from {tmp_file_name}...")
    paper_text = extract_text(tmp_file_name)

    # 参考文献以降を削除
    reference_pos = max(paper_text.find("References"), paper_text.find("REFERENCES"))
    paper_text = paper_text[:reference_pos].strip()
    # 論文PDFを削除
    logger.info(f"Delete paper {tmp_file_name}.")
    os.remove(tmp_file_name)
    return paper_text

import urllib.request
from logzero import logger
import fitz
from .utils import load_env

load_env()
PAPER_TEXT_KEYS = {"TEXT": "text", "TITLE": "title", "AUTHOR": "author"}


def _is_pdf(http_response_obj):
    content_type = http_response_obj.getheader("Content-Type")
    logger.info(f"Content-type: {content_type}.")
    return "application/pdf" in content_type


def download_pdf(url, tmp_file_name):
    logger.info(f"Downloading pdf from {url}...")
    try:
        with urllib.request.urlopen(url) as web_file:
            if not _is_pdf(web_file):
                logger.warn(f"Content-type of {url} is not application/pdf.")
                return False
            with open(tmp_file_name, "wb") as local_file:
                local_file.write(web_file.read())
    except Exception as e:
        logger.warning(f"Failed to download pdf from {url}.")
        logger.warning(f"Exception: {str(e)}")
        return False
    return True


def _get_text(tmp_file_name):
    logger.info(f"Reading pdf text from {tmp_file_name}...")
    text = ""
    with fitz.open(tmp_file_name) as doc:
        metadata = doc["metadata"]
        if "title" in metadata:
            title = metadata["title"]
        else:
            title = "取得できませんでした。"

        if "author" in metadata:
            author = metadata["author"]
        else:
            author = "取得できませんでした。"

        for page in doc:
            text += page.get_text()

    # Delete text after references
    reference_pos = max(
        text.find("References"),
        text.find("REFERENCES"),
        text.find("参考文献"),
    )
    text = text[:reference_pos].strip()
    return {
        PAPER_TEXT_KEYS.TEXT: text,
        PAPER_TEXT_KEYS.AUTHOR: author,
        PAPER_TEXT_KEYS.TITLE: title,
    }


def _get_figures(tmp_file_name):
    figure_paths = []
    return figure_paths


def get_content(tmp_file_name):
    text = _get_text(tmp_file_name)
    figure_paths = _get_figures(tmp_file_name)
    return text, figure_paths

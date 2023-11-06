import os
import urllib.request
from logzero import logger
from pdfminer.high_level import extract_text
import mimetypes
from .utils import load_env

load_env()


def _is_pdf(tmp_file_name, http_response_obj):
    mimetype = str(mimetypes.guess_type(tmp_file_name)[0])
    logger.info(f"MimeType of {tmp_file_name}is {mimetype}.")
    content_type = http_response_obj.getheader("Content-Type")
    logger.info(f"Content-Type of {tmp_file_name}is {content_type}.")
    return "application/pdf" in content_type or "application/pdf" in mimetype


def download_pdf(url_dic, tmp_file_name, slack_bot_token):
    req = urllib.request.Request(url_dic["url"])
    if url_dic["is_slack_upload"]:
        req.add_header("Authorization", f"Bearer {slack_bot_token}")

    logger.info(f'Downloading pdf from {url_dic["url"]}...')
    try:
        with urllib.request.urlopen(req) as web_file:
            with open(tmp_file_name, "wb") as local_file:
                local_file.write(web_file.read())

            if not _is_pdf(tmp_file_name, web_file):
                logger.warn(f'Content-type of {url_dic["url"]} is not application/pdf.')
                os.remove(tmp_file_name)
                return False
    except Exception as e:
        logger.warning(f'Failed to download pdf from {url_dic["url"]}.')
        logger.warning(f"Exception: {str(e)}")
        return False

    return True


def read(tmp_file_name):
    logger.info(f"Reading pdf text from {tmp_file_name}...")
    paper_text = extract_text(tmp_file_name).strip()

    # delete after refenrences
    reference_pos = max(
        paper_text.find("References"),
        paper_text.find("REFERENCES"),
        paper_text.find("参考文献"),
    )
    paper_text = paper_text[:reference_pos].strip()
    os.remove(tmp_file_name)
    return paper_text

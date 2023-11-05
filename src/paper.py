import urllib.request
from logzero import logger
import fitz
from .utils import load_env

load_env()


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


def _remove_reference(text):
    reference_pos = max(
        text.find("References"),
        text.find("REFERENCES"),
        text.find("参考文献"),
    )
    return text[:reference_pos].strip()


def _get_figures(page, doc):
    figure_paths = []
    logger.info("Downloading figures in paper.")
    images = page.get_images()
    num_of_pics = 0

    for page in doc:
        images = page.get_images()
        if not len(images) == 0:
            for image in images:
                num_of_pics += 1
                xref = image[0]
                img = doc.extract_image(xref)
                if img["width"] > 500 and img["height"] > 500:
                    file_name = "extracted_image{}.png".format(num_of_pics)
                    figure_paths.append(file_name)
                    with open(file_name, "wb") as f:
                        f.write(img["image"])


def get_content(tmp_file_name):
    logger.info(f"Extract content from {tmp_file_name}...")
    text = ""
    figure_paths = []
    with fitz.open(tmp_file_name) as doc:
        for page in doc:
            text += str(page.get_text()).strip()
            figure_paths.append(_get_figures(page, doc))

    return _remove_reference(text), figure_paths

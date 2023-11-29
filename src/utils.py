from dotenv import load_dotenv
from os.path import join, dirname
import os
from logzero import logger


def load_env():
    load_dotenv(verbose=True)
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)


def remove_tmp_files(pdf_file_path, image_file_paths):
    try:
        os.remove(pdf_file_path)
        for image in image_file_paths:
            os.remove(image)
    except OSError as e:
        logger.error(f"Failed to remove file: {e}")

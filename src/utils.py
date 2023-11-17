from dotenv import load_dotenv
from os.path import join, dirname
import os


def load_env():
    load_dotenv(verbose=True)
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)


def remove_tmp_files(pdf_file, images):
    os.remove(pdf_file)
    for image in images:
        os.remove(image)
    return

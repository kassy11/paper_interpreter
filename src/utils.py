from dotenv import load_dotenv
from os.path import join, dirname
from logzero import logger
import os


def load_env():
    load_dotenv(verbose=True)
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)

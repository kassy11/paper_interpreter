from dotenv import load_dotenv
from os.path import join, dirname


def load_env():
    load_dotenv(verbose=True)
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)

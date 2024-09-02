import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from util.validator import Validator


from jsonargparse import CLI


if __name__ == "__main__":
    print("here!")

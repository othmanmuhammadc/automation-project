import logging
import time
import functools

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger()


def setup_logging():
    log.setLevel(logging.INFO)

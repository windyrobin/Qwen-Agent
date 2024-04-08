import logging
import os


<<<<<<< HEAD
#def setup_logger(level=logging.INFO):
def setup_logger(level=logging.DEBUG):
=======
def setup_logger(level=None):

    if level is None:
        if int(os.getenv('QWEN_AGENT_DEBUG', '0').strip()):
            level = logging.DEBUG
        else:
            level = logging.INFO

>>>>>>> 55547b98313c153c451c04477b4163723219fb38
    logger = logging.getLogger('qwen_agent_logger')
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logging.basicConfig(filename='qwen.log')
logger = setup_logger()

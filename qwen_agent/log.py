import logging


#def setup_logger(level=logging.INFO):
def setup_logger(level=logging.DEBUG):
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

import logging
import logging.config


def respond_to_tracker(message, logger_name: str = "all_respond_to_logger"):
    logger = logging.getLogger(logger_name)
    logger.info(message)

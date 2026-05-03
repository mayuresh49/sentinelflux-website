from loguru import logger


def create_logger(config: dict):
    logger.remove()
    level = config.get("level", "INFO")
    log_file = config.get("file")
    logger.add("stdout", level=level)
    if log_file:
        logger.add(log_file, level=level, rotation="10 MB", retention="7 days")
    return logger

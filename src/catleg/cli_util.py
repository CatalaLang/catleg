from catleg.config import settings


def set_basic_loglevel():
    """
    Utility for setting the log level as per config -- meant to be used
    within CLI tools only.

    To use, set CATLEG_LOG_LEVEL=INFO in the environment
    or log_level in the .catleg.toml configuration file
    """
    log_level = settings.get("log_level")
    if log_level is not None:
        import logging

        logging.basicConfig(level=log_level.upper())

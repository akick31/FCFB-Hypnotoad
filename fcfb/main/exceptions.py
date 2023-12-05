import functools
import logging
import sys
import discord

# Set up logging
logging.basicConfig(format='[%(asctime)s] [%(levelname)s] - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger("hypnotoad_logger")

# Add Handlers
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
stream_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(stream_handler)


class DiscordAPIError(Exception):
    pass


class GameError(Exception):
    pass


class InvalidParameterError(ValueError):
    pass


class ZebstrikaGamesAPIError(Exception):
    pass


class ZebstrikaGamePlaysAPIError(Exception):
    pass


class ZebstrikaUsersAPIError(Exception):
    pass


def async_exception_handler():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except DiscordAPIError as dae:
                error_message = f"Discord API error in {func.__name__}(): {dae}"
                logger.error(error_message)
                # Optionally, re-raise the exception if needed
                raise dae
            except InvalidParameterError as ipe:
                error_message = f"Invalid parameter error in {func.__name__}(): {ipe}"
                logger.error(error_message)
                # Optionally, re-raise the exception if needed
                raise ipe

            except GameError as ge:
                error_message = f"Game error in {func.__name__}(): {ge}"
                logger.error(error_message)
                # Optionally, re-raise the exception if needed
                raise ge

            except Exception as e:
                error_message = f"An unexpected error occurred in {func.__name__}(): {e}"
                logger.error(error_message)
                # Optionally, re-raise the exception if needed
                raise e
        return wrapper
    return decorator
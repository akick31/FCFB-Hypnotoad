import requests
import sys
import logging

from fcfb.main.exceptions import async_exception_handler, ZebstrikaGamePlaysAPIError

GAME_PLAYS_PATH = "game_plays/"

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


@async_exception_handler()
async def submit_defensive_number(config_data, game_id, defensive_number, timeout_called):
    """
    Make API call to submit the defensive number for the play
    :param config_data:
    :param game_id:
    :param defensive_number:
    :param timeout_called:
    :return:
    """

    try:
        payload = f"defense_submitted/{game_id}/{defensive_number}/{timeout_called}"
        endpoint = config_data['api']['url'] + GAME_PLAYS_PATH + payload
        response = requests.post(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Submitted defensive number for game {game_id}")
            return response.status_code
        else:
            raise ZebstrikaGamePlaysAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")


@async_exception_handler()
async def submit_offensive_number(config_data, game_id, play_id, offensive_number, play, runoff_type,
                                  offensive_timeout_called, defensive_timeout_called):
    """
    Make API call to submit the offensive number for the play, run the play, and return the result

    :param config_data:
    :param game_id:
    :param play_id:
    :param offensive_number:
    :param play:
    :param runoff_type:
    :param offensive_timeout_called:
    :param defensive_timeout_called:
    :return:
    """

    try:
        offensive_timeout_called_str = str(offensive_timeout_called).lower()
        defensive_timeout_called_str = str(defensive_timeout_called).lower()
        payload = f"offense_submitted/{play_id}/{offensive_number}/{play}/{runoff_type}" \
                  f"/{offensive_timeout_called_str}/{defensive_timeout_called_str}"
        endpoint = config_data['api']['url'] + GAME_PLAYS_PATH + payload
        response = requests.put(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Play was run successfully {game_id}")
            return response.json()
        else:
            raise ZebstrikaGamePlaysAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")
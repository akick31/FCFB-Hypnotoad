import requests
import sys
import logging

from fcfb.main.exceptions import async_exception_handler, ZebstrikaUsersAPIError

USERS_PATH = "users/"

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
async def get_user_by_team(config_data, team):
    """
    Get the coach via their team

    :param config_data:
    :param team:
    :return:
    """

    try:
        endpoint = config_data['api']['url'] + USERS_PATH + "team/" + team
        response = requests.get(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Successfully grabbed a user object for {team}")
            return response.json()
        else:
            raise ZebstrikaUsersAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")

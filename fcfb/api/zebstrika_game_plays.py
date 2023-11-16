import requests

GAME_PLAYS_PATH = "game_plays/"


async def submit_defensive_number(config_data, game_id, defensive_number, logger):
    """
    Make API call to get the ongoing game via the channel ID
    :param config_data:
    :param game_id:
    :param defensive_number:
    :param logger:
    :return:
    """

    try:
        payload = f"defense_submitted/{game_id}/{defensive_number}"
        endpoint = config_data['api']['url'] + GAME_PLAYS_PATH + payload
        response = requests.post(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Submitted defensive number for game {game_id}")
            return response.status_code
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while submitting a defensive number: {e}"
        logger.error(error_message)
        raise Exception(error_message)
import requests

GAME_PLAYS_PATH = "game_plays/"


async def submit_defensive_number(config_data, game_id, defensive_number, timeout_called, logger):
    """
    Make API call to submit the defensive number for the play
    :param config_data:
    :param game_id:
    :param defensive_number:
    :param timeout_called:
    :param logger:
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
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while submitting a defensive number: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def submit_offensive_number(config_data, game_id, play_id, offensive_number, play, runoff_type, offensive_timeout_called, defensive_timeout_called, logger):
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
    :param logger:
    :return:
    """

    try:
        payload = f"offense_submitted/{play_id}/{offensive_number}/{play}/{runoff_type}/{offensive_timeout_called}/{defensive_timeout_called}"
        endpoint = config_data['api']['url'] + GAME_PLAYS_PATH + payload
        response = requests.post(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Play was run successfully {game_id}")
            return response.status_code
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while submitting a defensive number: {e}"
        logger.error(error_message)
        raise Exception(error_message)
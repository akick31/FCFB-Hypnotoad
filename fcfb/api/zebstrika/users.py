import requests

USERS_PATH = "users/"


async def get_user_by_team(config_data, team, logger):
    """
    Get the coach via their team

    :param config_data:
    :param team:
    :param logger:
    :return:
    """

    try:
        endpoint = config_data['api']['url'] + USERS_PATH + "team/" + team
        response = requests.get(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Successfully grabbed a user object for {team}")
            return response.json()
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while getting user by team: {e}"
        logger.error(error_message)
        raise Exception(error_message)

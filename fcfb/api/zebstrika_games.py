import requests

GAMES_PATH = "games/"


async def get_ongoing_game_by_channel_id(config_data, channel_id, logger):
    """
    Make API call to get the ongoing game via the channel ID
    :param config_data:
    :param channel_id:
    :param logger:
    :return:
    """

    try:
        payload = f"platform/Discord/platform_id/{channel_id}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.get(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Grabbed the ongoing game for {channel_id}")
            return response.json()
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while getting ongoing game by channel ID: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def post_game(config_data, channel_id, season, subdivision, home_team, away_team, tv_channel, start_time, location,
                    logger):
    """
    Make API call to Zebstrika to start game

    :param config_data:
    :param channel_id:
    :param season:
    :param subdivision:
    :param home_team:
    :param away_team:
    :param tv_channel:
    :param start_time:
    :param location:
    :param logger:
    :return:
    """

    try:
        payload = f"start/Discord/{channel_id}/{season}/{subdivision}/{home_team}/{away_team}/{tv_channel}/{start_time}/{location}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.post(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Successfully started a game at {channel_id}. {home_team} vs {away_team} in S{season} {subdivision}")
            return response.status_code
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while posting a game: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def run_coin_toss(config_data, game_id, coin_toss_choice, logger):
    """
    Make API call to Zebstrika to run coin toss

    :param config_data:
    :param game_id:
    :param coin_toss_choice:
    :param logger:
    :return:
    """

    try:
        payload = f"coinToss/{game_id}/{coin_toss_choice}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.put(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Successfully ran the coin toss for {game_id}")
            return response.json()
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while running a coin toss: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def update_coin_toss_choice(config_data, game_id, coin_toss_choice, logger):
    """
    Make API call to Zebstrika to update the coin toss choice to receive or defer

    :param config_data:
    :param game_id:
    :param coin_toss_choice:
    :param logger:
    :return:
    """

    try:
        payload = f"coinTossChoice/{game_id}/{coin_toss_choice}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.put(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Updated the coin toss choice for {game_id} to {coin_toss_choice}")
            return response.json()
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while updating the coin toss choice: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def update_waiting_on(config_data, game_id, username, logger):
    """
    Make API call to Zebstrika to update the team is waiting on using the coach's username

    :param config_data:
    :param game_id:
    :param username:
    :param logger:
    :return:
    """

    try:
        payload = f"waitingOn/{game_id}/{username}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.put(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Updated the team the game is waiting on for {game_id} to {username}")
            return response.json()
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while updating the coin toss choice: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def delete_ongoing_game(config_data, game_id, logger):
    """
    Make API call to Zebstrika to delete the game

    :param config_data:
    :param game_id:
    :param logger:
    :return:
    """

    try:
        payload = f"{game_id}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.delete(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Delete game {game_id}")
            return response.status_code
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while deleting the game: {e}"
        logger.error(error_message)
        raise Exception(error_message)
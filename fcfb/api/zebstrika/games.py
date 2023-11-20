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
        payload = f"ongoing/discord/{channel_id}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.get(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Grabbed the ongoing game for {channel_id}")
            return response.json()
        elif response.status_code == 404:
            logger.info(f"SUCCESS: No ongoing game for {channel_id}")
            return None
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while getting ongoing game by channel ID: {e}"
        logger.error(error_message)
        raise Exception(error_message)


async def get_ongoing_game_by_id(config_data, game_id, logger):
    """
    Make API call to get the ongoing game via the game ID
    :param config_data:
    :param game_id:
    :param logger:
    :return:
    """

    try:
        payload = f"game_id/{game_id}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.get(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Grabbed the ongoing game for game id {game_id}")
            return response.json()
        elif response.status_code == 404:
            logger.info(f"SUCCESS: No ongoing game for game id {game_id}")
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)
        return None

    except Exception as e:
        error_message = f"- An unexpected error occurred while getting an ongoing game by game ID: {e}"
        logger.error(error_message)
        raise Exception(error_message)
        return None


async def post_game(config_data, channel_id, season, week, subdivision, home_team, away_team, tv_channel, start_time,
                    location, is_scrimmage, logger):
    """
    Make API call to Zebstrika to start game

    :param config_data:
    :param channel_id:
    :param season:
    :param week:
    :param subdivision:
    :param home_team:
    :param away_team:
    :param tv_channel:
    :param start_time:
    :param location:
    :param is_scrimmage:
    :param logger:
    :return:
    """

    try:

        payload = f"start/Discord/{channel_id}/Discord/{channel_id}/{season}/{week}/{subdivision}/{home_team}/" \
                  f"{away_team}/{tv_channel}/{start_time}/{location}/{is_scrimmage}"
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
        payload = f"coin_toss/{game_id}/{coin_toss_choice}"
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
        payload = f"coin_toss_choice/{game_id}/{coin_toss_choice}"
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
        payload = f"waiting_on/{game_id}/{username}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.put(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Updated the team the game is waiting on for game {game_id} to {username}")
            return response.json()
        else:
            exception_message = f"HTTP {response.status_code} response {response.text}"
            logger.error(exception_message)
            raise Exception(exception_message)

    except Exception as e:
        error_message = f"- An unexpected error occurred while updating the team that the game is waiting on: {e}"
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
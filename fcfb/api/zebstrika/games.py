import requests
import sys
import logging

from fcfb.main.exceptions import async_exception_handler, ZebstrikaGamesAPIError

GAMES_PATH = "games/"

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
async def get_ongoing_game_by_thread_id(config_data, thread_id):
    """
    Make API call to get the ongoing game via the thread ID
    :param config_data:
    :param thread_id:
    :return:
    """

    try:
        payload = f"ongoing/discord/{thread_id}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.get(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Grabbed the ongoing game for {thread_id}")
            return response.json()
        elif response.status_code == 404:
            logger.info(f"SUCCESS: No ongoing game for {thread_id}")
            return None
        else:
            raise ZebstrikaGamesAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")


@async_exception_handler()
async def get_ongoing_game_by_id(config_data, game_id):
    """
    Make API call to get the ongoing game via the game ID
    :param config_data:
    :param game_id:
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
            raise ZebstrikaGamesAPIError(f"HTTP {response.status_code} response {response.text}")
        return None

    except Exception as e:
        raise Exception(f"{e}")


@async_exception_handler()
async def post_game(config_data, channel_id, season, week, subdivision, home_team, away_team, tv_channel, start_time,
                    location, is_scrimmage):
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
            raise ZebstrikaGamesAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")


@async_exception_handler()
async def run_coin_toss(config_data, game_id, coin_toss_choice):
    """
    Make API call to Zebstrika to run coin toss

    :param config_data:
    :param game_id:
    :param coin_toss_choice:
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
            raise ZebstrikaGamesAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")


@async_exception_handler()
async def update_coin_toss_choice(config_data, game_id, coin_toss_choice):
    """
    Make API call to Zebstrika to update the coin toss choice to receive or defer

    :param config_data:
    :param game_id:
    :param coin_toss_choice:
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
            raise ZebstrikaGamesAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")


@async_exception_handler()
async def update_waiting_on(config_data, game_id, username):
    """
    Make API call to Zebstrika to update the team is waiting on using the coach's username

    :param config_data:
    :param game_id:
    :param username:
    :return:
    """

    try:
        payload = f"waiting_on/{game_id}/{username}"
        endpoint = config_data['api']['url'] + GAMES_PATH + payload
        response = requests.put(endpoint)

        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"SUCCESS: Updated the team the game is waiting on for game {game_id} to {username}")
            return username
        else:
            raise ZebstrikaGamesAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")


@async_exception_handler()
async def delete_ongoing_game(config_data, game_id):
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
            raise ZebstrikaGamesAPIError(f"HTTP {response.status_code} response {response.text}")

    except Exception as e:
        raise Exception(f"{e}")
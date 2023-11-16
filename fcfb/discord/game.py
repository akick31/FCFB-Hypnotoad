import sys

from fcfb.discord.utils import create_channel, create_message, get_discord_user_by_name, delete_channel
from fcfb.api.zebstrika_games import post_game, get_ongoing_game_by_channel_id, delete_ongoing_game
from fcfb.api.zebstrika_users import get_user_by_team

sys.path.append("..")

async def start_game(client, config_data, discord_messages, message, game_parameters, logger):
    """
    Start a game
    :param config_data:
    :param discord_messages:
    :param message:
    :param game_parameters:
    :param logger:
    :return:
    """

    try:
        # Validate the number of game parameters
        if len(game_parameters) != 7:
            raise ValueError("Error parsing parameters for starting a game. Expected 7 parameters.")

        # Extract game parameters
        season, subdivision, home_team, away_team, tv_channel, start_time, location = map(str.strip, game_parameters)

        # Create game channel
        channel_name = f"{away_team} at {home_team} S{season} {subdivision}"
        game_channel = await create_channel(message, channel_name, "Games", logger)

        # Get discord tag of the away coach
        away_coach = await get_user_by_team(config_data, away_team, logger)
        away_coach_tag = away_coach['discordTag']

        # Get discord user object of the away coach
        away_coach_discord_object = await get_discord_user_by_name(client, away_coach_tag, logger)

        # Start the game
        await post_game(config_data, game_channel.id, season, subdivision, home_team, away_team, tv_channel, start_time,
                        location, logger)

        # Prompt for coin toss
        start_game_message = discord_messages["gameStartMessage"].format(
            away_coach_discord_object=away_coach_discord_object.mention)

        await create_message(game_channel, start_game_message, logger)

    except ValueError as ve:
        error_message = f"Error starting game: {ve}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)

        # If an error occurs, delete the game channel if it was created
        delete_game(config_data, game_channel, logger)

    except Exception as e:
        error_message = f"An unexpected error occurred while starting the game:\n{e}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)

        # If an error occurs, delete the game channel if it was created
        delete_game(config_data, game_channel, logger)


async def delete_game(config_data, game_channel, logger):
    """
    Delete the game from the database and delete the channel

    :param config_data:
    :param game_channel:
    :param logger:
    :return:
    """

    try:
        game_object = await get_ongoing_game_by_channel_id(config_data, game_channel.id, logger)
        await delete_ongoing_game(config_data, game_object['gameId'], logger)

        if 'game_channel' in locals() and game_channel:
            await delete_channel(game_channel, logger)

    except Exception as e:
        error_message = f"An unexpected error occurred while deleting the game:\n{e}"
        await create_message(game_channel, error_message, logger)
        logger.error(error_message)
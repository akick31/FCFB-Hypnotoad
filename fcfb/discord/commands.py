import sys
import discord
import logging

from fcfb.discord.game import start_game, delete_game, validate_and_submit_defensive_number, \
    message_defense_for_number, get_user_objects, validate_and_submit_offensive_number
from fcfb.discord.utils import create_message, get_discord_user_by_name
from fcfb.api.zebstrika.games import get_ongoing_game_by_thread_id, run_coin_toss, update_coin_toss_choice, \
    update_waiting_on
from fcfb.api.zebstrika.users import get_user_by_team
from fcfb.main.exceptions import async_exception_handler, GameError, InvalidParameterError
from fcfb.discord.game import validate_waiting_on

sys.path.append("..")

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
async def parse_game_thread_commands(client, config_data, discord_messages, message):
    """
    Handle commands from Discord users in a game thread.

    :param client:
    :param config_data:
    :param discord_messages:
    :param message:
    :return:
    """

    game_object = await get_ongoing_game_by_thread_id(config_data, message.channel.id)
    home_user_object, away_user_object = await get_user_objects(config_data, game_object)

    message_content_lower = message.content.lower()
    message_content = message.content

    try:
        validate_waiting_on(message, game_object, home_user_object, away_user_object)
        if ("heads" in message_content or "tails" in message_content) and game_object["coinTossWinner"] == "None":
            await coin_toss_command(client, config_data, game_object, discord_messages, message_content_lower, message)
        elif ("receive" in message_content or "defer" in message_content) and \
             (game_object["coinTossWinner"] != "None" and game_object["coinTossChoice"] == "None"):
            await coin_toss_choice_command(client, config_data, discord_messages, message_content_lower, message)
        else:
            await validate_and_submit_offensive_number(client, config_data, discord_messages, message)

    except Exception as e:
        await create_message(message.channel, f"ERROR: {e}")
        raise Exception(e)


@async_exception_handler()
async def parse_commands(client, config_data, discord_messages, prefix, message):
    """
    Handle commands from Discord users.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param prefix: Command prefix.
    :param message: Discord message object.
    :return: None
    """

    message_content_lower = message.content.lower()
    message_content = message.content

    try:
        if message_content_lower.startswith(prefix + 'help'):
            await display_help_command(message.channel, prefix)

        # TODO make sure only admins can do certain commands
        elif message_content_lower.startswith(prefix + 'start'):
            command = message_content.split('start')[1].strip()
            await start_game_command(client, config_data, discord_messages, command, message)

        elif message_content_lower.startswith(prefix + 'delete'):
            await delete_game_command(config_data, message)

        elif message_content_lower.startswith(prefix + 'choice'):
            coin_toss_choice = message_content.split('choice')[1].strip()
            await coin_toss_choice_command(client, config_data, discord_messages, coin_toss_choice, message)

    except Exception as e:
        await create_message(message.channel, f"ERROR: {e}")
        raise Exception(e)


@async_exception_handler()
async def parse_direct_message_number_submission(client, config_data, discord_messages, message):
    """
    Handle direct messages from Discord users.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param message: Discord message object.
    :return: None
    """

    await validate_and_submit_defensive_number(client, config_data, discord_messages, message)


@async_exception_handler()
async def display_help_command(channel, prefix):
    """
    Display help command with usage information.

    :param channel: Discord channel.
    :param prefix: Command prefix.
    :return: None
    """

    command_list = "start\n"
    parameters_list = "[season, week, subdivision, home team, away team, tv channel, start time, location, " \
                      "is scrimmage?]\n"
    example_list = prefix + "start 9, 1, FBS, Ohio State, Michigan, ABC, 12:00 PM, War Memorial Stadium, yes]\n"

    embed = discord.Embed(
        title="Hypnotoad Commands",
        color=discord.Color.green()
    )
    embed.add_field(name="Command", value=command_list, inline=True)
    embed.add_field(name="Parameters", value=parameters_list, inline=True)
    embed.add_field(name="Example", value=example_list, inline=True)
    await create_message(channel, "", embed)
    logger.info("SUCCESS: Help command processed")


@async_exception_handler()
async def start_game_command(client, config_data, discord_messages, command, message):
    """
    Handle command to start a game.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param command: Command string.
    :param message: Discord message object.
    :return: None
    """

    try:
        game_parameters = command.split('[')[1].split(']')[0].split(',')
        if len(game_parameters) != 9:
            raise InvalidParameterError(f"Expected 9 parameters but was {len(game_parameters)}.")

        logger.info("Starting game with parameters: " + str(game_parameters))
        await start_game(client, config_data, discord_messages, game_parameters)
        success_message = f"SUCCESS: Game started with parameters: {game_parameters} in channel: {message.channel.id}"
        logger.info(success_message)
        await create_message(message.channel, success_message)

    except Exception as e:
        raise Exception(e)


@async_exception_handler()
async def coin_toss_command(client, config_data, game_object, discord_messages, coin_toss_call, message):
    """
    Handle command to call a coin toss.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param game_object: Game object.
    :param discord_messages: Discord messages.
    :param coin_toss_call: The coin toss call, heads or tails.
    :param message: Discord message object.
    :return: None
    """

    try:
        game_id = game_object["gameId"]

        # Get coin toss choice
        if coin_toss_call not in ['heads', 'tails']:
            raise GameError("Invalid coin toss call, options are **heads** or **tails**")

        logger.info("Coin toss called: " + str(coin_toss_call))

        game_object = await run_coin_toss(config_data, game_id, coin_toss_call)

        coin_toss_winning_coach = await get_user_by_team(config_data, game_object["coinTossWinner"])
        coin_toss_winning_coach_tag = coin_toss_winning_coach['discordTag']

        coin_toss_winning_coach_object = await get_discord_user_by_name(client, coin_toss_winning_coach_tag)

        # Update waiting on
        await update_waiting_on(config_data, game_id, coin_toss_winning_coach["username"])

        # Make Discord comment
        coin_toss_result_message = discord_messages["coinTossResultMessage"].format(
            winner=coin_toss_winning_coach_object.mention)
        await create_message(message.channel, coin_toss_result_message)
        logger.info("SUCCESS: Coin toss was run and won by " + str(coin_toss_winning_coach["username"]) +
                    " in thread " + str(message.channel.id) + " with call " + str(coin_toss_call))

    except Exception as e:
        raise Exception(e)


@async_exception_handler()
async def coin_toss_choice_command(client, config_data, discord_messages, coin_toss_choice, message):
    """
    Handle command to update a coin toss choice to receive or defer.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param coin_toss_choice: The coin toss choice, receive or defer.
    :param message: Discord message object.
    :return: None
    """

    try:
        # Verify game is waiting on coin toss choice
        game_object = await get_ongoing_game_by_thread_id(config_data, message.channel.id)
        if game_object["coinTossChoice"] == "receive" or game_object["coinTossWinner"] == "defer":
            raise GameError("Game is not waiting on a coin toss choice at this time")

        game_id = game_object["gameId"]

        # Get coin toss choice as receive or defer
        if coin_toss_choice not in ['receive', 'defer']:
            raise GameError("Invalid choice, game is expecting a coin toss choice of **receive** or **defer**")

        logger.info("Coin toss choice selected: " + str(coin_toss_choice))

        game_object = await update_coin_toss_choice(config_data, game_id, coin_toss_choice)

        # Make Discord comment
        coin_toss_choice_message = discord_messages["coinTossChoiceMessage"].format(
            winner=game_object["coinTossWinner"],
            choice=game_object["coinTossChoice"])
        await create_message(message.channel, coin_toss_choice_message)

        # Update the team waiting on
        coin_toss_winner = game_object["coinTossWinner"]
        coin_toss_choice = game_object["coinTossChoice"]

        if coin_toss_winner == game_object["homeTeam"]:
            receiving_team = game_object["awayTeam"] if coin_toss_choice == "defer" else game_object["homeTeam"]
        elif coin_toss_winner == game_object["awayTeam"]:
            receiving_team = game_object["homeTeam"] if coin_toss_choice == "defer" else game_object["awayTeam"]
        else:
            raise GameError("Invalid coin toss winner")

        await message_defense_for_number(client, config_data, discord_messages, message, game_object, receiving_team)
        logger.info("SUCCESS: Coin toss choice was updated to " + str(coin_toss_choice) + " in thread "
                    + str(message.channel.id))

    except Exception as e:
        raise Exception(e)


@async_exception_handler()
async def delete_game_command(config_data, message):
    """
    Handle command to delete a game in the current thread.

    :param config_data: Configuration data.
    :param message: Discord message object.
    :return: None
    """

    try:
        logger.info(f"Deleting game in thread {message.channel.id}")
        await delete_game(config_data, message.channel)
        logger.info(f"SUCCESS: Game deleted in thread {message.channel.id}")

    except Exception as e:
        raise Exception(e)


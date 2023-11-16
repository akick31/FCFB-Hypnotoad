import sys
import discord
import re
from discord.ext.commands import bot

from fcfb.api.zebstrika_game_plays import submit_defensive_number
from fcfb.discord.game import start_game, delete_game
from fcfb.discord.utils import create_message, create_message_with_embed, get_discord_user_by_name, send_direct_message, \
    get_channel_by_id
from fcfb.api.zebstrika_games import get_ongoing_game_by_channel_id, run_coin_toss, update_coin_toss_choice, \
    update_waiting_on, get_ongoing_game_by_id
from fcfb.api.zebstrika_users import get_user_by_team

sys.path.append("..")


async def parse_commands(client, config_data, discord_messages, prefix, message, logger):
    """
    Handle commands from Discord users.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param prefix: Command prefix.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    message_content_lower = message.content.lower()
    message_content = message.content

    try:
        if message_content_lower.startswith(prefix + 'help'):
            await display_help_command(message.channel, logger)

        # TODO make sure only admins can do certain commands
        elif message_content_lower.startswith(prefix + 'start'):
            command = message_content.split('start')[1].strip()
            await start_game_command(client, config_data, discord_messages, command, message, logger)

        elif message_content_lower.startswith(prefix + 'delete'):
            await delete_game_command(client, config_data, discord_messages, message, logger)

        elif message_content_lower.startswith(prefix + 'coin'):
            coin_toss_choice = message_content.split('coin')[1].strip()
            await coin_toss_command(client, config_data, discord_messages, coin_toss_choice, message, logger)

        elif message_content_lower.startswith(prefix + 'choice'):
            coin_toss_choice = message_content.split('choice')[1].strip()
            await coin_toss_choice_command(client, config_data, discord_messages, coin_toss_choice, message, logger)

    except Exception as e:
        logger.error("An unexpected error occurred", exc_info=True)
        raise Exception("An unexpected error occurred")


async def validate_and_submit_defensive_number(client, config_data, discord_messages, message, logger):
    """
    Validate the defensive number and submit it to the API

    :param client:
    :param config_data:
    :param discord_messages:
    :param message:
    :param logger:
    :return:
    """
    try:
        game_id, prev_message_content = await find_previous_number_submit_embed_and_get_game_id(client, message)
        game_id = game_id.split("**Game ID: ")[1].split("**")[0].strip() if game_id is not None else None
        validate_game_id(game_id)

        game_object, home_user_object, away_user_object = await get_game_and_user_objects(config_data, game_id, logger)

        validate_waiting_on(message, game_object, home_user_object, away_user_object)

        validate_possession(message, game_object, home_user_object, away_user_object)

        defensive_number = parse_defensive_number(message.content)
        validate_defensive_number(defensive_number)

        username = get_opponent_username(game_object, home_user_object, away_user_object)

        # Submit defensive number and update waiting on
        await submit_defensive_number(config_data, game_id, defensive_number, logger)
        await update_waiting_on(config_data, game_id, username, logger)

        # Send confirmation DM and send the prompt for the offensive number
        await send_direct_message(message.author, f"Your defensive number has been submitted, it is {defensive_number}", logger)

        # Send the prompt for the offensive number
        embed = await craft_number_request_embed(config_data, message, logger, game_object["platformId"])

        if username == home_user_object["username"]:
            offensive_coach = home_user_object
        else:
            offensive_coach = away_user_object
        offensive_coach_tag = offensive_coach["discordTag"]

        offensive_coach_discord_object = await get_discord_user_by_name(client, offensive_coach_tag, logger)

        if prev_message_content == discord_messages["kickingNumberMessage"]:
            number_request_message = discord_messages["kickingNumberRequestMessage"].format(
                message_author=message.author.mention,
                offensive_coach_discord_object=offensive_coach_discord_object.mention)
        else:
            number_request_message = discord_messages["normalNumberRequestMessage"].format(
                message_author=message.author.mention,
                offensive_coach_discord_object=offensive_coach_discord_object.mention)

        channel = await get_channel_by_id(client, config_data, game_object["platformId"], logger)
        await create_message_with_embed(channel, number_request_message, embed, logger)

    except ValueError as ve:
        exception_message = str(ve)
        logger.error(exception_message)
        await create_message(message.channel, exception_message, logger)

    except Exception as e:
        exception_message = f"An unexpected error occurred while submitting a defensive number:\n{e}"
        logger.error(exception_message, exc_info=True)
        await create_message(message.channel, exception_message, logger)
        raise Exception(exception_message)


async def get_game_and_user_objects(config_data, game_id, logger):
    """
    Get the game and user objects from the game id
    :param config_data:
    :param game_id:
    :param logger:
    :return:
    """

    game_object = await get_ongoing_game_by_id(config_data, game_id, logger)
    home_user_object = await get_user_by_team(config_data, game_object["homeTeam"], logger)
    away_user_object = await get_user_by_team(config_data, game_object["awayTeam"], logger)

    return game_object, home_user_object, away_user_object


def validate_game_id(game_id):
    """
    Validate the game id
    :param game_id:
    :return:
    """

    if game_id is None:
        raise ValueError("Could not find a valid game id in previous messages, are you sure you are in a game?")


def validate_waiting_on(message, game_object, home_user_object, away_user_object):
    """
    Validate the user is waiting on a number from them

    :param message:
    :param game_object:
    :param home_user_object:
    :param away_user_object:
    :return:
    """
    waiting_on_username = game_object["waitingOn"]
    user_object = home_user_object if waiting_on_username == home_user_object["username"] else away_user_object

    if user_object["discordTag"] != message.author.name:
        raise ValueError(f"I am not waiting on a number from you currently. Currently waiting on a number from {waiting_on_username}")


def validate_possession(message, game_object, home_user_object, away_user_object):
    """
    Validate the user does not have possession of the ball
    :param message:
    :param game_object:
    :param home_user_object:
    :param away_user_object:
    :return:
    """

    possession, author_name = game_object["possession"], message.author.name

    if (possession == "home" and home_user_object["discordTag"] == author_name) or (possession == "away" and away_user_object["discordTag"] == author_name):
        raise ValueError("You have possession, please submit your number in the game channel instead")


def parse_defensive_number(message_content):
    """
    Parse the defensive number from the message content

    :param message_content:
    :return:
    """

    defensive_number = re.search(r'\b\d+\b', message_content)

    if defensive_number:
        return int(defensive_number.group())
    else:
        raise ValueError("I could not find a valid number in your message, please try again")


def validate_defensive_number(defensive_number):
    """
    Validate the defensive number is between 1 and 1500, inclusive

    :param defensive_number:
    :return:
    """

    if not (1 <= defensive_number <= 1500):
        raise ValueError("The number you submitted is not between 1 and 1500, please try again")


def get_opponent_username(game_object, home_user_object, away_user_object):
    """
    Get the username of the opponent of the user who submitted the number

    :param game_object:
    :param home_user_object:
    :param away_user_object:
    :return:
    """

    return away_user_object["username"] if game_object["waitingOn"] == home_user_object["username"] else home_user_object["username"]


async def parse_direct_message_number_submission(client, config_data, discord_messages, message, logger):
    """
    Handle direct messages from Discord users.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    await validate_and_submit_defensive_number(client, config_data, discord_messages, message, logger)


async def find_previous_number_submit_embed_and_get_game_id(client, message):
    """
    Find the previous embed from the bot asking the user to submit a number and get the game id from it

    :param client:
    :param message:
    :return:
    """

    async for prev_message in message.channel.history(limit=100):
        if prev_message.author.id == client.user.id and prev_message.id != message.id:
            # Check if the previous bot message has an embed with the specified title
            if prev_message.embeds and prev_message.embeds[0].title == "Submit a Number":
                embed_data = prev_message.embeds[0].to_dict()
                game_id = embed_data['description'] if 'description' in embed_data else None
                prev_message_content = prev_message.content
                break  # Exit the loop once the desired message is found
    else:
        game_id = None  # If the loop completes without finding the message, set game_id to None
    return game_id, prev_message_content


async def display_help_command(channel, prefix, logger):
    """
    Display help command with usage information.

    :param channel: Discord channel.
    :param prefix: Command prefix.
    :param logger: Logger object.
    :return: None
    """

    command_list = "start\n"
    parameters_list = "[season, subdivision, home team, away team, tv channel, start time, location]\n"
    example_list = prefix + "start [9, FBS, Ohio State, Michigan, ABC, 12:00 PM, War Memorial Stadium]\n"

    embed = discord.Embed(
        title="Hypnotoad Commands",
        color=discord.Color.green()
    )
    embed.add_field(name="Command", value=command_list, inline=True)
    embed.add_field(name="Parameters", value=parameters_list, inline=True)
    embed.add_field(name="Example", value=example_list, inline=True)
    await create_message_with_embed(channel, "", embed, logger)
    logger.info("SUCCESS: Help command processed")


async def start_game_command(client, config_data, discord_messages, command, message, logger):
    """
    Handle command to start a game.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param command: Command string.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    try:
        game_parameters = command.split('[')[1].split(']')[0].split(',')
        if len(game_parameters) != 7:
            raise ValueError("Error parsing parameters for start game command")

        logger.info("Starting game with parameters: " + str(game_parameters))
        await start_game(client, config_data, discord_messages, message, game_parameters, logger)
        logger.info("SUCCESS: Game started with parameters: " + str(game_parameters) + " in channel: " + str(message.channel.id))

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
        raise ValueError(exception_message)
    except Exception as e:
        logger.error("An unexpected error occurred:", exc_info=True)
        raise Exception("An unexpected error occurred")


async def coin_toss_command(client, config_data, discord_messages, coin_toss_call, message, logger):
    """
    Handle command to call a coin toss.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param coin_toss_call: The coin toss call, heads or tails.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    try:
        # Verify game is waiting on coin toss
        game_object = await get_ongoing_game_by_channel_id(config_data, message.channel.id, logger)
        if game_object["coinTossWinner"] is not None and game_object["coinTossWinner"] != "None":
            raise ValueError("Game is not waiting on a coin toss")

        game_id = game_object["gameId"]

        # Get coin toss choice
        if coin_toss_call not in ['heads', 'tails']:
            raise ValueError("Invalid coin toss call, please call **heads** or **tails**")

        logger.info("Coin toss called: " + str(coin_toss_call))

        game_object = await run_coin_toss(config_data, game_id, coin_toss_call, logger)

        coin_toss_winning_coach = await get_user_by_team(config_data, game_object["coinTossWinner"], logger)
        coin_toss_winning_coach_tag = coin_toss_winning_coach['discordTag']

        coin_toss_winning_coach_object = await get_discord_user_by_name(client, coin_toss_winning_coach_tag, logger)

        # Update waiting on
        await update_waiting_on(config_data, game_id, coin_toss_winning_coach["username"], logger)

        # Make Discord comment
        coin_toss_result_message = discord_messages["coinTossResultMessage"].format(
            winner=coin_toss_winning_coach_object.mention)
        await create_message(message.channel, coin_toss_result_message, logger)
        logger.info("SUCCESS: Coin toss was run and won by " + str(coin_toss_winning_coach["username"]) +
                    " in channel " + str(message.channel.id) + " with call " + str(coin_toss_call))

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
    except Exception as e:
        error_message = f"An unexpected error occurred while processing the coin toss:\n{e}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)
        raise Exception(error_message)


async def coin_toss_choice_command(client, config_data, discord_messages, coin_toss_choice, message, logger):
    """
    Handle command to update a coin toss choice to receive or defer.

    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param coin_toss_choice: The coin toss choice, receive or defer.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    try:
        # Verify game is waiting on coin toss choice
        game_object = await get_ongoing_game_by_channel_id(config_data, message.channel.id, logger)
        if game_object["coinTossChoice"] == "receive" or game_object["coinTossWinner"] == "defer":
            raise ValueError("Game is not waiting on a coin toss choice at this time")

        game_id = game_object["gameId"]

        # Get coin toss choice as receive or defer
        if coin_toss_choice not in ['receive', 'defer']:
            raise ValueError("Invalid choice, please select **receive** or **defer**")

        logger.info("Coin toss choice selected: " + str(coin_toss_choice))

        game_object = await update_coin_toss_choice(config_data, game_id, coin_toss_choice, logger)

        # Make Discord comment
        coin_toss_choice_message = discord_messages["coinTossChoiceMessage"].format(
            winner=game_object["coinTossWinner"],
            choice=game_object["coinTossChoice"])
        await create_message(message.channel, coin_toss_choice_message, logger)

        # Update the team waiting on
        coin_toss_winner = game_object["coinTossWinner"]
        coin_toss_choice = game_object["coinTossChoice"]

        if coin_toss_winner == game_object["homeTeam"]:
            receiving_team = game_object["awayTeam"] if coin_toss_choice == "defer" else game_object["homeTeam"]
        elif coin_toss_winner == game_object["awayTeam"]:
            receiving_team = game_object["homeTeam"] if coin_toss_choice == "defer" else game_object["awayTeam"]
        else:
            raise ValueError("Invalid coin toss winner")
        receiving_coach = await get_user_by_team(config_data, receiving_team, logger)

        await update_waiting_on(config_data, game_id, receiving_coach["username"], logger)

        embed = await craft_number_request_embed(config_data, message, logger)
        receiving_coach_tag = receiving_coach["discordTag"]
        receiving_coach_discord_object = await get_discord_user_by_name(client, receiving_coach_tag, logger)
        kicking_number_message = discord_messages["kickingNumberMessage"]

        await send_direct_message(receiving_coach_discord_object, kicking_number_message, logger, embed)
        logger.info("SUCCESS: Coin toss choice was updated to " + str(coin_toss_choice) + " in channel " + str(message.channel.id))

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
    except Exception as e:
        error_message = f"An unexpected error occurred while processing the coin toss choice:\n{e}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)
        raise Exception(error_message)


async def craft_number_request_embed(config_data, message, logger, channel_id=None):
    """
    Create the embed for number requests

    :param config_data:
    :param message:
    :param logger:
    :param channel_id:
    :return:
    """

    if channel_id is None:
        game_object = await get_ongoing_game_by_channel_id(config_data, message.channel.id, logger)
    else:
        game_object = await get_ongoing_game_by_channel_id(config_data, channel_id, logger)
    home_score, away_score = int(game_object["homeScore"]), int(game_object["awayScore"])
    down, yards_to_go = game_object["down"], game_object["yardsToGo"]
    ball_location = game_object["ballLocation"]
    possession, home_team, away_team = game_object["possession"], game_object["homeTeam"], game_object["awayTeam"]

    score_text = (f"{home_team} leads {away_team} {home_score}-{away_score}" if home_score > away_score else
                  f"{away_team} leads {home_team} {home_score}-{away_score}" if home_score < away_score else
                  f"{home_team} and {away_team} are tied {home_score}-{away_score}")

    down_and_distance = f"{down}{'st' if down == 1 else 'nd' if down == 2 else 'rd' if down == 3 else 'th'} and {yards_to_go}"

    yard_line = (f"{away_team} {100 - ball_location}" if ball_location > 50 and possession == home_team else
                 f"{home_team} {100 - ball_location}" if ball_location > 50 and possession == away_team else
                 f"{home_team} {ball_location}" if possession == home_team else
                 f"{away_team} {ball_location}")

    status_message = f"{score_text}\nQ{game_object['quarter']} | {game_object['clock']} | {down_and_distance} | :football: {yard_line}"

    embed = discord.Embed(
        title="Submit a Number",
        description=f"**Game ID: {game_object['gameId']}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Status", value=status_message, inline=False)
    embed.add_field(name="Instructions", value="Please submit a number between **1** and **1500**, inclusive", inline=False)
    embed.add_field(name="Deadline", value=f"You have until {game_object['gameTimer']} to submit a number", inline=False)

    return embed


async def delete_game_command(client, config_data, discord_messages, message, logger):
    """
    Handle command to delete a game in the current channel.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    try:
        logger.info(f"Deleting game in channel {message.channel.id}")
        await delete_game(config_data, message.channel, logger)
        logger.info(f"SUCCESS: Game deleted in channel {message.channel.id}")

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
        raise ValueError(exception_message)
    except Exception as e:
        logger.error("An unexpected error occurred:", exc_info=True)
        raise Exception("An unexpected error occurred")
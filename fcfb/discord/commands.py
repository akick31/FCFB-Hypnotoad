import sys
import discord

from fcfb.discord.game import start_game, delete_game, validate_and_submit_defensive_number, \
    validate_and_submit_offensive_number, message_defense_for_number
from fcfb.discord.utils import create_message, create_message_with_embed, get_discord_user_by_name, \
    check_if_channel_is_game_channel
from fcfb.api.zebstrika.games import get_ongoing_game_by_channel_id, run_coin_toss, update_coin_toss_choice, \
    update_waiting_on
from fcfb.api.zebstrika.users import get_user_by_team

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
            await display_help_command(message.channel, prefix, logger)

        # TODO make sure only admins can do certain commands
        elif message_content_lower.startswith(prefix + 'start'):
            command = message_content.split('start')[1].strip()
            await start_game_command(client, config_data, discord_messages, command, message, logger)

        elif message_content_lower.startswith(prefix + 'delete'):
            await delete_game_command(config_data, message, logger)

        elif message_content_lower.startswith(prefix + 'coin'):
            coin_toss_choice = message_content.split('coin')[1].strip()
            await coin_toss_command(client, config_data, discord_messages, coin_toss_choice, message, logger)

        elif message_content_lower.startswith(prefix + 'choice'):
            coin_toss_choice = message_content.split('choice')[1].strip()
            await coin_toss_choice_command(client, config_data, discord_messages, coin_toss_choice, message, logger)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise Exception("An unexpected error occurred")


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


async def parse_game_channel_messages(client, config_data, discord_messages, message, logger):
    """
    Handle messages from game channels.

    :param client: Discord client.
    :param config_data: Configuration data.
    :param discord_messages: Discord messages.
    :param message: Discord message object.
    :param logger: Logger object.
    :return: None
    """

    await validate_and_submit_offensive_number(client, config_data, discord_messages, message, logger)


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
    example_list = prefix + "start 9, FBS, Ohio State, Michigan, ABC, 12:00 PM, War Memorial Stadium]\n"

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
        success_message = f"SUCCESS: Game started with parameters: {game_parameters} in channel: {message.channel.id}"
        logger.info(success_message)
        await create_message(message.channel, success_message, logger)

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
        raise ValueError(exception_message)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
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

    :param client: Discord client.
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

        await message_defense_for_number(client, config_data, discord_messages, message, game_object, receiving_team,
                                         logger)
        logger.info("SUCCESS: Coin toss choice was updated to " + str(coin_toss_choice) + " in channel "
                    + str(message.channel.id))

    except ValueError as ve:
        exception_message = str(ve)
        await create_message(message.channel, exception_message, logger)
    except Exception as e:
        error_message = f"An unexpected error occurred while processing the coin toss choice:\n{e}"
        await create_message(message.channel, error_message, logger)
        logger.error(error_message)
        raise Exception(error_message)


async def delete_game_command(config_data, message, logger):
    """
    Handle command to delete a game in the current channel.

    :param config_data: Configuration data.
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
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise Exception("An unexpected error occurred")
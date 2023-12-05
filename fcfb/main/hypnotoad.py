import json
import pathlib
import logging
import sys

sys.path.append("..")


def hypnotoad():
    """
    Run Hypnotoad.

    :return:
    """
    from fcfb.discord.runner import run_hypnotoad
    run_hypnotoad(config_data, discord_messages)


if __name__ == '__main__':
    proj_dir = str(pathlib.Path(__file__).parent.absolute().parent.absolute())
    with open(proj_dir + '/configuration/config.json', 'r') as config_file:
        config_data = json.load(config_file)

    with open(proj_dir + '/resources/messages.json', 'r') as discord_messages_file:
        discord_messages = json.load(discord_messages_file)

    # Run Hypnotoad
    hypnotoad()

# TODO: Move game ID to footer of embed
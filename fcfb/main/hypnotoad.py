import json
import asyncio
import pathlib
import logging
import sys

sys.path.append("..")

from fcfb.discord.runner import run_hypnotoad

def hypnotoad(config_data, logger):
    """
    Run Hypnotoad.

    :param config_data:
    :param logger:
    :return:
    """

    run_hypnotoad(config_data, logger)


if __name__ == '__main__':
    proj_dir = str(pathlib.Path(__file__).parent.absolute().parent.absolute())
    with open(proj_dir + '/configuration/config.json', 'r') as config_file:
        config_data = json.load(config_file)

    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger("hypnotoad_logger")

    # Add Handlers
    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
    stream_handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(stream_handler)

    hypnotoad(config_data, logger)

import requests


async def send_post_request_to_zebstrika(configData, payload, logger):
    """
    Make api call to start game

    :param configData
    :param payload:
    :return:
    """

    endpoint = configData['api']['url'] + payload
    response = requests.post(endpoint)
    if response.status_code == 201:
        gameInfo = response.json()
        return gameInfo
    else:
        exceptionMessage = "HTTP" + str(response.status_code) + " response " + str(response.text)
        logger.error(exceptionMessage)
        raise Exception(exceptionMessage)

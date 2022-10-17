import requests


class TelegramClient:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url

    def init_url(self, method: str):
        result_url = f"{self.base_url}bot{self.token}/"

        # TODO: check if 'method' is a valid Telegram API method
        if method is not None:
            result_url += method
        return result_url

    def post(self, method: str = None, params: dict = None, data: dict = None):
        url = self.init_url(method)

        # TODO: check if the data is valid
        response = requests.post(url, params=params, data=data)
        return response.json()


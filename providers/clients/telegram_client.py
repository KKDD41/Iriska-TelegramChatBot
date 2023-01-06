import requests


class TelegramClient:
    __slots__ = "token", "base_url"

    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url

    def init_url(self, method: str):
        result_url = f"{self.base_url}bot{self.token}/"
        if method is not None:
            result_url += method
        return result_url

    def post(self, method: str = None, params: dict = None, data: dict = None):
        url = self.init_url(method)
        response = requests.post(url, params=params, data=data)
        return response.json()

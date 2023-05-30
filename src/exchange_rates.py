import json
import requests

from dataclasses import dataclass
from typing import Dict
from loguru import logger


# @dataclass
class ExchangeRateUpdate:

    # path_settings: str
    __API_RATES = "https://api.exchangerate-api.com/v4/latest/RUB"

    def __init__(self, path_settings: str):
        self.path_settings = path_settings

    def refresh_rates_from_api(self, rates: Dict) -> None:
        try:
            response = requests.get(self.__API_RATES)
            new_rates = response.json()["rates"]
        except requests.exceptions.SSLError:
            logger.error('Не могу получить обменный курс! Попробуйте позже или измените API хоста')
            raise AssertionError("[FAIL] Cannot get exchange rate! Try later or change the host API")

        for currency in rates:
            rates[currency] = new_rates[currency]

        rates["RUR"] = rates.pop("RUB")

    def save_rates(self, rates: Dict) -> None:

        with open(self.path_settings, "r") as cfg:
            data = json.load(cfg)

        data["rates"] = rates

        with open(self.path_settings, "w") as cfg:
            json.dump(data, cfg, indent=2)


if __name__ == "__main__":
    _exchanger = ExchangeRateUpdate("../settings.json")
    _default = {"RUB": None, "USD": None, "EUR": None, "UAH": None}
    _exchanger.refresh_rates_from_api(_default)
    _exchanger.save_rates(_default)
    for _k, _v in _default.items():
        print(f"{_k}: {_v :.05f}")

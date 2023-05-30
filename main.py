import os

from dataclasses import dataclass
from loguru import logger
from src.stats import Statistics
from src.exchange_rates import ExchangeRateUpdate
from src.generate_data import Data
from src.commands import Settings
from src.forecast import Forecast

CACHE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cache")
SETTINGS_PATH = "settings.json"


@dataclass
class SearchAnalyzingHHData:
    """Основной класс для поиска вакансий и их анализа."""

    collector: Data | None = None
    analyzer: Statistics | None = None
    predictor: Forecast = Forecast()
    settings: Settings = Settings(SETTINGS_PATH, no_parse=False)
    exchanger: ExchangeRateUpdate | None = ExchangeRateUpdate(SETTINGS_PATH)

    def settings_refresh(self, **kwargs):
        """ Обновление настроек из файла """
        self.settings.update_params(**kwargs)
        if not any(self.settings.rates.values()) or self.settings.update:
            # logger.info(f"Попытка получить курсы обмена с удаленного сервера...")
            self.exchanger.refresh_rates_from_api(self.settings.rates)
            self.exchanger.save_rates(self.settings.rates)

        # logger.info(f"Получить курс валюты: {self.settings.rates}")
        self.collector = Data(self.settings.rates)
        self.analyzer = Statistics(self.settings.save_result)

    def __call__(self):
        # logger.info(f"Собираем данные...")
        vacancies = self.collector.collect_vacancies(
            query=self.settings.options,
            refresh=self.settings.refresh,
            num_workers=self.settings.num_workers
        )
        # logger.info(f"Подготовка dataframe...")
        df = self.analyzer.prepare_df(vacancies)
        self.analyzer.analyze_df(df)
        # total_df = self.predictor.predict(df)
        # self.predictor.plot_results(total_df)
        logger.success('Выполнено! Выход')


if __name__ == "__main__":
    initialization = SearchAnalyzingHHData()
    initialization.settings_refresh()
    initialization()

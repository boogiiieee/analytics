import os
import re
import pickle
import hashlib
import time

import requests

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Tuple
from urllib.parse import urlencode
from tqdm import tqdm
from loguru import logger

CACHE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cache")


@dataclass
class Data:

    _rates: Dict | None = None
    __API_BASE_URL: str = "https://api.hh.ru/vacancies/"
    __DICT_KEYS: Tuple = (
        "Ids",
        "Employer",
        "Name",
        "Salary",
        "From",
        "To",
        "Experience",
        "Schedule",
        "Keys",
        "Description",
    )

    @staticmethod
    def delete_html_tags(html_text: str) -> str:
        pattern = re.compile("<.*?>")
        return re.sub(pattern, "", html_text)

    @staticmethod
    def __convert_gross(is_gross: bool) -> float:
        return 0.87 if is_gross else 1

    def get_vacancy(self, vacancy_id: str):
        # Get data from URL
        url = f"{self.__API_BASE_URL}{vacancy_id}"
        vacancy = requests.api.get(url).json()
        if 'errors' in vacancy.keys():
            logger.warning("Required captcha...")
        # Extract salary
        salary = vacancy.get("salary")

        # Calculate salary:
        # Get salary into {RUB, USD, EUR} with {Gross} parameter and
        # return a new salary in RUB.
        from_to = {"from": None, "to": None}
        if salary:
            is_gross = vacancy["salary"].get("gross")
            for k, v in from_to.items():
                if vacancy["salary"][k] is not None:
                    _value = self.__convert_gross(is_gross)
                    from_to[k] = int(_value * salary[k] / self._rates[salary["currency"]])

        # Create pages tuple
        return (
            vacancy_id,
            vacancy["employer"]["name"],
            vacancy["name"],
            salary is not None,
            from_to["from"],
            from_to["to"],
            vacancy["experience"]["name"],
            vacancy["schedule"]["name"],
            [key_skills["name"] for key_skills in vacancy["key_skills"]],
            self.delete_html_tags(vacancy["description"]),
        )

    @staticmethod
    def __encode_query_for_url(query: Dict | None) -> str:
        if 'professional_roles' in query:
            query_copy = query.copy()

            roles = '&'.join([f'professional_role={r}' for r in query_copy.pop('professional_roles')])

            return roles + (f'&{urlencode(query_copy)}' if len(query_copy) > 0 else '')

        return urlencode(query)

    def collect_vacancies(
            self, query: Dict | None,
            refresh: bool = False,
            num_workers: int = 1) -> Dict:

        if num_workers is None or num_workers < 1:
            num_workers = 1

        url_params = self.__encode_query_for_url(query)

        # Get cached data if exists...
        cache_name: str = url_params
        cache_hash = hashlib.md5(cache_name.encode()).hexdigest()
        cache_file = os.path.join(CACHE_DIR, cache_hash)
        try:
            if not refresh:
                logger.info("Получаем результаты из кеша! Чтобы обновить результаты, вкл опцию обновления.")
                return pickle.load(open(cache_file, "rb"))
        except (FileNotFoundError, pickle.UnpicklingError) as e:
            logger.error(f"Произошла ошибка {e}")
            pass

        # Check number of pages...
        target_url = self.__API_BASE_URL + "?" + url_params
        num_pages = requests.get(target_url).json()["pages"]

        # Collect vacancy IDs...
        ids = []
        for idx in range(num_pages + 1):
            response = requests.get(target_url, {"page": idx})
            data = response.json()
            if "items" not in data:
                break
            ids.extend(x["id"] for x in data["items"])

        # Collect vacancies...
        jobs_list = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for vacancy in tqdm(
                executor.map(self.get_vacancy, ids),
                desc="Получаем данные с headhunters.ru",
                ncols=100,
                total=len(ids),
            ):
                jobs_list.append(vacancy)
                time.sleep(0.25)

        unzipped_list = list(zip(*jobs_list))
        result = {}
        for idx, key in enumerate(self.__DICT_KEYS):
            result[key] = unzipped_list[idx]

        pickle.dump(result, open(cache_file, "wb"))
        return result


if __name__ == "__main__":
    dc = Data({"USD": 0.01264, "EUR": 0.01083, "RUR": 1.00000})

    vacancies = dc.collect_vacancies(
        query={"text": "Python dev", "area": 1255, "per_page": 50},
        # refresh=True
    )
    print(vacancies["Employer"])

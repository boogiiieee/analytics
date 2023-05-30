import re
import nltk
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from dataclasses import dataclass
from typing import Dict, List
from loguru import logger


@dataclass
class Statistics:

    is_save_result_to_csv: bool = False

    @staticmethod
    def find_top_words_from_keys(keys_list: List) -> pd.Series:
        lst_keys = []
        for keys_elem in keys_list:
            for el in keys_elem:
                if el != "":
                    lst_keys.append(re.sub("'", "", el.lower()))

        set_keys = set(lst_keys)
        dct_keys = {el: lst_keys.count(el) for el in set_keys}
        srt_keys = dict(sorted(dct_keys.items(), key=lambda x: x[1], reverse=True))
        return pd.Series(srt_keys, name="Keys")

    @staticmethod
    def find_top_words_from_description(desc_list: List) -> pd.Series:
        words_ls = " ".join([re.sub(" +", " ", re.sub(r"\d+", "", el.strip().lower())) for el in desc_list])
        words_re = re.findall("[a-zA-Z]+", words_ls)
        words_l2 = [el for el in words_re if len(el) > 2]
        words_st = set(words_l2)
        try:
            _ = nltk.corpus.stopwords.words("english")
        except LookupError:
            nltk.download("stopwords")
        finally:
            stop_words = set(nltk.corpus.stopwords.words("english"))

        words_st ^= stop_words
        words_st ^= {"amp", "quot"}
        words_cnt = {el: words_l2.count(el) for el in words_st}
        return pd.Series(dict(sorted(words_cnt.items(), key=lambda x: x[1], reverse=True)))

    def prepare_df(self, vacancies: Dict) -> pd.DataFrame:

        # Create pandas dataframe
        df = pd.DataFrame.from_dict(vacancies)
        # Print some info from data frame
        # with pd.option_context("display.max_rows", None, "display.max_columns", None):
        #     print(df[df["Salary"]][["Employer", "From", "To", "Experience"]][0:15])
        # Save to file
        if self.is_save_result_to_csv:
            print("\n\n[INFO]: Сохраняем данные с hh.ru в файл csv...")
            df.to_csv(rf"vacancies_from_hh.csv", index=False)
            # logger.success(f"Данные сохранены в vacancies_from_hh.csv...")
        return df

    def analyze_df(self, df: pd.DataFrame):
        sns.set()

        print(f"\nВсего вакансий: {df['Ids'].count()}")
        print(df.loc[:, ~df.columns.isin(['Description', 'Keys'])])

        if len(df[(df['Experience'] == 'Нет опыта')]) > 0:
            print(f"\nВакансии без опыта работы: {len(df[(df['Experience'] == 'Нет опыта')])}")
            print(df[(df['Experience'] == 'Нет опыта')].loc[:, ~df.columns.isin(['Description', 'Keys'])])
            print(f"Процент ваканасий для выпускника без опыта: "
                  f"{round(len(df[(df['Experience'] == 'Нет опыта')]) / df['Ids'].count() * 100, 2)} %")

        if df["Salary"] is True:
            print("\nВакансии с максимальной зарплатой: ")
            print(df.iloc[df[["From", "To"]].idxmax()])

            print("\nВакансия с минимальной зарплатой: ")
            print(df.iloc[df[["From", "To"]].idxmin()])

        print("\nВсе работодатели: ")
        print(df["Employer"])

        # print("\n[INFO]: Describe salary data frame")
        # df_stat = df[["From", "To"]].describe().applymap(np.int32)
        # print(df_stat.iloc[list(range(4)) + [-1]])

        print('\n[INFO]: Средняя статистика (фильтр по параметрам "From"-"To"):')
        comb_ft = np.nanmean(df[df["Salary"]][["From", "To"]].to_numpy(), axis=1)
        print("Заработная плата:")
        print(f"Мин    : {np.min(comb_ft)}")
        print(f"Макс    : {np.max(comb_ft)}")
        print(f"Средняя   : {np.mean(comb_ft)}")
        print(f"Медиан : {np.median(comb_ft)}")

        print("\nНаиболее часто используемые слова [Keywords]:")
        most_keys = self.find_top_words_from_keys(df["Keys"].to_list())
        print(most_keys[:12])

        print("\nНаиболее часто используемые слова [Description]:")
        most_words = self.find_top_words_from_description(df["Description"].to_list())
        print(most_words[:12])

        fz = plt.figure("Графики заработной платы", figsize=(12, 8))
        fz.add_subplot(2, 2, 1)
        plt.title("From / To: Boxplot")
        sns.boxplot(data=df[["From", "To"]].dropna() / 1000, width=0.4)
        plt.ylabel("Salary x 1000 [RUB]")
        fz.add_subplot(2, 2, 2)
        plt.title("From / To: Swarmplot")
        sns.swarmplot(data=df[["From", "To"]].dropna() / 1000, size=6)

        fz.add_subplot(2, 2, 3)
        plt.title("From: Distribution ")
        sns.histplot(df["From"].dropna() / 1000, bins=14, color="C0", kde=True)
        plt.grid(True)
        plt.xlabel("Salary x 1000 [RUB]")
        plt.xlim([-50, df["From"].max() / 1000])
        plt.yticks([], [])

        fz.add_subplot(2, 2, 4)
        plt.title("To: Distribution")
        sns.histplot(df["To"].dropna() / 1000, bins=14, color="C1", kde=True)
        plt.grid(True)
        plt.xlim([-50, df["To"].max() / 1000])
        plt.xlabel("Salary x 1000 [RUB]")
        plt.yticks([], [])
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    statistic = Statistics()

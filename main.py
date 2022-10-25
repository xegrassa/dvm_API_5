import os
import urllib.parse
from collections import defaultdict
from typing import Callable

import requests
from dotenv import load_dotenv
from requests import HTTPError
from terminaltables import SingleTable

load_dotenv()

LANGUAGES = (
    "TypeScript",
    "Swift",
    "Scala",
    "Objective-C",
    "Shell",
    "Go",
    "C",
    "C#",
    "C++",
    "PHP",
    "Ruby",
    "Python",
    "Java",
    "JavaScript",
)

BASE_HH_URL = "https://api.hh.ru"
BASE_SJ_URL = "https://api.superjob.ru"
SJ_TOKEN = os.getenv("SJ_TOKEN")


def get_hh_salaries_by_language(language, period=30):
    """Используя API HH, возвращает вакансии для Программиста определенного языка.

    Args:
        language (str): Язык программирования по которому будет поиск вакансий
        period (int): Количество дней, в пределах которых нужно найти вакансии. Максимальное значение: 30

    Returns:
        dict: "found": кол-во найденных вакансий,
              "items": зарплаты вакансий
    """
    moscow_id = 1
    programming_role_id = 96  # "Программист, разработчик"

    endpoint = urllib.parse.urljoin(BASE_HH_URL, 'vacancies')
    hh_salaries = {
        "found": None,
        "items": [],
    }

    page = 0
    while True:
        payload = {
            "professional_role": programming_role_id,
            "area": moscow_id,
            "period": period,
            "text": f"Программист {language}",
            "per_page": 100,
            "page": page,
        }
        response = requests.get(url=endpoint, params=payload)
        response.raise_for_status()

        found_vacancies = response.json()
        vacancy_salaries = [vacancy["salary"] for vacancy in found_vacancies["items"]]

        hh_salaries["items"].extend(vacancy_salaries)
        hh_salaries["found"] = found_vacancies["found"]

        page += 1
        if page >= found_vacancies["pages"]:
            break

    return hh_salaries


def get_sj_salaries_by_language(language, period=None):
    """Используя API HH, возвращает вакансии для Программиста определенного языка.

    Args:
        language (str): Язык программирования по которому будет поиск вакансий
        period (int|None): Количество дней, в пределах которых нужно найти вакансии

    Returns:
        dict: "found": кол-во найденных вакансий,
              "items": зарплаты вакансий
    """
    moscow_id = 4
    programming_catalog_id = 48
    vacancy_on_page_count = 100

    endpoint = urllib.parse.urljoin(BASE_SJ_URL, "2.0/vacancies")
    sj_salaries = {
        "found": None,
        "items": [],
    }

    headers = {
        "X-Api-App-Id": SJ_TOKEN,
    }

    page = 0
    while True:
        payload = {
            "t": moscow_id,
            "catalogues": programming_catalog_id,
            "keyword": f"Программист {language}",
            "count": vacancy_on_page_count,
            "page": page,
        }
        response = requests.get(url=endpoint, headers=headers, params=payload)
        response.raise_for_status()

        found_vacancies = response.json()

        vacancy_salaries = [{"payment_from": vacancy["payment_from"],
                             "payment_to": vacancy["payment_to"],
                             "town": vacancy["town"]["title"]} for vacancy in found_vacancies["objects"]]

        sj_salaries["items"].extend(vacancy_salaries)
        sj_salaries["found"] = found_vacancies["total"]

        if found_vacancies["more"] is False:
            break
        page += 1

    return sj_salaries


def predict_rub_salary(salary_from, salary_to):
    """Считает среднюю зарплату по вакансии.

    Args:
        salary_from (int|None): Зарплата "от"
        salary_to (int|None): Зарплата "до"

    Returns:
        float: Средняя зарплата
    """
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        return salary_from * 1.2
    if salary_to:
        return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    """Считает среднуюю зарплату по вакансии сайта HH.

    Считается зарплата только для вакансий с рублями

    Args:
        vacancy (dict|None): Объект вакансии из HH.

    Returns:
        int|None: Средняя зарплата или None если в вакансии нет никаких данных о зарплате
    """
    if vacancy is None:
        return None
    if not vacancy.get("currency") == "RUR":
        return None
    return int(predict_rub_salary(vacancy.get("from"), vacancy.get("to")))


def predict_rub_salary_sj(vacancy):
    """Считает среднуюю зарплату по вакансии сайта SJ.

    Args:
        vacancy (dict|None): Объект вакансии из SJ.

    Returns:
        int|None: Средняя зарплата или None если в вакансии нет никаких данных о зарплате
    """
    if not vacancy["payment_from"] and not vacancy["payment_to"]:
        return None
    return int(predict_rub_salary(vacancy["payment_from"], vacancy["payment_to"]))


def print_beautiful_table(table_data, title):
    """Выводит красивую табличку зарплат по языкам программирования.

    Args:
        table_data (dict): Данные о языках и зарплатах.
                           {
                            'Go': {
                                   'vacancies_found': int,
                                   'vacancies_processed': int,
                                   'average_salary': int,
                                  },
                            'Python': {}...
                           }
        title (str): Заголовок для таблицы
    """
    data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]

    for language, values in table_data.items():
        data.append([language,
                     values['vacancies_found'],
                     values['vacancies_processed'],
                     values['average_salary']])
    table_instance = SingleTable(data, title)
    print(table_instance.table)


def get_vacancies_stat(salary_getter: Callable, predict_salary: Callable) -> dict:
    """Создает структуру данных о языке прграммирования.

    Сколько таких вакансий найдено, сколько имеют данные о зарплате, средняя ЗП по языку.

    Args:
        salary_getter: Функция для получения данных о вакансиях какого либо сайта
        predict_salary: Функция подсчета средней зарплаты вакансии с сайта
    """
    vacancy_statistics = defaultdict(dict)
    for language in LANGUAGES:
        salaries = salary_getter(language, period=30)
        valid_salaries = list(filter(None, map(predict_salary, salaries["items"])))

        vacancies_processed_count = len(valid_salaries)
        total_sum_salary = sum(valid_salaries)

        vacancy_statistics[language]["vacancies_found"] = salaries["found"]
        vacancy_statistics[language]["vacancies_processed"] = vacancies_processed_count

        if vacancies_processed_count > 0:
            vacancy_statistics[language]["average_salary"] = int(total_sum_salary / vacancies_processed_count)
        else:
            vacancy_statistics[language]["average_salary"] = 0

    return vacancy_statistics


def main():
    try:
        hh_stat = get_vacancies_stat(get_hh_salaries_by_language, predict_rub_salary_hh)
        print_beautiful_table(hh_stat, "HeadHunter Moscow")
    except HTTPError:
        print("При сборе статистики на сайте HH произошла ошибка!")

    try:
        sj_stat = get_vacancies_stat(get_sj_salaries_by_language, predict_rub_salary_sj)
        print_beautiful_table(sj_stat, "SuperJob Moscow")
    except HTTPError:
        print("При сборе статистики на сайте SJ произошла ошибка!")


if __name__ == '__main__':
    main()

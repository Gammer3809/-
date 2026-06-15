"""
Модуль универсальных утилит приложения «Анализ данных о клиентах банка».

Содержит вспомогательные функции общего назначения, используемые
во всех остальных модулях: чтение конфигурации, работа с файлами,
валидация данных, генерация тестовых данных.

Авторы: Садовский Арсений Валентинович, Старченко Денис Сергеевич,
        Черноморец Олег Сергеевич
"""

import os
import configparser
import pickle
import random
import pandas as pd


# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------

def load_config(config_path='config.ini'):
    """
    Загружает конфигурационный файл приложения.

    :param config_path: Путь к файлу конфигурации (по умолчанию 'config.ini').
    :type config_path: str
    :returns: Объект ConfigParser с параметрами приложения.
    :rtype: configparser.ConfigParser
    :author: Садовский Арсений Валентинович
    """
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    return config


def get_param(config, section, key, fallback=None):
    """
    Возвращает значение параметра конфигурации с безопасным fallback.

    :param config: Объект ConfigParser.
    :type config: configparser.ConfigParser
    :param section: Название секции конфигурации.
    :type section: str
    :param key: Ключ параметра.
    :type key: str
    :param fallback: Значение по умолчанию, если параметр не найден.
    :returns: Значение параметра или fallback.
    :author: Садовский Арсений Валентинович
    """
    return config.get(section, key, fallback=fallback)


# ---------------------------------------------------------------------------
# Работа с файлами
# ---------------------------------------------------------------------------

def save_dataframe(df, filepath):
    """
    Сохраняет DataFrame в двоичный файл формата pickle.

    :param df: Таблица данных для сохранения.
    :type df: pandas.DataFrame
    :param filepath: Путь к файлу назначения (расширение .pkl).
    :type filepath: str
    :returns: True при успехе, False при ошибке.
    :rtype: bool
    :author: Старченко Денис Сергеевич
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as fobj:
            pickle.dump(df, fobj)
        return True
    except (OSError, pickle.PicklingError) as err:
        print(f'Ошибка сохранения файла {filepath}: {err}')
        return False


def load_dataframe(filepath):
    """
    Загружает DataFrame из двоичного файла pickle.

    :param filepath: Путь к файлу .pkl.
    :type filepath: str
    :returns: Загруженный DataFrame или пустой DataFrame при ошибке.
    :rtype: pandas.DataFrame
    :author: Старченко Денис Сергеевич
    """
    try:
        with open(filepath, 'rb') as fobj:
            return pickle.load(fobj)
    except (OSError, pickle.UnpicklingError) as err:
        print(f'Ошибка загрузки файла {filepath}: {err}')
        return pd.DataFrame()


def save_text(filepath, content):
    """
    Сохраняет текстовое содержимое отчёта в файл .txt или .csv.

    :param filepath: Полный путь к файлу назначения.
    :type filepath: str
    :param content: Строковое содержимое для записи.
    :type content: str
    :returns: None
    :author: Садовский Арсений Валентинович
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as fobj:
        fobj.write(content)


def ensure_dirs(config):
    """
    Создаёт необходимые рабочие каталоги, если они отсутствуют.

    :param config: Объект ConfigParser с путями из секции [paths].
    :type config: configparser.ConfigParser
    :returns: None
    :author: Садовский Арсений Валентинович
    """
    for key in ('data_dir', 'output_dir', 'graphics_dir'):
        path = get_param(config, 'paths', key, key)
        os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# Словари нормализации CSV
# ---------------------------------------------------------------------------

JOB_MAP = {
    'admin.': 'Администратор',
    'unemployed': 'Безработный',
    'management': 'Управленец',
    'housemaid': 'Домработница',
    'entrepreneur': 'Предприниматель',
    'student': 'Студент',
    'blue-collar': 'Рабочий',
    'self-employed': 'Самозанятый',
    'retired': 'Пенсионер',
    'technician': 'Техник',
    'services': 'Сфера услуг',
    'unknown': 'Неизвестно',
}

MARITAL_MAP = {
    'married': 'Женат/Замужем',
    'divorced': 'Разведён/Разведена',
    'single': 'Холост/Не замужем',
}

EDUCATION_MAP = {
    'primary': 'Начальное',
    'secondary': 'Среднее',
    'tertiary': 'Высшее',
    'unknown': 'Неизвестно',
}

BINARY_MAP = {'yes': 'Да', 'no': 'Нет', 'unknown': 'Неизвестно'}

CONTACT_MAP = {
    'unknown': 'Неизвестно',
    'telephone': 'Телефон',
    'cellular': 'Мобильный',
}

POUTCOME_MAP = {
    'unknown': 'Неизвестно',
    'other': 'Другое',
    'failure': 'Неудача',
    'success': 'Успех',
}

MONTH_MAP = {
    'jan': 'Январь', 'feb': 'Февраль', 'mar': 'Март',
    'apr': 'Апрель', 'may': 'Май', 'jun': 'Июнь',
    'jul': 'Июль', 'aug': 'Август', 'sep': 'Сентябрь',
    'oct': 'Октябрь', 'nov': 'Ноябрь', 'dec': 'Декабрь',
}

# Допустимые значения для валидации
VALID_JOB = list(JOB_MAP.values())
VALID_MARITAL = list(MARITAL_MAP.values())
VALID_EDUCATION = list(EDUCATION_MAP.values())
VALID_BINARY = ['Да', 'Нет']


# ---------------------------------------------------------------------------
# Загрузка и нормализация исходного CSV
# ---------------------------------------------------------------------------

def load_source_csv(csv_path):
    """
    Загружает и нормализует исходный CSV-файл Bank Marketing Dataset.

    Переводит категориальные значения на русский язык,
    добавляет числовой идентификатор клиента (ID_клиента).

    :param csv_path: Путь к файлу bank-full.csv.
    :type csv_path: str
    :returns: DataFrame с нормализованными данными или None при ошибке.
    :rtype: pandas.DataFrame or None
    :author: Садовский Арсений Валентинович
    """
    try:
        df = pd.read_csv(csv_path, sep=';')
    except (OSError, pd.errors.ParserError) as err:
        print(f'Ошибка чтения CSV: {err}')
        return None

    df.rename(columns={
        'age': 'Возраст', 'job': 'Профессия',
        'marital': 'Семейное_положение', 'education': 'Образование',
        'default': 'Дефолт', 'balance': 'Баланс',
        'housing': 'Ипотека', 'loan': 'Кредит',
        'contact': 'Тип_связи', 'day': 'День', 'month': 'Месяц',
        'duration': 'Длительность', 'campaign': 'Кол_контактов',
        'pdays': 'Дней_после_контакта', 'previous': 'Предыдущих_контактов',
        'poutcome': 'Результат_кампании', 'y': 'Подписка',
    }, inplace=True)

    df['Профессия'] = df['Профессия'].map(JOB_MAP).fillna('Неизвестно')
    df['Семейное_положение'] = df['Семейное_положение'].map(MARITAL_MAP)
    df['Образование'] = df['Образование'].map(EDUCATION_MAP)
    df['Дефолт'] = df['Дефолт'].map(BINARY_MAP)
    df['Ипотека'] = df['Ипотека'].map(BINARY_MAP)
    df['Кредит'] = df['Кредит'].map(BINARY_MAP)
    df['Тип_связи'] = df['Тип_связи'].map(CONTACT_MAP)
    df['Месяц'] = df['Месяц'].map(MONTH_MAP)
    df['Результат_кампании'] = df['Результат_кампании'].map(POUTCOME_MAP)
    df['Подписка'] = df['Подписка'].map({'yes': 'Да', 'no': 'Нет'})
    df.insert(0, 'ID_клиента', range(1, len(df) + 1))

    return df


def split_to_handbooks(df):
    """
    Разделяет полный DataFrame на два нормализованных справочника (3НФ).

    Справочник 1 — социально-демографические характеристики.
    Справочник 2 — финансовое положение и кредитная история.

    :param df: Полный DataFrame с колонкой 'ID_клиента'.
    :type df: pandas.DataFrame
    :returns: Кортеж (df_clients, df_finance).
    :rtype: tuple[pandas.DataFrame, pandas.DataFrame]
    :author: Старченко Денис Сергеевич
    """
    df_clients = df[['ID_клиента', 'Возраст', 'Профессия',
                     'Семейное_положение', 'Образование']].copy()
    df_finance = df[['ID_клиента', 'Дефолт', 'Баланс',
                     'Ипотека', 'Кредит']].copy()
    return df_clients, df_finance


# ---------------------------------------------------------------------------
# Генерация синтетических тестовых данных
# ---------------------------------------------------------------------------

def create_sample_data(n=200):
    """
    Создаёт синтетические тестовые данные, если CSV и pkl-файлы отсутствуют.

    Возвращает два DataFrame в структуре, идентичной split_to_handbooks():
    справочник демографии и справочник финансов.

    :param n: Количество синтетических записей (по умолчанию 200).
    :type n: int
    :returns: Кортеж (df_clients, df_finance).
    :rtype: tuple[pandas.DataFrame, pandas.DataFrame]
    :author: Садовский Арсений Валентинович
    """
    random.seed(42)
    ids = list(range(1, n + 1))

    df_clients = pd.DataFrame({
        'ID_клиента': ids,
        'Возраст': [random.randint(18, 70) for _ in ids],
        'Профессия': [random.choice(VALID_JOB) for _ in ids],
        'Семейное_положение': [random.choice(VALID_MARITAL) for _ in ids],
        'Образование': [random.choice(VALID_EDUCATION) for _ in ids],
    })

    df_finance = pd.DataFrame({
        'ID_клиента': ids,
        'Дефолт': [random.choice(VALID_BINARY) for _ in ids],
        'Баланс': [random.randint(-500, 10000) for _ in ids],
        'Ипотека': [random.choice(VALID_BINARY) for _ in ids],
        'Кредит': [random.choice(VALID_BINARY) for _ in ids],
    })

    return df_clients, df_finance


# ---------------------------------------------------------------------------
# Валидация вводимых значений
# ---------------------------------------------------------------------------

def validate_age(value):
    """
    Проверяет корректность введённого возраста клиента.

    :param value: Строковое представление возраста.
    :type value: str
    :returns: True если значение валидно (целое число от 18 до 100).
    :rtype: bool
    :author: Старченко Денис Сергеевич
    """
    try:
        age = int(value)
        return 18 <= age <= 100
    except (ValueError, TypeError):
        return False


def validate_balance(value):
    """
    Проверяет корректность введённого значения баланса.

    :param value: Строковое представление баланса.
    :type value: str
    :returns: True если значение является целым числом.
    :rtype: bool
    :author: Старченко Денис Сергеевич
    """
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_choice(value, valid_list):
    """
    Проверяет, что значение входит в список допустимых.

    :param value: Проверяемое значение.
    :type value: str
    :param valid_list: Список допустимых значений.
    :type valid_list: list
    :returns: True если value содержится в valid_list.
    :rtype: bool
    :author: Старченко Денис Сергеевич
    """
    return value in valid_list

"""
Модуль построения аналитических отчётов приложения «Анализ данных о клиентах банка».

Реализует семь видов отчётов согласно техническому заданию:
1. Простой текстовый отчёт (проекция/сокращение).
2. Статистический текстовый отчёт.
3. Сводная таблица (pivot_table).
4. Кластеризованная столбчатая диаграмма.
5. Категоризированная гистограмма.
6. Категоризированная диаграмма Бокса-Вискера.
7. Категоризированная диаграмма рассеивания.

Авторы: Садовский Арсений Валентинович, Черноморец Олег Сергеевич
"""

import os
import numpy as np
import pandas as pd
import matplotlib
try:
    matplotlib.use('TkAgg')
except Exception:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Максимальное количество категорий для читаемого графика
_MAX_READABLE_CATS = 8
# Максимальное количество строк в текстовом отчёте
_MAX_TEXT_ROWS = 1000

# Палитра для графиков
VIBRANT_COLORS = [
    '#007BFF',
    '#E63946',
    '#2A9D8F',
    '#F4A261',
    '#7209B7',
    '#00B4D8',
    '#D90368',
    '#8AC926',
    '#FFBE0B',
    '#FB5607',
]


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _get_full_df(df_clients, df_finance):
    """
    Объединяет два справочника по ключу 'ID_клиента' (INNER JOIN).

    :param df_clients: Справочник социально-демографических данных.
    :type df_clients: pandas.DataFrame
    :param df_finance: Справочник финансовых данных.
    :type df_finance: pandas.DataFrame
    :returns: Объединённый DataFrame.
    :rtype: pandas.DataFrame
    :author: Садовский Арсений Валентинович
    """
    return pd.merge(df_clients, df_finance, on='ID_клиента', how='inner')


def _save_figure(fig, filepath):
    """
    Сохраняет объект Figure в файл .png или .pdf.

    :param fig: Объект фигуры matplotlib.
    :type fig: matplotlib.figure.Figure
    :param filepath: Полный путь к файлу назначения.
    :type filepath: str
    :returns: None
    :author: Черноморец Олег Сергеевич
    """
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    fig.savefig(filepath, bbox_inches='tight', dpi=150)


def _check_cat_count(series, name):
    """
    Проверяет количество уникальных категорий. Выводит предупреждение,
    если категорий больше _MAX_READABLE_CATS — график может быть нечитаемым.

    :param series: Серия с категориальными значениями.
    :type series: pandas.Series
    :param name: Название атрибута для сообщения.
    :type name: str
    :returns: Количество уникальных значений.
    :rtype: int
    :author: Садовский Арсений Валентинович
    """
    n = series.nunique()
    if n > _MAX_READABLE_CATS:
        print(
            f'Предупреждение: атрибут «{name}» содержит {n} уникальных значений '
            f'(рекомендуется не более {_MAX_READABLE_CATS}). '
            f'График может быть нечитаемым.'
        )
    return n


# ---------------------------------------------------------------------------
# Отчёт 1: Простой текстовый отчёт
# ---------------------------------------------------------------------------

def report_simple(df_clients, df_finance, columns, filters=None):
    """
    Формирует простой текстовый отчёт: выбор столбцов и фильтрация строк.

    Объединяет справочники через merge, применяет проекцию (выбор столбцов)
    и сокращение (фильтрацию строк). Выводит не более 1000 строк.

    :param df_clients: Справочник социально-демографических данных.
    :type df_clients: pandas.DataFrame
    :param df_finance: Справочник финансовых данных.
    :type df_finance: pandas.DataFrame
    :param columns: Список выбираемых столбцов.
    :type columns: list[str]
    :param filters: Словарь {столбец: значение} для фильтрации строк.
    :type filters: dict or None
    :returns: Отформатированная строка с таблицей результатов.
    :rtype: str
    :author: Садовский Арсений Валентинович
    """
    df = _get_full_df(df_clients, df_finance)

    # Сокращение строк по фильтрам
    if filters:
        for col, val in filters.items():
            if col in df.columns and val:
                df = df[df[col] == val]

    # Проекция столбцов
    available = [c for c in columns if c in df.columns]
    if not available:
        available = df.columns.tolist()
    df = df[available].reset_index(drop=True)

    total = len(df)
    display_df = df.head(_MAX_TEXT_ROWS)
    result = (f'Записей найдено: {total} '
              f'(показаны первые {min(_MAX_TEXT_ROWS, total)})\n\n')
    result += display_df.to_string(index=False)
    return result


# ---------------------------------------------------------------------------
# Отчёт 2: Статистический текстовый отчёт
# ---------------------------------------------------------------------------

def report_statistics(df_clients, df_finance, columns):
    """
    Формирует статистический отчёт по выбранным атрибутам.

    Для качественных переменных строит таблицу частот.
    Для количественных — описательные статистики методами pandas.DataFrame.

    :param df_clients: Справочник социально-демографических данных.
    :type df_clients: pandas.DataFrame
    :param df_finance: Справочник финансовых данных.
    :type df_finance: pandas.DataFrame
    :param columns: Список атрибутов для анализа.
    :type columns: list[str]
    :returns: Строковый отчёт со статистиками.
    :rtype: str
    :author: Садовский Арсений Валентинович
    """
    df = _get_full_df(df_clients, df_finance)
    result = ''

    for col in columns:
        if col not in df.columns:
            continue
        result += f'{"=" * 60}\n'
        result += f'Атрибут: {col}\n'
        result += f'{"=" * 60}\n'
        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            stats = pd.DataFrame({
                'Показатель': ['Минимум', 'Максимум', 'Среднее',
                               'Дисперсия', 'Стандартное отклонение'],
                'Значение': [
                    series.min(), series.max(),
                    round(series.mean(), 2),
                    round(series.var(), 2),
                    round(series.std(), 2),
                ]
            })
            result += stats.to_string(index=False) + '\n\n'
        else:
            freq = series.value_counts().reset_index()
            freq.columns = ['Значение', 'Частота']
            freq['Процент'] = (freq['Частота'] / len(series) * 100).round(2)
            freq['Процент'] = freq['Процент'].astype(str) + '%'
            result += freq.to_string(index=False) + '\n\n'

    return result if result else 'Не выбраны атрибуты для анализа.'


# ---------------------------------------------------------------------------
# Отчёт 3: Сводная таблица
# ---------------------------------------------------------------------------

def report_pivot(df_clients, df_finance, index_col, columns_col,
                 values_col, aggfunc='count'):
    """
    Строит сводную таблицу для пары атрибутов с помощью pandas.pivot_table().

    :param df_clients: Справочник социально-демографических данных.
    :type df_clients: pandas.DataFrame
    :param df_finance: Справочник финансовых данных.
    :type df_finance: pandas.DataFrame
    :param index_col: Атрибут для строк сводной таблицы.
    :type index_col: str
    :param columns_col: Атрибут для столбцов сводной таблицы.
    :type columns_col: str
    :param values_col: Атрибут для вычисления значений.
    :type values_col: str
    :param aggfunc: Функция агрегации ('count', 'mean', 'sum', 'min', 'max').
    :type aggfunc: str
    :returns: Строковое представление сводной таблицы.
    :rtype: str
    :author: Садовский Арсений Валентинович
    """
    df = _get_full_df(df_clients, df_finance)
    agg_map = {
        'count': 'count', 'mean': np.mean,
        'sum': np.sum, 'min': np.min, 'max': np.max,
    }
    agg_fn = agg_map.get(aggfunc, 'count')

    try:
        pivot = pd.pivot_table(
            df, index=index_col, columns=columns_col,
            values=values_col, aggfunc=agg_fn, fill_value=0,
        )
        result = (f'Сводная таблица: {index_col} × {columns_col}\n'
                  f'Значения: {values_col}, Агрегация: {aggfunc}\n\n')
        result += pivot.to_string() + '\n'
    except Exception as err:  # pylint: disable=broad-except
        result = f'Ошибка построения сводной таблицы: {err}'

    return result


# ---------------------------------------------------------------------------
# Отчёт 4: Кластеризованная столбчатая диаграмма
# ---------------------------------------------------------------------------

def report_bar_chart(df_clients, df_finance, cat1, cat2, save_path=None):
    """
    Строит кластеризованную столбчатую диаграмму для пары качественных атрибутов.

    При количестве категорий > 8 автоматически уменьшает шрифт и поворачивает
    подписи, высота фигуры увеличивается пропорционально числу категорий.
    Использует matplotlib.pyplot.bar().

    :param df_clients: Справочник социально-демографических данных.
    :type df_clients: pandas.DataFrame
    :param df_finance: Справочник финансовых данных.
    :type df_finance: pandas.DataFrame
    :param cat1: Первый качественный атрибут (ось X).
    :type cat1: str
    :param cat2: Второй качественный атрибут (группировка).
    :type cat2: str
    :param save_path: Путь для сохранения изображения (None — без сохранения).
    :type save_path: str or None
    :returns: Объект Figure.
    :rtype: matplotlib.figure.Figure
    :author: Черноморец Олег Сергеевич
    """
    df = _get_full_df(df_clients, df_finance)
    n_cats = _check_cat_count(df[cat1], cat1)

    counts = df.groupby([cat1, cat2]).size().unstack(fill_value=0)
    x_labels = counts.index.tolist()
    x_pos = np.arange(len(x_labels))
    groups = counts.columns.tolist()
    n_groups = len(groups)
    width = 0.8 / n_groups

    # Высота пропорциональна числу категорий при их большом количестве
    fig_h = max(6, n_cats * 0.5)
    fig, axes = plt.subplots(figsize=(max(12, n_cats * 0.8), fig_h))
    colors = VIBRANT_COLORS  # pylint: disable=no-member

    for i, group in enumerate(groups):
        offset = (i - n_groups / 2 + 0.5) * width
        axes.bar(
            x_pos + offset, counts[group], width=width,
            label=str(group), color=colors[i % len(colors)],
            alpha=0.9, edgecolor='white',
        )

    # Уменьшаем шрифт и поворачиваем подписи при большом числе категорий
    tick_fs = 9 if n_cats <= _MAX_READABLE_CATS else 7
    plt.xticks(x_pos, x_labels, rotation=45, ha='right', fontsize=tick_fs)
    axes.set_xlabel(cat1, fontsize=11)
    axes.set_ylabel('Количество клиентов', fontsize=11)
    axes.set_title(f'Распределение «{cat2}» по «{cat1}»', fontsize=13, pad=15)
    axes.legend(title=cat2, bbox_to_anchor=(1.01, 1), loc='upper left')
    axes.grid(axis='y', alpha=0.4)
    fig.tight_layout()

    if save_path:
        _save_figure(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# Отчёт 5: Категоризированная гистограмма
# ---------------------------------------------------------------------------

def report_histogram(df_clients, df_finance, num_col, cat_col,
                     bins=20, save_path=None):
    """
    Строит категоризированную гистограмму для пары «количественный–качественный».

    При количестве категорий > 8 выводит предупреждение и уменьшает шрифт
    подписей легенды. Использует matplotlib.pyplot.hist().

    :param df_clients: Справочник социально-демографических данных.
    :type df_clients: pandas.DataFrame
    :param df_finance: Справочник финансовых данных.
    :type df_finance: pandas.DataFrame
    :param num_col: Количественный атрибут (ось X).
    :type num_col: str
    :param cat_col: Качественный атрибут (группировка цветом).
    :type cat_col: str
    :param bins: Количество интервалов гистограммы.
    :type bins: int
    :param save_path: Путь для сохранения изображения.
    :type save_path: str or None
    :returns: Объект Figure.
    :rtype: matplotlib.figure.Figure
    :author: Черноморец Олег Сергеевич
    """
    df = _get_full_df(df_clients, df_finance)
    categories = df[cat_col].unique()
    n_cats = _check_cat_count(df[cat_col], cat_col)
    colors = VIBRANT_COLORS  # pylint: disable=no-member

    fig, axes = plt.subplots(figsize=(11, 6))
    for i, cat in enumerate(categories):
        subset = df.loc[df[cat_col] == cat, num_col].dropna()
        axes.hist(subset, bins=bins, alpha=0.9, label=str(cat),
                  color=colors[i % len(colors)], edgecolor='white')

    axes.set_xlabel(num_col, fontsize=11)
    axes.set_ylabel('Количество клиентов', fontsize=11)
    axes.set_title(f'Гистограмма «{num_col}» по группам «{cat_col}»',
                   fontsize=13, pad=15)
    legend_fs = 9 if n_cats <= _MAX_READABLE_CATS else 7
    axes.legend(title=cat_col, bbox_to_anchor=(1.01, 1),
                loc='upper left', fontsize=legend_fs)
    axes.grid(axis='y', alpha=0.4)
    fig.tight_layout()

    if save_path:
        _save_figure(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# Отчёт 6: Диаграмма Бокса-Вискера
# ---------------------------------------------------------------------------

def report_boxplot(df_clients, df_finance, num_col, cat_col, save_path=None):
    """
    Строит категоризированную диаграмму Бокса-Вискера.

    При количестве категорий > 8 уменьшает шрифт подписей оси X.
    Использует matplotlib.pyplot.boxplot().

    :param df_clients: Справочник социально-демографических данных.
    :type df_clients: pandas.DataFrame
    :param df_finance: Справочник финансовых данных.
    :type df_finance: pandas.DataFrame
    :param num_col: Количественный атрибут.
    :type num_col: str
    :param cat_col: Качественный атрибут (группировка).
    :type cat_col: str
    :param save_path: Путь для сохранения изображения.
    :type save_path: str or None
    :returns: Объект Figure.
    :rtype: matplotlib.figure.Figure
    :author: Черноморец Олег Сергеевич
    """
    df = _get_full_df(df_clients, df_finance)
    categories = sorted(df[cat_col].dropna().unique())
    n_cats = _check_cat_count(df[cat_col], cat_col)

    data_groups = [
        df.loc[df[cat_col] == cat, num_col].dropna().values
        for cat in categories
    ]

    fig, axes = plt.subplots(figsize=(max(10, len(categories) * 1.5), 6))
    bp = axes.boxplot(data_groups, label=categories,
                      patch_artist=True, notch=False, vert=True)

    colors = VIBRANT_COLORS  # pylint: disable=no-member
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.9)

    axes.set_xlabel(cat_col, fontsize=11)
    axes.set_ylabel(num_col, fontsize=11)
    axes.set_title(f'Диаграмма Бокса-Вискера: «{num_col}» по «{cat_col}»',
                   fontsize=13, pad=15)
    tick_fs = 9 if n_cats <= _MAX_READABLE_CATS else 7
    axes.tick_params(axis='x', rotation=45, labelsize=tick_fs)
    axes.grid(axis='y', alpha=0.4)
    fig.tight_layout()

    if save_path:
        _save_figure(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# Отчёт 7: Диаграмма рассеивания
# ---------------------------------------------------------------------------

def report_scatter(df_clients, df_finance, num_col1, num_col2, cat_col,
                   save_path=None):
    """
    Строит категоризированную диаграмму рассеивания для двух количественных
    и одного качественного атрибута.

    При количестве категорий > 8 уменьшает шрифт легенды.
    Использует matplotlib.pyplot.scatter().

    :param df_clients: Справочник социально-демографических данных.
    :type df_clients: pandas.DataFrame
    :param df_finance: Справочник финансовых данных.
    :type df_finance: pandas.DataFrame
    :param num_col1: Первый количественный атрибут (ось X).
    :type num_col1: str
    :param num_col2: Второй количественный атрибут (ось Y).
    :type num_col2: str
    :param cat_col: Качественный атрибут (цвет точек).
    :type cat_col: str
    :param save_path: Путь для сохранения изображения.
    :type save_path: str or None
    :returns: Объект Figure.
    :rtype: matplotlib.figure.Figure
    :author: Черноморец Олег Сергеевич
    """
    df = _get_full_df(df_clients, df_finance)
    categories = df[cat_col].unique()
    n_cats = _check_cat_count(df[cat_col], cat_col)
    colors = VIBRANT_COLORS  # pylint: disable=no-member

    fig, axes = plt.subplots(figsize=(11, 7))
    for i, cat in enumerate(categories):
        subset = df[df[cat_col] == cat]
        if len(subset) > 2000:
            subset = subset.sample(2000, random_state=42)
        axes.scatter(
            subset[num_col1], subset[num_col2],
            label=str(cat), color=colors[i % len(colors)],
            alpha=0.9, s=15, edgecolors='none',
        )

    axes.set_xlabel(num_col1, fontsize=11)
    axes.set_ylabel(num_col2, fontsize=11)
    axes.set_title(
        f'Диаграмма рассеивания: «{num_col1}» — «{num_col2}» по «{cat_col}»',
        fontsize=13, pad=15,
    )
    legend_fs = 9 if n_cats <= _MAX_READABLE_CATS else 7
    axes.legend(title=cat_col, bbox_to_anchor=(1.01, 1),
                loc='upper left', fontsize=legend_fs)
    axes.grid(alpha=0.3)
    fig.tight_layout()

    if save_path:
        _save_figure(fig, save_path)
    return fig

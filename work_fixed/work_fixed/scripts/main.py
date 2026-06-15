"""
Главный модуль приложения «Анализ данных о клиентах банка».

Реализует графический интерфейс на базе Tkinter для работы
со справочниками клиентов и построения аналитических отчётов.

Запуск: python scripts/main.py
(из корневого каталога work)

Авторы: Черноморец Олег Сергеевич, Садовский Арсений Валентинович,
        Старченко Денис Сергеевич
Группа: БИВ255
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

# Добавление корневого каталога work в пути поиска модулей
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import library.utils as utils   # noqa: E402
import scripts.reports as rpt   # noqa: E402

# ---------------------------------------------------------------------------
# Глобальные переменные (состояние приложения)
# ---------------------------------------------------------------------------
CONFIG = utils.load_config(os.path.join(ROOT_DIR, 'config.ini'))
DF_CLIENTS = pd.DataFrame()   # Справочник 1 — демография
DF_FINANCE = pd.DataFrame()   # Справочник 2 — финансы


# ---------------------------------------------------------------------------
# Пути к pkl-файлам справочников
# ---------------------------------------------------------------------------

def _clients_path():
    """
    Возвращает абсолютный путь к файлу справочника демографии.

    :returns: Путь к clients.pkl.
    :rtype: str
    :author: Садовский Арсений Валентинович
    """
    return os.path.join(
        ROOT_DIR, utils.get_param(CONFIG, 'paths', 'clients_file', 'data/clients.pkl'))


def _finance_path():
    """
    Возвращает абсолютный путь к файлу справочника финансов.

    :returns: Путь к finance.pkl.
    :rtype: str
    :author: Садовский Арсений Валентинович
    """
    return os.path.join(
        ROOT_DIR, utils.get_param(CONFIG, 'paths', 'finance_file', 'data/finance.pkl'))


# ---------------------------------------------------------------------------
# Вспомогательные функции GUI
# ---------------------------------------------------------------------------

def _make_label(parent, text, font_size=11, bold=False, **kwargs):
    """
    Создаёт метку с заданными параметрами шрифта и цветовой схемой из config.

    :param parent: Родительский виджет.
    :param text: Текст метки.
    :type text: str
    :param font_size: Размер шрифта в пунктах.
    :type font_size: int
    :param bold: Жирное начертание.
    :type bold: bool
    :returns: Объект Label.
    :rtype: tk.Label
    :author: Черноморец Олег Сергеевич
    """
    family = utils.get_param(CONFIG, 'interface', 'font_family', 'Calibri')
    weight = 'bold' if bold else 'normal'
    # kwargs могут переопределять bg/fg — убираем дубли
    bg = kwargs.pop('bg', utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD'))
    fg = kwargs.pop('fg', utils.get_param(CONFIG, 'interface', 'fg_color', '#002B5B'))
    return tk.Label(
        parent, text=text,
        font=(family, font_size, weight),
        bg=bg,
        fg=fg,
        **kwargs,
    )


def _make_button(parent, text, command, width=22):
    """
    Создаёт кнопку в стиле приложения с красивым оформлением.

    :param parent: Родительский виджет.
    :param text: Надпись на кнопке.
    :type text: str
    :param command: Функция-обработчик нажатия.
    :type command: callable
    :param width: Ширина кнопки в символах.
    :type width: int
    :returns: Объект Button.
    :rtype: tk.Button
    :author: Черноморец Олег Сергеевич
    """
    family = utils.get_param(CONFIG, 'interface', 'font_family', 'Calibri')
    btn = tk.Button(
        parent, text=text, command=command, width=width,
        bg='#007BFF', fg='#FFFFFF', font=(family, 12, 'bold'),
        relief='flat', cursor='hand2',
        activebackground='#0056B3', activeforeground='#FFFFFF',
        bd=0, padx=14, pady=10,
        highlightthickness=0,
    )
    def on_enter(e):
        btn.config(bg='#0056B3', relief='flat')
    def on_leave(e):
        btn.config(bg='#007BFF', relief='flat')
    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)
    return btn


def _style_treeview():
    """Настраивает стиль Treeview: заголовки и строки."""
    style = ttk.Style()
    style.theme_use('default')
    style.configure('Treeview',
                    background='#FFFFFF',
                    foreground='#002B5B',
                    rowheight=26,
                    fieldbackground='#FFFFFF',
                    font=('Calibri', 10))
    style.configure('Treeview.Heading',
                    background='#007BFF',
                    foreground='#FFFFFF',
                    font=('Calibri', 10, 'bold'),
                    relief='flat')
    style.map('Treeview',
              background=[('selected', '#007BFF')],
              foreground=[('selected', '#FFFFFF')])
    style.map('Treeview.Heading',
              background=[('active', '#0056B3')])


def _make_combobox(parent, values, width=24):
    """
    Создаёт выпадающий список (readonly) с заданными значениями.

    :param parent: Родительский виджет.
    :param values: Список допустимых значений.
    :type values: list
    :param width: Ширина виджета в символах.
    :type width: int
    :returns: Объект ttk.Combobox.
    :rtype: ttk.Combobox
    :author: Черноморец Олег Сергеевич
    """
    style = ttk.Style()
    style.theme_use('default')
    style.configure('TCombobox', fieldbackground='#FFFFFF', foreground='#002B5B',
                    padding=6, relief='solid', borderwidth=2)
    cb = ttk.Combobox(parent, values=values, width=width, state='readonly',
                      font=('Calibri', 11, 'bold'), style='TCombobox')
    if values:
        cb.current(0)
    return cb


def _show_df_in_tree(tree, df, max_rows=500):
    """
    Отображает DataFrame в виджете Treeview с динамической шириной колонок.

    Ширина каждого столбца вычисляется на основе максимальной длины
    содержимого (не менее 60 пикс.).

    :param tree: Виджет ttk.Treeview для отображения.
    :type tree: ttk.Treeview
    :param df: Таблица данных.
    :type df: pandas.DataFrame
    :param max_rows: Максимальное количество отображаемых строк.
    :type max_rows: int
    :returns: None
    :author: Черноморец Олег Сергеевич
    """
    try:
        tree.delete(*tree.get_children())
        if df.empty:
            return

        tree['columns'] = list(df.columns)
        tree['show'] = 'headings'

        display = df.head(max_rows)
        for col in df.columns:
            # Динамическая ширина: максимум из заголовка и значений
            col_vals = display[col].astype(str).tolist() + [str(col)]
            col_w = max(len(v) for v in col_vals) * 8 + 20
            col_w = max(col_w, 80)
            tree.heading(col, text=col)
            tree.column(col, width=col_w, anchor='center')

        for _, row in display.iterrows():
            tree.insert('', 'end', values=list(row))
    except Exception as err:
        print(f"Ошибка при отображении таблицы: {err}")


# ---------------------------------------------------------------------------
# Диалог справочника (CRUD)
# ---------------------------------------------------------------------------

def _open_handbook_window(title, df_getter, df_setter, auto_save_fn,
                          columns_meta):
    """
    Открывает окно для работы со справочником: просмотр, добавление,
    редактирование, удаление записей с автосохранением после каждой операции.

    Изменения немедленно записываются в глобальную переменную и pkl-файл,
    поэтому отчёты всегда используют актуальные данные.

    :param title: Заголовок окна.
    :type title: str
    :param df_getter: Функция, возвращающая текущий DataFrame (без аргументов).
    :type df_getter: callable
    :param df_setter: Функция для обновления глобального DataFrame (принимает df).
    :type df_setter: callable
    :param auto_save_fn: Функция автосохранения df в pkl (без аргументов).
    :type auto_save_fn: callable
    :param columns_meta: Список словарей {'name', 'type', 'values'}.
    :type columns_meta: list[dict]
    :returns: None
    :author: Старченко Денис Сергеевич
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry('1100x680')
    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    win.configure(bg=bg)

    # — Таблица —
    frame_tree = tk.Frame(win, bg=bg)
    frame_tree.pack(fill='both', expand=True, padx=10, pady=5)

    scroll_y = tk.Scrollbar(frame_tree, orient='vertical')
    scroll_x = tk.Scrollbar(frame_tree, orient='horizontal')
    tree = ttk.Treeview(
        frame_tree,
        yscrollcommand=scroll_y.set,
        xscrollcommand=scroll_x.set,
        height=20,
    )
    scroll_y.config(command=tree.yview)
    scroll_x.config(command=tree.xview)
    scroll_y.pack(side='right', fill='y')
    scroll_x.pack(side='bottom', fill='x')
    tree.pack(fill='both', expand=True)

    def refresh():
        """Обновляет отображение таблицы из текущего глобального DataFrame."""
        _show_df_in_tree(tree, df_getter())

    refresh()

    # — Форма добавления/редактирования —
    frame_form = tk.LabelFrame(win, text=' ✏️ Редактирование записи ', bg=bg, pady=8,
                              font=('Calibri', 11, 'bold'), fg='#007BFF', padx=15,
                              relief='groove', bd=2)
    frame_form.pack(fill='x', padx=12, pady=8)

    entries = {}
    for i, meta in enumerate(columns_meta):
        if meta['name'] == 'ID_клиента':
            continue
        tk.Label(frame_form, text=meta['name'] + ':', bg=bg, fg='#002B5B',
                 font=('Calibri', 11, 'bold')).grid(row=0, column=i * 2,
                                            padx=8, pady=6, sticky='e')
        if meta['type'] == 'choice':
            widget = _make_combobox(frame_form, meta['values'], width=16)
        else:
            widget = tk.Entry(frame_form, width=12, font=('Calibri', 11),
                            relief='solid', bd=2)
        widget.grid(row=0, column=i * 2 + 1, padx=8, pady=6)
        entries[meta['name']] = widget

    def _fill_form(event=None):
        """Заполняет форму значениями строки, выбранной в таблице."""
        sel = tree.selection()
        if not sel:
            return
        values = tree.item(sel[0])['values']
        cols = df_getter().columns.tolist()
        for j, col in enumerate(cols):
            if col in entries:
                widget = entries[col]
                if isinstance(widget, ttk.Combobox):
                    widget.set(str(values[j]))
                else:
                    widget.delete(0, 'end')
                    widget.insert(0, str(values[j]))

    tree.bind('<<TreeviewSelect>>', _fill_form)

    def _get_form_values():
        """
        Считывает и возвращает значения из формы в виде словаря.

        :returns: Словарь {имя_поля: значение}.
        :rtype: dict
        :author: Старченко Денис Сергеевич
        """
        vals = {}
        for col, widget in entries.items():
            vals[col] = (widget.get() if isinstance(widget, ttk.Combobox)
                         else widget.get().strip())
        return vals

    def _validate_form(vals):
        """
        Проверяет значения формы на соответствие ограничениям.

        Используется как при добавлении, так и при редактировании записей.

        :param vals: Словарь значений из формы.
        :type vals: dict
        :returns: True если все значения валидны, иначе False.
        :rtype: bool
        :author: Старченко Денис Сергеевич
        """
        for meta in columns_meta:
            if meta['name'] == 'ID_клиента':
                continue
            val = vals.get(meta['name'], '')
            if meta['type'] == 'age':
                if not utils.validate_age(val):
                    messagebox.showerror(
                        'Ошибка ввода',
                        'Возраст должен быть целым числом от 18 до 100.',
                        parent=win,
                    )
                    return False
            elif meta['type'] == 'int':
                if not utils.validate_balance(val):
                    messagebox.showerror(
                        'Ошибка ввода',
                        f'Поле «{meta["name"]}» должно быть целым числом.',
                        parent=win,
                    )
                    return False
            elif meta['type'] == 'choice':
                if not utils.validate_choice(val, meta['values']):
                    messagebox.showerror(
                        'Ошибка ввода',
                        f'Недопустимое значение для «{meta["name"]}».',
                        parent=win,
                    )
                    return False
        return True

    def _add_record():
        """
        Добавляет новую запись в справочник после валидации.

        После успешного добавления обновляет глобальный DataFrame
        и автоматически сохраняет pkl-файл.

        :returns: None
        :author: Старченко Денис Сергеевич
        """
        vals = _get_form_values()
        if not _validate_form(vals):
            return

        df = df_getter()
        new_id = int(df['ID_клиента'].max() + 1) if not df.empty else 1
        new_row = {'ID_клиента': new_id}
        for meta in columns_meta:
            if meta['name'] == 'ID_клиента':
                continue
            raw = vals[meta['name']]
            new_row[meta['name']] = (int(raw) if meta['type'] in ('int', 'age')
                                     else raw)

        updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df_setter(updated)
        auto_save_fn()
        refresh()

    def _edit_record():
        """
        Обновляет выбранную запись значениями из формы (с валидацией).

        После успешного редактирования обновляет глобальный DataFrame
        и автоматически сохраняет pkl-файл.

        :returns: None
        :author: Старченко Денис Сергеевич
        """
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Внимание',
                                   'Выберите запись для редактирования.',
                                   parent=win)
            return

        vals = _get_form_values()
        if not _validate_form(vals):
            return

        idx_val = tree.item(sel[0])['values'][0]  # ID_клиента
        df = df_getter().copy()
        for meta in columns_meta:
            col = meta['name']
            if col == 'ID_клиента':
                continue
            raw = vals[col]
            cast = (int(raw) if meta['type'] in ('int', 'age')
                    and str(raw).lstrip('-').isdigit() else raw)
            df.loc[df['ID_клиента'] == idx_val, col] = cast

        df_setter(df)
        auto_save_fn()
        refresh()

    def _delete_record():
        """
        Удаляет выбранную запись из справочника после подтверждения.

        После удаления обновляет глобальный DataFrame (с reset_index),
        автоматически сохраняет pkl-файл.

        :returns: None
        :author: Старченко Денис Сергеевич
        """
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Внимание',
                                   'Выберите запись для удаления.',
                                   parent=win)
            return
        idx_val = tree.item(sel[0])['values'][0]
        if messagebox.askyesno('Подтверждение',
                               f'Удалить запись ID={idx_val}?', parent=win):
            df = df_getter()
            updated = (df[df['ID_клиента'] != idx_val]
                       .reset_index(drop=True))
            df_setter(updated)
            auto_save_fn()
            refresh()

    def _manual_save():
        """
        Явное сохранение справочника в pkl-файл (дублирует автосохранение).

        :returns: None
        :author: Старченко Денис Сергеевич
        """
        auto_save_fn()
        messagebox.showinfo('Сохранение', 'Справочник сохранён.', parent=win)

    def _load_from_file():
        """
        Загружает справочник из выбранного pkl-файла, обновляя глобальный DataFrame.

        :returns: None
        :author: Старченко Денис Сергеевич
        """
        path = filedialog.askopenfilename(
            parent=win,
            filetypes=[('Pickle files', '*.pkl')],
            title='Выберите файл справочника',
        )
        if path:
            loaded = utils.load_dataframe(path)
            if not loaded.empty:
                df_setter(loaded)
                refresh()

    # — Кнопки управления —
    frame_btns = tk.Frame(win, bg=bg)
    frame_btns.pack(pady=10)
    for label, cmd in [
        ('➕ Добавить', _add_record),
        ('✏️ Изменить', _edit_record),
        ('🗑️ Удалить', _delete_record),
        ('💾 Сохранить', _manual_save),
        ('📂 Загрузить', _load_from_file),
    ]:
        _make_button(frame_btns, label, cmd, width=15).pack(side='left', padx=6)


# ---------------------------------------------------------------------------
# Окна отчётов
# ---------------------------------------------------------------------------

def _output_text_window(title, content):
    """
    Открывает окно для отображения текстового отчёта с возможностью сохранения.

    Сохранение выполняется через utils.save_text().

    :param title: Заголовок окна.
    :type title: str
    :param content: Текстовое содержимое отчёта.
    :type content: str
    :returns: None
    :author: Черноморец Олег Сергеевич
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry('950x650')
    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    win.configure(bg=bg)

    txt = tk.Text(win, font=('Courier New', 11), wrap='none',
                  bg='#FFFFFF', fg='#002B5B', relief='solid', bd=2)
    sy = tk.Scrollbar(win, orient='vertical', command=txt.yview)
    sx = tk.Scrollbar(win, orient='horizontal', command=txt.xview)
    txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    sy.pack(side='right', fill='y')
    sx.pack(side='bottom', fill='x')
    txt.pack(fill='both', expand=True, padx=5, pady=5)
    txt.insert('end', content)
    txt.configure(state='disabled')

    out_dir = utils.get_param(CONFIG, 'paths', 'output_dir', 'output')
    ext = utils.get_param(CONFIG, 'export', 'text_format', 'txt')

    def _save():
        """Сохраняет содержимое текстового отчёта в файл через utils.save_text."""
        path = filedialog.asksaveasfilename(
            parent=win,
            initialdir=out_dir,
            defaultextension=f'.{ext}',
            filetypes=[('Text', '*.txt'), ('CSV', '*.csv')],
        )
        if path:
            utils.save_text(path, content)
            messagebox.showinfo('Сохранено', f'Файл сохранён:\n{path}',
                                parent=win)

    btn_frame = tk.Frame(win, bg=bg)
    btn_frame.pack(pady=10)
    _make_button(btn_frame, '💾 Сохранить отчёт', _save, width=26).pack()


# ---------------------------------------------------------------------------
# Диалоги семи отчётов
# ---------------------------------------------------------------------------

def _open_report1():
    """
    Открывает диалог простого текстового отчёта (проекция + сокращение).

    :returns: None
    :author: Садовский Арсений Валентинович
    """
    if DF_CLIENTS.empty or DF_FINANCE.empty:
        messagebox.showwarning('Нет данных', 'Сначала загрузите данные.')
        return

    all_cols = list(DF_CLIENTS.columns) + [
        c for c in DF_FINANCE.columns if c != 'ID_клиента'
    ]
    win = tk.Toplevel()
    win.title('Отчёт 1 — Простой текстовый отчёт')
    win.geometry('750x550')
    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    win.configure(bg=bg)

    _make_label(win, 'Выберите столбцы для отображения:', bold=True, font_size=12).pack(
        pady=(15, 8))

    frame_cols = tk.Frame(win, bg=bg)
    frame_cols.pack(padx=20, fill='x')

    col_vars = {}
    for i, col in enumerate(all_cols):
        var = tk.BooleanVar(value=True)
        col_vars[col] = var
        chk = tk.Checkbutton(frame_cols, text=col, variable=var,
                       bg=bg, fg='#002B5B', font=('Calibri', 10),
                       selectcolor=bg, activebackground=bg, activeforeground='#007BFF')
        chk.grid(row=i // 4, column=i % 4, sticky='w', padx=8, pady=4)

    _make_label(win, 'Фильтр (необязательно):', bold=True, font_size=12).pack(pady=(15, 8))
    frame_filter = tk.Frame(win, bg=bg)
    frame_filter.pack(pady=5)

    # Только строковые столбцы для фильтрации
    merged = pd.merge(DF_CLIENTS, DF_FINANCE, on='ID_клиента', how='inner')
    cat_cols = [c for c in merged.columns
                if not pd.api.types.is_numeric_dtype(merged[c])]

    tk.Label(frame_filter, text='Столбец:', bg=bg,
             font=('Calibri', 11, 'bold'), fg='#002B5B').pack(side='left', padx=8)
    cb_filter_col = _make_combobox(frame_filter, ['(нет)'] + cat_cols, width=22)
    cb_filter_col.pack(side='left', padx=5)

    tk.Label(frame_filter, text='Значение:', bg=bg,
             font=('Calibri', 11, 'bold'), fg='#002B5B').pack(side='left', padx=8)
    entry_filter_val = tk.Entry(frame_filter, width=20, font=('Calibri', 11),
                               relief='solid', bd=2)
    entry_filter_val.pack(side='left', padx=5)

    def _run():
        """Формирует и отображает отчёт по выбранным параметрам."""
        try:
            selected = [c for c, v in col_vars.items() if v.get()]
            fil_col = cb_filter_col.get()
            fil_val = entry_filter_val.get().strip()
            filters = ({fil_col: fil_val}
                       if fil_col != '(нет)' and fil_val else None)
            content = rpt.report_simple(DF_CLIENTS, DF_FINANCE, selected, filters)
            _output_text_window('Результат — Отчёт 1', content)
        except Exception as err:
            messagebox.showerror('Ошибка', f'Ошибка формирования отчёта:\n{err}', parent=win)

    btn_frame = tk.Frame(win, bg=bg)
    btn_frame.pack(pady=20)
    _make_button(btn_frame, '📋 Сформировать отчёт', _run, width=26).pack()


def _open_report2():
    """
    Открывает диалог статистического текстового отчёта.

    :returns: None
    :author: Садовский Арсений Валентинович
    """
    if DF_CLIENTS.empty or DF_FINANCE.empty:
        messagebox.showwarning('Нет данных', 'Сначала загрузите данные.')
        return

    all_cols = (list(DF_CLIENTS.columns) +
                [c for c in DF_FINANCE.columns if c != 'ID_клиента'])
    win = tk.Toplevel()
    win.title('Отчёт 2 — Статистический отчёт')
    win.geometry('650x500')
    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    win.configure(bg=bg)

    _make_label(win, 'Выберите атрибуты для статистики:', bold=True, font_size=12).pack(
        pady=15)
    frame_cols = tk.Frame(win, bg=bg)
    frame_cols.pack(padx=20, fill='x')

    col_vars = {}
    for i, col in enumerate(all_cols):
        if col == 'ID_клиента':
            continue
        var = tk.BooleanVar(value=False)
        col_vars[col] = var
        chk = tk.Checkbutton(frame_cols, text=col, variable=var,
                       bg=bg, fg='#002B5B', font=('Calibri', 10),
                       selectcolor=bg, activebackground=bg, activeforeground='#007BFF')
        chk.grid(row=i // 3, column=i % 3, sticky='w', padx=8, pady=5)

    def _run():
        """Формирует статистический отчёт по отмеченным атрибутам."""
        try:
            selected = [c for c, v in col_vars.items() if v.get()]
            if not selected:
                messagebox.showwarning('Выбор',
                                       'Выберите хотя бы один атрибут.', parent=win)
                return
            content = rpt.report_statistics(DF_CLIENTS, DF_FINANCE, selected)
            _output_text_window('Результат — Отчёт 2 (Статистика)', content)
        except Exception as err:
            messagebox.showerror('Ошибка', f'Ошибка формирования отчёта:\n{err}', parent=win)

    btn_frame = tk.Frame(win, bg=bg)
    btn_frame.pack(pady=20)
    _make_button(btn_frame, '📊 Сформировать отчёт', _run, width=26).pack()


def _open_report3():
    """
    Открывает диалог построения сводной таблицы (pivot_table).

    :returns: None
    :author: Садовский Арсений Валентинович
    """
    if DF_CLIENTS.empty or DF_FINANCE.empty:
        messagebox.showwarning('Нет данных', 'Сначала загрузите данные.')
        return

    all_cols = (list(DF_CLIENTS.columns) +
                [c for c in DF_FINANCE.columns if c != 'ID_клиента'])
    merged = pd.merge(DF_CLIENTS, DF_FINANCE, on='ID_клиента', how='inner')
    cat_cols = [c for c in all_cols
                if not pd.api.types.is_numeric_dtype(merged.get(c, pd.Series(dtype=str)))]

    win = tk.Toplevel()
    win.title('Отчёт 3 — Сводная таблица')
    win.geometry('620x380')
    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    win.configure(bg=bg)

    _make_label(win, 'Настройка сводной таблицы:', bold=True, font_size=12).pack(
        pady=15)

    params = [
        ('Строки (index):', cat_cols),
        ('Столбцы (columns):', cat_cols),
        ('Значения:', all_cols),
        ('Агрегация:', ['count', 'mean', 'sum', 'min', 'max']),
    ]

    form_frame = tk.Frame(win, bg=bg)
    form_frame.pack(padx=20, pady=10)

    combos = []
    for i, (lbl, vals) in enumerate(params):
        _make_label(form_frame, lbl, font_size=11, bold=True).grid(
            row=i, column=0, padx=10, pady=10, sticky='e')
        cb = _make_combobox(form_frame, vals, width=24)
        cb.grid(row=i, column=1, padx=10, pady=10)
        combos.append(cb)

    def _run():
        """Строит сводную таблицу по выбранным параметрам."""
        try:
            content = rpt.report_pivot(
                DF_CLIENTS, DF_FINANCE,
                combos[0].get(), combos[1].get(),
                combos[2].get(), combos[3].get(),
            )
            _output_text_window('Результат — Отчёт 3 (Сводная таблица)', content)
        except Exception as err:
            messagebox.showerror('Ошибка', f'Ошибка построения таблицы:\n{err}', parent=win)

    btn_frame = tk.Frame(win, bg=bg)
    btn_frame.pack(pady=20)
    _make_button(btn_frame, '📐 Построить таблицу', _run, width=26).pack()


def _build_graphic_window(title, col_params, build_fn, report_num):
    """
    Универсальный диалог настройки и запуска графического отчёта.

    :param title: Заголовок окна.
    :type title: str
    :param col_params: Список кортежей (метка, список_значений).
    :type col_params: list[tuple]
    :param build_fn: Функция (combos, save_path) -> Figure.
    :type build_fn: callable
    :param report_num: Номер отчёта для имени файла по умолчанию.
    :type report_num: int
    :returns: None
    :author: Черноморец Олег Сергеевич
    """
    if DF_CLIENTS.empty or DF_FINANCE.empty:
        messagebox.showwarning('Нет данных', 'Сначала загрузите данные.')
        return

    win = tk.Toplevel()
    win.title(title)
    win.geometry('1280x800')
    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    win.configure(bg=bg)

    _make_label(win, title, bold=True, font_size=12).pack(pady=15)

    params_frame = tk.Frame(win, bg=bg)
    params_frame.pack(padx=20, pady=10)

    combos = []
    for i, (lbl, vals) in enumerate(col_params):
        _make_label(params_frame, lbl, font_size=11, bold=True).grid(
            row=i, column=0, padx=10, pady=10, sticky='e')
        cb = _make_combobox(params_frame, vals, width=26)
        cb.grid(row=i, column=1, padx=10, pady=10)
        combos.append(cb)

    gfx_dir = utils.get_param(CONFIG, 'paths', 'graphics_dir', 'graphics')
    gfx_fmt = utils.get_param(CONFIG, 'export', 'graphics_format', 'png')

    canvas_frame = tk.Frame(win, bg='white')
    canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def _run():
        """Строит и отображает график."""
        try:
            # Очистить предыдущий график
            for widget in canvas_frame.winfo_children():
                widget.destroy()

            # Построить фигуру
            save_path = os.path.join(gfx_dir, f'report{report_num}.{gfx_fmt}')
            fig = build_fn(combos, save_path)

            # Встроить график в Tkinter
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
        except Exception as err:  # pylint: disable=broad-except
            messagebox.showerror('Ошибка', f'Ошибка при отображении графика:\n{err}', parent=win)

    def _save():
        """Строит график и сохраняет в выбранный файл."""
        path = filedialog.asksaveasfilename(
            parent=win,
            initialdir=gfx_dir,
            defaultextension=f'.{gfx_fmt}',
            filetypes=[('PNG', '*.png'), ('PDF', '*.pdf')],
        )
        if path:
            try:
                build_fn(combos, path)
                messagebox.showinfo('Сохранено', f'График сохранён:\n{path}',
                                    parent=win)
            except Exception as err:  # pylint: disable=broad-except
                messagebox.showerror('Ошибка', f'Ошибка сохранения:\n{err}', parent=win)

    btn_frame = tk.Frame(win, bg=bg)
    btn_frame.pack(pady=15)
    _make_button(btn_frame, '👁️ Показать', _run, width=16).pack(side='left', padx=10)
    _make_button(btn_frame, '💾 Сохранить', _save, width=16).pack(side='left', padx=10)


def _open_report4():
    """
    Диалог кластеризованной столбчатой диаграммы (отчёт 4).

    :returns: None
    :author: Черноморец Олег Сергеевич
    """
    cat_cols = [c for c in list(DF_CLIENTS.columns) +
                [c for c in DF_FINANCE.columns if c != 'ID_клиента']
                if c not in ('ID_клиента', 'Возраст', 'Баланс')]

    def _build(combos, save_path):
        """Вызывает report_bar_chart с выбранными атрибутами."""
        return rpt.report_bar_chart(
            DF_CLIENTS, DF_FINANCE,
            combos[0].get(), combos[1].get(), save_path,
        )

    _build_graphic_window(
        'Отчёт 4 — Столбчатая диаграмма',
        [('Атрибут (ось X):', cat_cols), ('Группировка:', cat_cols)],
        _build, 4,
    )


def _open_report5():
    """
    Диалог категоризированной гистограммы (отчёт 5).

    :returns: None
    :author: Черноморец Олег Сергеевич
    """
    num_cols = ['Возраст', 'Баланс']
    cat_cols = [c for c in list(DF_CLIENTS.columns) +
                [c for c in DF_FINANCE.columns if c != 'ID_клиента']
                if c not in num_cols + ['ID_клиента']]

    def _build(combos, save_path):
        """Вызывает report_histogram с выбранными атрибутами."""
        return rpt.report_histogram(
            DF_CLIENTS, DF_FINANCE,
            combos[0].get(), combos[1].get(), save_path=save_path,
        )

    _build_graphic_window(
        'Отчёт 5 — Гистограмма',
        [('Количественный атрибут:', num_cols),
         ('Качественный атрибут:', cat_cols)],
        _build, 5,
    )


def _open_report6():
    """
    Диалог диаграммы Бокса-Вискера (отчёт 6).

    :returns: None
    :author: Черноморец Олег Сергеевич
    """
    num_cols = ['Возраст', 'Баланс']
    cat_cols = [c for c in list(DF_CLIENTS.columns) +
                [c for c in DF_FINANCE.columns if c != 'ID_клиента']
                if c not in num_cols + ['ID_клиента']]

    def _build(combos, save_path):
        """Вызывает report_boxplot с выбранными атрибутами."""
        return rpt.report_boxplot(
            DF_CLIENTS, DF_FINANCE,
            combos[0].get(), combos[1].get(), save_path,
        )

    _build_graphic_window(
        'Отчёт 6 — Диаграмма Бокса-Вискера',
        [('Количественный атрибут:', num_cols),
         ('Качественный атрибут:', cat_cols)],
        _build, 6,
    )


def _open_report7():
    """
    Диалог диаграммы рассеивания (отчёт 7).

    :returns: None
    :author: Черноморец Олег Сергеевич
    """
    num_cols = ['Возраст', 'Баланс']
    cat_cols = [c for c in list(DF_CLIENTS.columns) +
                [c for c in DF_FINANCE.columns if c != 'ID_клиента']
                if c not in num_cols + ['ID_клиента']]

    def _build(combos, save_path):
        """Вызывает report_scatter с выбранными атрибутами."""
        return rpt.report_scatter(
            DF_CLIENTS, DF_FINANCE,
            combos[0].get(), combos[1].get(),
            combos[2].get(), save_path,
        )

    _build_graphic_window(
        'Отчёт 7 — Диаграмма рассеивания',
        [('Ось X (количественный):', num_cols),
         ('Ось Y (количественный):', num_cols),
         ('Цвет (качественный):', cat_cols)],
        _build, 7,
    )


# ---------------------------------------------------------------------------
# Оценка клиентов (новая функция)
# ---------------------------------------------------------------------------

def _calculate_client_score(client_id):
    """
    Вычисляет оценку клиента и определяет, подходит ли он.

    :param client_id: ID клиента.
    :returns: Кортеж (оценка_от_100, статус_подходит_ли).
    :rtype: tuple[int, bool]
    """
    if DF_CLIENTS.empty or DF_FINANCE.empty:
        return 0, False

    client = DF_CLIENTS[DF_CLIENTS['ID_клиента'] == client_id]
    finance = DF_FINANCE[DF_FINANCE['ID_клиента'] == client_id]

    if client.empty or finance.empty:
        return 0, False

    score = 50  # базовая оценка

    # 1. Возраст (28-45 лет идеально)
    age = int(client['Возраст'].values[0])
    if 28 <= age <= 45:
        score += 20
    elif 25 <= age <= 50:
        score += 10

    # 2. Образование (выше = лучше)
    education = client['Образование'].values[0]
    if education == 'Высшее':
        score += 15
    elif education == 'Среднее':
        score += 8

    # 3. Семейное положение (женат/замужем лучше)
    marital = client['Семейное_положение'].values[0]
    if marital == 'Женат/Замужем':
        score += 10

    # 4. Профессия (управленец лучше)
    job = client['Профессия'].values[0]
    if job in ('Управленец', 'Предприниматель'):
        score += 12
    elif job in ('Техник', 'Администратор'):
        score += 6

    # 5. Баланс (положительный баланс хорошо)
    balance = int(finance['Баланс'].values[0])
    if balance > 5000:
        score += 18
    elif balance > 0:
        score += 10

    # 6. Дефолт (нет дефолтов = очень хорошо)
    default = finance['Дефолт'].values[0]
    if default == 'Нет':
        score += 15
    else:
        score -= 30

    # 7. Кредит и ипотека (наличие = позитивная кредитная история)
    has_credit = finance['Кредит'].values[0] == 'Да'
    has_mortgage = finance['Ипотека'].values[0] == 'Да'
    if has_credit and has_mortgage:
        score += 8
    elif has_credit or has_mortgage:
        score += 4

    score = max(0, min(100, score))  # от 0 до 100
    is_suitable = score >= 65

    return int(score), is_suitable


def _open_client_assessment():
    """
    Открывает окно для оценки клиентов.

    Позволяет выбрать клиента и увидеть его оценку с рекомендацией.

    :returns: None
    """
    if DF_CLIENTS.empty or DF_FINANCE.empty:
        messagebox.showwarning('Нет данных', 'Сначала загрузите данные.')
        return

    win = tk.Toplevel()
    win.title('⭐ Оценка клиентов')
    win.geometry('900x700')
    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    win.configure(bg=bg)

    # — Заголовок —
    _make_label(win, '⭐ Оценка и классификация клиентов', bold=True,
               font_size=14, bg=bg, fg='#007BFF').pack(pady=15)

    # — Список клиентов —
    frame_list = tk.Frame(win, bg=bg)
    frame_list.pack(fill='both', expand=True, padx=15, pady=10)

    _make_label(frame_list, 'Выберите клиента из списка:', bold=True,
               font_size=11, bg=bg).pack(anchor='w', pady=(0, 8))

    scroll_y = tk.Scrollbar(frame_list, orient='vertical')
    scroll_x = tk.Scrollbar(frame_list, orient='horizontal')

    client_tree = ttk.Treeview(
        frame_list,
        columns=('ID', 'Возраст', 'Профессия', 'Баланс'),
        show='headings',
        height=12,
        yscrollcommand=scroll_y.set,
        xscrollcommand=scroll_x.set,
    )

    scroll_y.config(command=client_tree.yview)
    scroll_x.config(command=client_tree.xview)

    client_tree.heading('ID', text='ID')
    client_tree.heading('Возраст', text='Возраст')
    client_tree.heading('Профессия', text='Профессия')
    client_tree.heading('Баланс', text='Баланс')

    client_tree.column('ID', width=60)
    client_tree.column('Возраст', width=80)
    client_tree.column('Профессия', width=150)
    client_tree.column('Баланс', width=100)

    for _, row in DF_CLIENTS.iterrows():
        client_id = int(row['ID_клиента'])
        age = int(row['Возраст'])
        job = row['Профессия']
        balance = int(DF_FINANCE[DF_FINANCE['ID_клиента'] == client_id]['Баланс'].values[0])
        client_tree.insert('', 'end', values=(client_id, age, job, balance))

    scroll_y.pack(side='right', fill='y')
    scroll_x.pack(side='bottom', fill='x')
    client_tree.pack(fill='both', expand=True)

    # — Информационная панель —
    info_frame = tk.Frame(win, bg='#FFFFFF', relief='solid', bd=2)
    info_frame.pack(fill='both', padx=15, pady=10)

    info_text = tk.Text(info_frame, font=('Calibri', 11), wrap='word',
                       bg='#FFFFFF', fg='#002B5B', relief='flat', height=12)
    info_text.pack(fill='both', expand=True, padx=12, pady=12)
    info_text.configure(state='disabled')

    def _on_select(event=None):
        """Отображает информацию о выбранном клиенте."""
        sel = client_tree.selection()
        if not sel:
            return

        values = client_tree.item(sel[0])['values']
        client_id = int(values[0])

        client = DF_CLIENTS[DF_CLIENTS['ID_клиента'] == client_id].iloc[0]
        finance = DF_FINANCE[DF_FINANCE['ID_клиента'] == client_id].iloc[0]
        score, is_suitable = _calculate_client_score(client_id)

        status = '✅ ПОДХОДИТ' if is_suitable else '❌ НЕ ПОДХОДИТ'
        color_indicator = '🟢' if is_suitable else '🔴'

        info_text.configure(state='normal')
        info_text.delete('1.0', 'end')

        content = f"""{color_indicator} {status}
Оценка: {score}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 ДАННЫЕ КЛИЕНТА
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID клиента: {client_id}
Возраст: {int(client['Возраст'])} лет
Профессия: {client['Профессия']}
Семейное положение: {client['Семейное_положение']}
Образование: {client['Образование']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 ФИНАНСОВАЯ ИНФОРМАЦИЯ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Баланс: {int(finance['Баланс'])} €
Дефолт: {finance['Дефолт']}
Ипотека: {finance['Ипотека']}
Кредит: {finance['Кредит']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 КРИТЕРИИ ОЦЕНКИ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Возраст оптимален (28-45): {'✅' if 28 <= int(client['Возраст']) <= 45 else '❌'}
✓ Высокое образование: {'✅' if client['Образование'] == 'Высшее' else '❌'}
✓ Семейное положение: {'✅' if client['Семейное_положение'] == 'Женат/Замужем' else '❌'}
✓ Хорошая профессия: {'✅' if client['Профессия'] in ('Управленец', 'Предприниматель') else '❌'}
✓ Положительный баланс: {'✅' if int(finance['Баланс']) > 0 else '❌'}
✓ Отсутствие дефолтов: {'✅' if finance['Дефолт'] == 'Нет' else '❌'}
✓ Кредитная история: {'✅' if finance['Кредит'] == 'Да' or finance['Ипотека'] == 'Да' else '❌'}
"""

        info_text.insert('end', content)
        info_text.configure(state='disabled')

    client_tree.bind('<<TreeviewSelect>>', _on_select)

    # — Кнопки —
    btn_frame = tk.Frame(win, bg=bg)
    btn_frame.pack(pady=10)

    def _export_assessment():
        """Экспортирует оценку в файл."""
        sel = client_tree.selection()
        if not sel:
            messagebox.showwarning('Выбор', 'Выберите клиента.', parent=win)
            return

        values = client_tree.item(sel[0])['values']
        client_id = int(values[0])
        score, is_suitable = _calculate_client_score(client_id)

        content = info_text.get('1.0', 'end')
        out_dir = utils.get_param(CONFIG, 'paths', 'output_dir', 'output')
        path = os.path.join(out_dir, f'assessment_client_{client_id}.txt')

        utils.save_text(path, content)
        messagebox.showinfo('Сохранено', f'Оценка сохранена:\n{path}', parent=win)

    _make_button(btn_frame, '💾 Сохранить оценку', _export_assessment, width=24).pack(side='left', padx=8)
    _make_button(btn_frame, '✅ Закрыть', win.destroy, width=24).pack(side='left', padx=8)


# ---------------------------------------------------------------------------
# Загрузка данных
# ---------------------------------------------------------------------------

def _load_data_dialog():
    """
    Открывает диалог загрузки данных из CSV или из сохранённых .pkl справочников.

    При загрузке из CSV нормализует данные, разделяет на два справочника,
    немедленно сохраняет pkl-файлы и обновляет глобальные переменные.

    :returns: None
    :author: Садовский Арсений Валентинович
    """
    global DF_CLIENTS, DF_FINANCE  # pylint: disable=global-statement

    win = tk.Toplevel()
    win.title('Загрузка данных')
    win.geometry('520x320')
    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    win.configure(bg=bg)
    win.grab_set()

    _make_label(win, '📂 Выберите источник данных:', bold=True, font_size=14, bg=bg).pack(
        pady=25)

    def _from_csv():
        """Загружает и нормализует CSV, сохраняет pkl, обновляет глобальные переменные."""
        path = filedialog.askopenfilename(
            parent=win,
            filetypes=[('CSV files', '*.csv')],
            title='Выберите файл bank-full.csv',
        )
        if not path:
            return
        df_full = utils.load_source_csv(path)
        if df_full is None:
            messagebox.showerror('Ошибка', 'Не удалось загрузить CSV.',
                                 parent=win)
            return

        global DF_CLIENTS, DF_FINANCE  # pylint: disable=global-statement
        DF_CLIENTS, DF_FINANCE = utils.split_to_handbooks(df_full)
        utils.save_dataframe(DF_CLIENTS, _clients_path())
        utils.save_dataframe(DF_FINANCE, _finance_path())

        messagebox.showinfo(
            'Загружено',
            f'✅ Загружено {len(DF_CLIENTS)} клиентов.\n'
            'Справочники сохранены автоматически.',
            parent=win,
        )
        win.destroy()

    def _from_pkl():
        """Загружает справочники из pkl-файлов и обновляет глобальные переменные."""
        if not os.path.exists(_clients_path()) or not os.path.exists(_finance_path()):
            messagebox.showwarning(
                'Файлы не найдены',
                'Сначала загрузите данные из CSV.',
                parent=win,
            )
            return

        global DF_CLIENTS, DF_FINANCE  # pylint: disable=global-statement
        df_c = utils.load_dataframe(_clients_path())
        df_f = utils.load_dataframe(_finance_path())

        if df_c.empty or df_f.empty:
            messagebox.showerror('Ошибка',
                                 'Справочники пусты или повреждены.',
                                 parent=win)
            return

        DF_CLIENTS = df_c
        DF_FINANCE = df_f
        messagebox.showinfo('Загружено',
                            f'✅ Справочники загружены: {len(DF_CLIENTS)} клиентов.',
                            parent=win)
        win.destroy()

    btn_frame = tk.Frame(win, bg=bg)
    btn_frame.pack(pady=20)
    _make_button(btn_frame, '📥 Загрузить из CSV', _from_csv, width=26).pack(pady=10)
    _make_button(btn_frame, '📦 Из справочников (.pkl)', _from_pkl, width=26).pack(pady=10)


def _init_data():
    """
    Инициализирует данные при запуске приложения по следующему приоритету:

    1. Если pkl-файлы существуют — загружает их.
    2. Если есть CSV — загружает из CSV и сохраняет pkl.
    3. Если нет ни pkl, ни CSV — создаёт синтетические тестовые данные.

    :returns: None
    :author: Садовский Арсений Валентинович
    """
    global DF_CLIENTS, DF_FINANCE  # pylint: disable=global-statement

    # 1. Попытка загрузки из pkl
    if os.path.exists(_clients_path()) and os.path.exists(_finance_path()):
        df_c = utils.load_dataframe(_clients_path())
        df_f = utils.load_dataframe(_finance_path())
        if not df_c.empty and not df_f.empty:
            DF_CLIENTS = df_c
            DF_FINANCE = df_f
            print(f'[init] Загружены справочники: {len(DF_CLIENTS)} записей.')
            return

    # 2. Попытка загрузки из CSV
    csv_path = os.path.join(
        ROOT_DIR, utils.get_param(CONFIG, 'paths', 'source_csv', 'data/bank-full.csv'))
    if os.path.exists(csv_path):
        df_full = utils.load_source_csv(csv_path)
        if df_full is not None:
            DF_CLIENTS, DF_FINANCE = utils.split_to_handbooks(df_full)
            utils.save_dataframe(DF_CLIENTS, _clients_path())
            utils.save_dataframe(DF_FINANCE, _finance_path())
            print(f'[init] CSV загружен: {len(DF_CLIENTS)} записей.')
            return

    # 3. Синтетические тестовые данные
    print('[init] CSV и pkl не найдены — создаются тестовые данные (200 записей).')
    DF_CLIENTS, DF_FINANCE = utils.create_sample_data(200)
    utils.save_dataframe(DF_CLIENTS, _clients_path())
    utils.save_dataframe(DF_FINANCE, _finance_path())


# ---------------------------------------------------------------------------
# Главное окно
# ---------------------------------------------------------------------------

def build_main_window():
    """
    Создаёт и конфигурирует главное окно приложения.

    Строит заголовок, боковую панель навигации с кнопками,
    информационную область и статус-бар.

    :returns: Объект главного окна Tkinter.
    :rtype: tk.Tk
    :author: Черноморец Олег Сергеевич
    """
    root = tk.Tk()
    _style_treeview()
    app_title = utils.get_param(CONFIG, 'interface', 'title',
                                'Анализ данных о клиентах банка')
    root.title(app_title)

    w = int(utils.get_param(CONFIG, 'interface', 'window_width', '1200'))
    h = int(utils.get_param(CONFIG, 'interface', 'window_height', '750'))
    root.geometry(f'{w}x{h}')
    root.resizable(True, True)

    bg = utils.get_param(CONFIG, 'interface', 'bg_color', '#E3F2FD')
    accent = utils.get_param(CONFIG, 'interface', 'accent_color', '#007BFF')
    fg = utils.get_param(CONFIG, 'interface', 'fg_color', '#002B5B')
    root.configure(bg=bg)

    # — Верхняя панель —
    header = tk.Frame(root, bg='#003366', height=65)
    header.pack(fill='x')
    header.pack_propagate(False)
    tk.Label(header, text='  🏦  ' + app_title,
             bg='#003366', fg='white',
             font=('Calibri', 18, 'bold')).pack(side='left', padx=20, pady=12)

    # — Левая панель навигации —
    sidebar = tk.Frame(root, bg='#003366', width=260)
    sidebar.pack(side='left', fill='y')
    sidebar.pack_propagate(False)

    # — Основная область —
    content = tk.Frame(root, bg=bg)
    content.pack(side='left', fill='both', expand=True)

    def _sidebar_button(text, command):
        """Создаёт кнопку на боковой панели с hover-эффектом."""
        btn = tk.Button(
            sidebar, text=text, command=command,
            bg='#004080', fg='#FFFFFF',
            font=('Calibri', 11, 'bold'), relief='flat',
            anchor='w', padx=15, pady=11, cursor='hand2',
            activebackground='#007BFF', activeforeground='#FFFFFF',
            bd=0, highlightthickness=0,
        )
        btn.pack(fill='x', pady=2, padx=8)
        btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#007BFF', relief='flat'))
        btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#004080', relief='flat'))
        return btn

    def _section_label(text):
        """Создаёт заголовок секции в боковой панели."""
        tk.Label(sidebar, text=text, bg='#003366', fg='#00A8E8',
                 font=('Calibri', 10, 'bold')).pack(
            fill='x', padx=20, pady=(16, 6))

    # — ДАННЫЕ —
    _section_label('ДАННЫЕ')
    _sidebar_button('📂  Загрузить данные', _load_data_dialog)

    # — СПРАВОЧНИКИ —
    _section_label('СПРАВОЧНИКИ')

    def _open_clients():
        """Открывает справочник демографии с геттером/сеттером глобальной переменной."""
        if DF_CLIENTS.empty:
            messagebox.showwarning('Нет данных', 'Сначала загрузите данные.')
            return

        def getter():
            """Возвращает текущий DataFrame демографии."""
            return DF_CLIENTS

        def setter(df):
            """Обновляет глобальный DF_CLIENTS."""
            global DF_CLIENTS  # pylint: disable=global-statement
            DF_CLIENTS = df

        def auto_save():
            """Сохраняет DF_CLIENTS в pkl."""
            utils.save_dataframe(DF_CLIENTS, _clients_path())

        meta = [
            {'name': 'ID_клиента', 'type': 'int', 'values': []},
            {'name': 'Возраст', 'type': 'age', 'values': []},
            {'name': 'Профессия', 'type': 'choice', 'values': utils.VALID_JOB},
            {'name': 'Семейное_положение', 'type': 'choice',
             'values': utils.VALID_MARITAL},
            {'name': 'Образование', 'type': 'choice',
             'values': utils.VALID_EDUCATION},
        ]
        _open_handbook_window('Справочник 1 — Демография',
                              getter, setter, auto_save, meta)

    def _open_finance():
        """Открывает справочник финансов с геттером/сеттером глобальной переменной."""
        if DF_FINANCE.empty:
            messagebox.showwarning('Нет данных', 'Сначала загрузите данные.')
            return

        def getter():
            """Возвращает текущий DataFrame финансов."""
            return DF_FINANCE

        def setter(df):
            """Обновляет глобальный DF_FINANCE."""
            global DF_FINANCE  # pylint: disable=global-statement
            DF_FINANCE = df

        def auto_save():
            """Сохраняет DF_FINANCE в pkl."""
            utils.save_dataframe(DF_FINANCE, _finance_path())

        meta = [
            {'name': 'ID_клиента', 'type': 'int', 'values': []},
            {'name': 'Дефолт', 'type': 'choice', 'values': utils.VALID_BINARY},
            {'name': 'Баланс', 'type': 'int', 'values': []},
            {'name': 'Ипотека', 'type': 'choice', 'values': utils.VALID_BINARY},
            {'name': 'Кредит', 'type': 'choice', 'values': utils.VALID_BINARY},
        ]
        _open_handbook_window('Справочник 2 — Финансы',
                              getter, setter, auto_save, meta)

    _sidebar_button('👥  Демография', _open_clients)
    _sidebar_button('💳  Финансы', _open_finance)

    # — ОЦЕНКА КЛИЕНТОВ —
    _section_label('ОЦЕНКА КЛИЕНТОВ')
    _sidebar_button('⭐  Оценить клиентов', _open_client_assessment)

    # — ТЕКСТОВЫЕ ОТЧЁТЫ —
    _section_label('ТЕКСТОВЫЕ ОТЧЁТЫ')
    _sidebar_button('📋  Отчёт 1 — Выборка', _open_report1)
    _sidebar_button('📊  Отчёт 2 — Статистика', _open_report2)
    _sidebar_button('📐  Отчёт 3 — Сводная таблица', _open_report3)

    # — ГРАФИЧЕСКИЕ ОТЧЁТЫ —
    _section_label('ГРАФИЧЕСКИЕ ОТЧЁТЫ')
    _sidebar_button('📈  Отчёт 4 — Столбчатая диагр.', _open_report4)
    _sidebar_button('📉  Отчёт 5 — Гистограмма', _open_report5)
    _sidebar_button('📦  Отчёт 6 — Бокса-Вискера', _open_report6)
    _sidebar_button('🔵  Отчёт 7 — Рассеивание', _open_report7)

    # — Приветственная панель —
    info_frame = tk.Frame(content, bg=bg)
    info_frame.pack(fill='both', expand=True, padx=50, pady=30)

    tk.Label(
        info_frame,
        text='🏦 Система анализа данных клиентов банка',
        bg=bg, fg='#003366', font=('Calibri', 22, 'bold'),
        wraplength=720, justify='center',
    ).pack(pady=(20, 8))

    tk.Label(
        info_frame,
        text='Аналитическая платформа для работы со справочниками и построения отчётов',
        bg=bg, fg='#3A6EA5', font=('Calibri', 12),
        justify='center',
    ).pack(pady=(0, 25))

    # Карточки статистики
    cards_frame = tk.Frame(info_frame, bg=bg)
    cards_frame.pack(pady=10)

    n_records = len(DF_CLIENTS) if not DF_CLIENTS.empty else 0

    def _info_card(parent, icon, title, value, col):
        card = tk.Frame(parent, bg='#FFFFFF', relief='solid', bd=1)
        card.grid(row=0, column=col, padx=12, pady=8, ipadx=20, ipady=12)
        tk.Label(card, text=icon, bg='#FFFFFF', fg='#007BFF', font=('Calibri', 24)).pack()
        tk.Label(card, text=str(value), bg='#FFFFFF', fg='#007BFF',
                 font=('Calibri', 18, 'bold')).pack()
        tk.Label(card, text=title, bg='#FFFFFF', fg='#3A6EA5',
                 font=('Calibri', 10)).pack()

    _info_card(cards_frame, '👥', 'Клиентов загружено', n_records, 0)
    _info_card(cards_frame, '📋', 'Видов отчётов', '7', 1)
    _info_card(cards_frame, '📊', 'Справочников', '2', 2)

    sep = tk.Frame(info_frame, bg='#90CAF9', height=1)
    sep.pack(fill='x', pady=20)

    hint_text = (
        '← Используйте меню слева для навигации\n\n'
        '📂  Загрузите данные из CSV или pkl-файла\n'
        '👥  Просматривайте и редактируйте справочники\n'
        '📋  Формируйте текстовые и графические отчёты\n'
        '⭐  Оценивайте клиентов по критериям'
    )
    tk.Label(
        info_frame, text=hint_text,
        bg=bg, fg=fg, font=('Calibri', 12),
        justify='left',
    ).pack(pady=5)

    # Статус-бар
    status_bar = tk.Label(
        root,
        text=f'  ✓ Готово. Записей в памяти: {n_records}.',
        bg='#007BFF', fg='#FFFFFF',
        font=('Calibri', 10), anchor='w', padx=15, pady=6,
    )
    status_bar.pack(side='bottom', fill='x')

    return root


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

def main():
    """
    Точка входа в приложение.

    Создаёт рабочие каталоги, инициализирует данные (pkl → CSV → синтетика),
    строит главное окно и запускает цикл событий Tkinter.

    :returns: None
    :author: Садовский Арсений Валентинович
    """
    os.chdir(ROOT_DIR)
    utils.ensure_dirs(CONFIG)
    _init_data()
    root = build_main_window()
    root.mainloop()


if __name__ == '__main__':
    main()

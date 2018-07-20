#! /usr/bin/env/ python
# -*- coding: utf-8 -*-

import os
import re
import sqlite3
from datetime import date
from calendar import monthrange
from contextlib import closing

from setting_file import *

# yearからデータベースファイルのパスを返す
def _get_filepath(year):
    directory_path = '../db'
    file_name = 'kakeibo' + str(year) + '.db'

    if not os.path.exists('../db'):
        os.mkdir('../db')

    return os.path.join(directory_path, file_name)

# 外部キー制約の有効化とテーブルの初期化
def _initialize_database(curs):
    curs.execute('PRAGMA foreign_keys = ON')  # 外部キー制約の有効化

    # 大項目テーブルの初期化
    ddl = '''
    CREATE TABLE IF NOT EXISTS major
    (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        major_item TEXT UNIQUE NOT NULL
    )
    '''
    curs.execute(ddl)

    curs.execute('SELECT COUNT(*) FROM major')
    if (curs.fetchall()[0][0] == 0):
        curs.execute('INSERT INTO major (major_item) VALUES(\'繰越\')')
        curs.execute('INSERT INTO major (major_item) VALUES(\'振替\')')
        for major_item in get_json('item').keys():
            ins = 'INSERT INTO major (major_item) VALUES(?)'
            curs.execute(ins, (major_item,))

    # 小項目テーブルの初期化
    ddl = '''
    CREATE TABLE IF NOT EXISTS minor
    (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        minor_item TEXT NOT NULL,
        major_item TEXT,
        amount_sign TEXT NOT NULL,
        UNIQUE(minor_item, major_item),
        FOREIGN KEY(major_item) REFERENCES major(major_item)
    )
    '''
    curs.execute(ddl)

    curs.execute('SELECT COUNT(*) FROM minor')
    if (curs.fetchall()[0][0] == 0):
        curs.execute('INSERT INTO minor (minor_item, major_item, amount_sign) VALUES(\'繰越\', \'繰越\', \'+\')')
        curs.execute('INSERT INTO minor (minor_item, major_item, amount_sign) VALUES(\'振替\', \'振替\', \'±\')')
        for item_tuple in get_json('item').items():
            for minor_item_list in item_tuple[1]:
                if minor_item_list[1] == '+' or minor_item_list[1] == '-' or minor_item_list[1] == '±':
                    ins = 'INSERT INTO minor (minor_item, major_item, amount_sign) VALUES(?, ?, ?)'
                    curs.execute(ins, (minor_item_list[0], item_tuple[0], minor_item_list[1]))

    # 金融機関テーブルの初期化
    ddl = '''
    CREATE TABLE IF NOT EXISTS bank
    (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        bank_name TEXT UNIQUE NOT NULL
    )
    '''
    curs.execute(ddl)

    curs.execute('SELECT COUNT(*) FROM bank')
    if (curs.fetchall()[0][0] == 0):
        for bank_name in get_json('name').keys():
            ins = 'INSERT INTO bank (bank_name) VALUES(?)'
            curs.execute(ins, (bank_name,))

    # 目的テーブルの初期化
    ddl = '''
    CREATE TABLE IF NOT EXISTS purpose
    (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        purpose_name TEXT NOT NULL,
        bank_name TEXT,
        UNIQUE(purpose_name, bank_name),
        FOREIGN KEY(bank_name) REFERENCES bank(bank_name)
    )
    '''
    curs.execute(ddl)

    curs.execute('SELECT COUNT(*) FROM purpose')
    if (curs.fetchall()[0][0] == 0):
        for name_tuple in get_json('name').items():
            ins = 'INSERT INTO purpose (purpose_name, bank_name) VALUES(?, ?)'
            curs.execute(ins, (name_tuple[0], name_tuple[0]))
            for purpose_name in name_tuple[1]:
                if purpose_name != name_tuple[0]:
                    ins = 'INSERT INTO purpose (purpose_name, bank_name) VALUES(?, ?)'
                    curs.execute(ins, (purpose_name, name_tuple[0]))

    # 通貨テーブルの初期化
    ddl = '''
    CREATE TABLE IF NOT EXISTS currency
    (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    '''
    curs.execute(ddl)

    curs.execute('SELECT COUNT(*) FROM currency')
    if (curs.fetchall()[0][0] == 0):
        for name in get_json('currency'):
            ins = 'INSERT INTO currency (name) VALUES(?)'
            curs.execute(ins, (name,))

    # 収支表テーブルの初期化
    ddl = '''
    CREATE TABLE IF NOT EXISTS balance
    (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        balance_date DATE NOT NULL,
        connection TEXT,
        content TEXT,
        major_item TEXT NOT NULL,
        minor_item TEXT NOT NULL,
        bank_name TEXT NOT NULL,
        purpose_name TEXT NOT NULL,
        currency TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY(major_item, minor_item) REFERENCES minor(major_item, minor_item),
        FOREIGN KEY(bank_name, purpose_name) REFERENCES purpose(bank_name, purpose_name),
        FOREIGN KEY(currency) REFERENCES currency(name)
    )
    '''
    curs.execute(ddl)

# 条件文とプレースホルダの引数リストを返す
def _conditions_tuple(delimiter=', ', **kwargs):
    conditions_list = []
    args_list = []

    for items in kwargs.items():
        if items[0] == 'sort':
            if items[1] == 'income':
                conditions_list.append('amount >= 0')
            elif items[1] == 'outgo':
                conditions_list.append('amount < 0')
        else:
            if items[1]:
                conditions_list.append(items[0] + ' = ?')
                args_list.append(items[1])

    return (delimiter.join(conditions_list), args_list)

# データベース接続のためのデコレータ
def connect_database(func):
    def _wrapper(*args, year=None, **kwargs):
        if year is None:
            year = date.today().year

        with closing(sqlite3.connect(_get_filepath(year), detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)) as conn:
            curs = conn.cursor()
            _initialize_database(curs)

            res = func(curs, year, *args, **kwargs)

            curs.close()
            conn.commit()

        return res

    return _wrapper

# データベースの作成
# e.g. create_database(year=20XX)
@connect_database
def create_database(curs, year):
    pass

# 大項目テーブルへの追加
# e.g. insert_major(major_item, year=20XX)
@connect_database
def insert_major(curs, year, major_item):
    ins = 'INSERT INTO major (major_item) VALUES(?)'
    curs.execute(ins, (major_item,))

# 小項目テーブルへの追加
# e.g. insert_minor(minor_item, major_item, amount_sign, year=20XX)
@connect_database
def insert_minor(curs, year, minor_item, major_item, amount_sign):
    if amount_sign == '+' or amount_sign == '-' or amount_sign == '±':
        ins = 'INSERT INTO minor (minor_item, major_item, amount_sign) VALUES(?, ?, ?)'
        curs.execute(ins, (minor_item, major_item, amount_sign))

# 金融機関テーブルへの追加
# e.g. insert_bank(bank_name, year=20XX)
@connect_database
def insert_bank(curs, year, bank_name):
    ins = 'INSERT INTO bank (bank_name) VALUES(?)'
    curs.execute(ins, (bank_name,))
    ins = 'INSERT INTO purpose (purpose_name, bank_name) VALUES(?, ?)'
    curs.execute(ins, (bank_name, bank_name))


# 目的テーブルへの追加
# e.g. insert_purpose(purpose_name, bank_name, year=20XX)
@connect_database
def insert_purpose(curs, year, purpose_name, bank_name):
    ins = 'INSERT INTO purpose (purpose_name, bank_name) VALUES(?, ?)'
    curs.execute(ins, (purpose_name, bank_name))

# 通貨テーブルへの追加
# e.g. insert_currency(name, year=20XX)
@connect_database
def insert_currency(curs, year, name):
    ins = 'INSERT INTO currency (name) VALUES(?)'
    curs.execute(ins, (name,))

# 収支表テーブルへの追加
# e.g. insert_balance(balance_date, connection, content, major_item, minor_item, bank_name, purpose_name, currency, amount, year=20XX)
@connect_database
def insert_balance(curs, year, balance_date, connection, content, major_item, minor_item, bank_name, purpose_name, currency, amount):
    ins = 'INSERT INTO balance (balance_date, connection, content, major_item, minor_item, bank_name, purpose_name, currency, amount) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)'
    curs.execute(ins, (balance_date, connection, content, major_item, minor_item, bank_name, purpose_name, currency, amount))

# 大項目の取得
# e.g. select_major(year=20XX)
@connect_database
def select_major(curs, year):
    curs.execute('SELECT * FROM major')

    return curs.fetchall()  # [(ID, 大項目), ...]

# 小項目の取得
# e.g. select_minor(major_item, year=20XX)
@connect_database
def select_minor(curs, year, major_item=None):
    if major_item is None:
        curs.execute('SELECT * FROM minor')
    else:
        sel = 'SELECT * FROM minor WHERE major_item = ?'
        curs.execute(sel, (major_item,))

    return curs.fetchall()  # [(ID, 小項目, 大項目, 正負), ...]

# 金融機関の取得
# e.g. select_bank(year=20XX)
@connect_database
def select_bank(curs, year):
    curs.execute('SELECT * FROM bank')

    return curs.fetchall()  # [(ID, 金融機関), ...]

# 目的の取得
# e.g. select_purpose(bank_name, year=20XX)
@connect_database
def select_purpose(curs, year, bank_name=None):
    if bank_name is None:
        curs.execute('SELECT * FROM purpose')
    else:
        sel = 'SELECT * FROM purpose WHERE bank_name = ?'
        curs.execute(sel, (bank_name,))

    return curs.fetchall()  # [(ID, 目的, 金融機関), ...]

# 通貨の取得
# e.g. select_currency(year=20XX)
@connect_database
def select_currency(curs, year):
    curs.execute('SELECT * FROM currency')

    return curs.fetchall()  # [(ID, 通貨), ...]

# 収支表の取得
# e.g. select_balance(year=20XX)
@connect_database
def select_balance(curs, year):
    curs.execute('SELECT * FROM balance')

    return curs.fetchall()  # [(ID, 日付, 取引先, 内容, 大項目, 小項目, 金融機関, 目的, 通貨, 金額), ...]

# 年収支の取得
# sort - 'both', 'income' or 'outgo'
# e.g. sum_year(sort, major_item, minor_item, bank_name, purpose_name, currency, year=20XX)
@connect_database
def sum_year(curs, year, sort='both', major_item=None, minor_item=None, bank_name=None, purpose_name=None, currency=None):
    if currency is None:
        from setting_file import get_default
        currency = get_default('currency')

    conditions = _conditions_tuple(' AND ', sort=sort, major_item=major_item, minor_item=minor_item, bank_name=bank_name, purpose_name=purpose_name, currency=currency)

    if conditions[0]:
        sel = 'SELECT SUM(amount), COUNT(amount) FROM balance WHERE ' + conditions[0]
        curs.execute(sel, conditions[1])
    else:
        curs.execute('SELECT SUM(amount), COUNT(amount) FROM balance')

    res = list(curs.fetchall()[0])
    if res[0] is None:
        res[0] = 0

    return tuple(res)  # (合計, レコード数)

# 期間（start_month月start_day日からend_month月end_day日まで）収支の取得
# sort - 'both', 'income' or 'outgo'
# e.g. sum_period(start_month, start_day, end_month, end_day, sort, major, minor, bank, purpose, currency, year=20XX)
@connect_database
def sum_period(curs, year, start_month=1, start_day=1, end_month=12, end_day=31, sort='both', major_item=None, minor_item=None, bank_name=None, purpose_name=None, currency=None):
    if currency is None:
        from setting_file import get_default
        currency = get_default('currency')

    if end_day == 31:
        end_day = monthrange(year, end_month)[1]

    conditions = _conditions_tuple(' AND ', sort=sort, major_item=major_item, minor_item=minor_item, bank_name=bank_name, purpose_name=purpose_name, currency=currency)

    if conditions[0]:
        sel = 'SELECT SUM(amount), COUNT(amount) FROM balance WHERE ' + conditions[0] + ' AND balance_date BETWEEN ? AND ?'
        curs.execute(sel, (*conditions[1], date(year, start_month, start_day), date(year, end_month, end_day)))
    else:
        sel = 'SELECT SUM(amount), COUNT(amount) FROM balance WHERE balance_date BETWEEN ? AND ?'
        curs.execute(sel, (date(year, start_month, start_day), date(year, end_month, end_day)))

    res = list(curs.fetchall()[0])
    if res[0] is None:
        res[0] = 0

    return tuple(res)  # (合計, レコード数)

# 月ごとの年収支の取得
# sort - 'both', 'income' or 'outgo'
# e.g. sum_year_monthly(sort, major, minor, bank, purpose, currency, year=20XX)
@connect_database
def sum_year_monthly(curs, year, sort='both', major_item=None, minor_item=None, bank_name=None, purpose_name=None, currency=None):
    if currency is None:
        from setting_file import get_default
        currency = get_default('currency')

    conditions = _conditions_tuple(' AND ', sort=sort, major_item=major_item, minor_item=minor_item, bank_name=bank_name, purpose_name=purpose_name, currency=currency)

    if conditions[0]:
        sel = 'SELECT STRFTIME(\'%Y%m\', balance_date), SUM(amount), COUNT(amount) FROM balance WHERE ' + conditions[0] + ' GROUP BY STRFTIME(\'%m\', balance_date)'
        curs.execute(sel, conditions[1])
    else:
        curs.execute('SELECT STRFTIME(\'%Y%m\', balance_date), SUM(amount), COUNT(amount) FROM balance GROUP BY STRFTIME(\'%m\', balance_date)')

    res = []
    for row in curs.fetchall():
        m = re.match(r'(\d{4})(\d{2})', row[0])
        res.append(((int(m.group(1)), int(m.group(2))), row[1], row[2]))

    return res  # [((年, 月), 合計, レコード数), ...]

# 月ごとの期間（start_month月start_day日からend_month月end_day日まで）収支の取得
# sort - 'both', 'income' or 'outgo'
# e.g. sum_period_monthly(start_month, start_day, end_month, end_day, sort, major, minor, bank, purpose, currency, year=20XX)
@connect_database
def sum_period_monthly(curs, year, start_month=1, start_day=1, end_month=12, end_day=31, sort='both', major_item=None, minor_item=None, bank_name=None, purpose_name=None, currency=None):
    if currency is None:
        from setting_file import get_default
        currency = get_default('currency')

    if end_day == 31:
        end_day = monthrange(year, end_month)[1]

    conditions = _conditions_tuple(' AND ', sort=sort, major_item=major_item, minor_item=minor_item, bank_name=bank_name, purpose_name=purpose_name, currency=currency)

    if conditions[0]:
        sel = 'SELECT STRFTIME(\'%Y%m\', balance_date), SUM(amount), COUNT(amount) FROM balance WHERE ' + conditions[0] + ' AND balance_date BETWEEN ? AND ? GROUP BY STRFTIME(\'%m\', balance_date)'
        curs.execute(sel, (*conditions[1], date(year, start_month, start_day), date(year, end_month, end_day)))
    else:
        sel = 'SELECT STRFTIME(\'%Y%m\', balance_date), SUM(amount), COUNT(amount) FROM balance WHERE balance_date BETWEEN ? AND ? GROUP BY STRFTIME(\'%m\', balance_date)'
        curs.execute(sel, (date(year, start_month, start_day), date(year, end_month, end_day)))

    res = []
    for row in curs.fetchall():
        m = re.match(r'(\d{4})(\d{2})', row[0])
        res.append(((int(m.group(1)), int(m.group(2))), row[1], row[2]))

    return res  # [((年, 月), 合計, レコード数), ...]

# 大項目レコードの更新
# e.g. update_major(major_id, major_item, year=20XX)
@connect_database
def update_major(curs, year, major_id, major_item):
    curs.execute('UPDATE major SET major_item = ? WHERE id = ?', (major_item, major_id))

# 小項目レコードの更新
# e.g. update_minor(minor_id, minor_item, major_item, amount_sign, year=20XX)
@connect_database
def update_minor(curs, year, minor_id, minor_item=None, major_item=None, amount_sign=None):
    if amount_sign == '+' or amount_sign == '-' or amount_sign == '±' or amount_sign is None:
        if not all(arg is None for arg in [minor_item, major_item, amount_sign]):
            conditions = _conditions_tuple(minor_item=minor_item, major_item=major_item, amount_sign=amount_sign)
            conditions[1].append(minor_id)

            upd = 'UPDATE minor SET ' + conditions[0] + ' WHERE id = ?'
            curs.execute(upd, conditions[1])

# 金融機関レコードの更新
# e.g. update_bank(bank_id, bank_name, year=20XX)
@connect_database
def update_bank(curs, year, bank_id, bank_name):
    curs.execute('UPDATE bank SET bank_name = ? WHERE id = ?', (bank_name, bank_id))


# 目的レコードの更新
# e.g. update_purpose(purpose_id, purpose_name, bank_name, year=20XX)
@connect_database
def update_purpose(curs, year, purpose_id, purpose_name=None, bank_name=None):
    if not all(arg is None for arg in [purpose_name, bank_name]):
        conditions = _conditions_tuple(purpose_name=purpose_name, bank_name=bank_name)
        conditions[1].append(purpose_id)

        upd = 'UPDATE purpose SET ' + conditions[0] + ' WHERE id = ?'
        curs.execute(upd, conditions[1])

# 通貨レコードの更新
# e.g. update_currency(currency_id, name, year=20XX)
@connect_database
def update_currency(curs, year, currency_id, name):
    curs.execute('UPDATE currency SET name = ? WHERE id = ?', (name, currency_id))

# 収支表レコードの更新
# e.g. update_balance(balance_id, balance_date, connection, content, major_item, minor_item, bank_name, purpose_name, currency, amount, year=20XX)
@connect_database
def update_balance(curs, year, balance_id, balance_date=None, connection=None, content=None, major_item=None, minor_item=None, bank_name=None, purpose_name=None, currency=None, amount=None):
    if not all(arg is None for arg in [balance_date, connection, content, major_item, minor_item, bank_name, purpose_name, currency, amount]):
        conditions = _conditions_tuple(balance_date=balance_date, connection=connection, content=content, major_item=major_item, minor_item=minor_item, bank_name=bank_name, purpose_name=purpose_name, currency=currency, amount=amount)
        conditions[1].append(balance_id)

        upd = 'UPDATE balance SET ' + conditions[0] + ' WHERE id = ?'
        curs.execute(upd, conditions[1])

# 大項目レコードの削除
# e.g. delete_major(major_id, year=20XX)
@connect_database
def delete_major(curs, year, major_id):
    curs.execute('DELETE FROM major WHERE id = ?', (major_id,))

# 小項目レコードの削除
# e.g. delete_minor(minor_id, year=20XX)
@connect_database
def delete_minor(curs, year, minor_id):
    curs.execute('DELETE FROM minor WHERE id = ?', (minor_id,))

# 金融機関レコードの削除
# e.g. delete_bank(bank_id, year=20XX)
@connect_database
def delete_bank(curs, year, bank_id):
    curs.execute('DELETE FROM bank WHERE id = ?', (bank_id,))

# 目的レコードの削除
# e.g. delete_purpose(purpose_id, year=20XX)
@connect_database
def delete_purpose(curs, year, purpose_id):
    curs.execute('DELETE FROM purpose WHERE id = ?', (purpose_id,))

# 通貨レコードの削除
# e.g. delete_currency(currency_id, year=20XX)
@connect_database
def delete_currency(curs, year, currency_id):
    curs.execute('DELETE FROM currency WHERE id = ?', (currency_id,))

# 収支表レコードの削除
# e.g. delete_balance(balance_id, year=20XX)
@connect_database
def delete_balance(curs, year, balance_id):
    curs.execute('DELETE FROM balance WHERE id = ?', (balance_id,))

#! /usr/bin/env/ python
# -*- coding: utf-8 -*-

from datetime import date
from calendar import monthrange
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import messagebox

from database import *

# 符号文字列エラー
class AmountSignError(Exception):
    def __str__(self):
        return 'amount_sign has to be \'+\', \'-\' or \'±\''

# 収支表入力フレーム
class InputBalanceFrame(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.default_font = font.Font(family='メイリオ', size=11)
        self.option_add('*Font', self.default_font)
        self.pack(expand=1, fill=BOTH, anchor=NW, padx=15, pady=15)
        self.columnconfigure(0, weight=1, uniform='balance')
        self.columnconfigure(1, weight=3, uniform='balance')

        # 日付を表すWidget変数の初期化
        self.input_year = IntVar()
        self.input_year.set(date.today().year)
        self.input_month = IntVar()
        self.input_month.set(date.today().month)
        self.input_day = IntVar()
        self.input_day.set(date.today().day)

        self.initialize_widgets()

    # フレーム内のWidgetを初期化
    def initialize_widgets(self):
        # その他のWidget変数の初期化
        self.input_connection = StringVar()
        self.input_major = StringVar()
        self.input_minor = StringVar()
        self.input_bank_from = StringVar()
        self.input_bank_to = StringVar()
        self.input_purpose_from = StringVar()
        self.input_purpose_to = StringVar()
        self.input_currency = StringVar()
        self.input_amount_sign = StringVar()
        self.input_amount = StringVar()
        self.input_amount.trace('w', self.check_amount)

        # 日付フォーム
        ttk.Label(self, text='日付').grid(column=0, row=0, padx=10, pady=5, sticky=E)
        self.initialize_date_frame()

        # 取引先フォーム
        ttk.Label(self, text='取引先').grid(column=0, row=1, padx=10, pady=5, sticky=E)
        ttk.Entry(self, textvariable=self.input_connection, width=30).grid(column=1, row=1, padx=10, pady=5, sticky=W)

        # 内容フォーム
        ttk.Label(self, text='内容').grid(column=0, row=2, padx=10, pady=5, sticky=E)
        self.input_content = Text(self, height=3, width=30)
        self.input_content.grid(column=1, row=2, padx=10, pady=5, sticky=W)

        # 確定ボタン
        ttk.Button(self, text='確定', width=15, command=self.confirm_balance).grid(column=0, columnspan=2, row=7, padx=10, pady=5)

    # 日付フレームの初期化
    def initialize_date_frame(self, *args):
        if 'date_frame' in self.__dict__.keys():
            self.date_frame.destroy()
        self.date_frame = ttk.Frame(self)
        self.date_frame.grid(column=1, row=0, padx=10, pady=5, sticky=W)
        ttk.OptionMenu(self.date_frame, self.input_year, self.input_year.get(), *range(self.input_year.get()-5, self.input_year.get()+6), command=self.initialize_date_frame).grid(column=0, row=0)
        ttk.Label(self.date_frame, text='年').grid(column=1, row=0)
        ttk.OptionMenu(self.date_frame, self.input_month, self.input_month.get(), *range(1, 13), command=self.set_day_1).grid(column=2, row=0)
        ttk.Label(self.date_frame, text='月').grid(column=3, row=0)
        ttk.OptionMenu(self.date_frame, self.input_day, self.input_day.get(), *range(1, monthrange(self.input_year.get(), self.input_month.get())[1]+1)).grid(column=4, row=0)
        ttk.Label(self.date_frame, text='日 ').grid(column=5, row=0)
        ttk.Button(self.date_frame, text='今日', width=5, command=self.set_today).grid(column=6, row=0)

        # input_year年度のデータベースから情報を取得
        self.major_list = select_major(year=self.input_year.get())
        self.input_major.set(self.major_list[0][1])
        self.bank_list = select_bank(year=self.input_year.get())
        self.input_bank_from.set(self.bank_list[0][1])
        self.input_bank_to.set(self.bank_list[0][1])
        self.currency_list = select_currency(year=self.input_year.get())
        self.input_currency.set(self.currency_list[0][1])

        # 大項目フレームの初期化
        if 'major_frame' in self.__dict__.keys():
            self.major_frame.destroy()
        self.major_frame = ttk.Frame(self)
        self.major_frame.grid(column=0, columnspan=2, row=3, sticky=NSEW)
        self.major_frame.columnconfigure(0, weight=1, uniform='balance')
        self.major_frame.columnconfigure(1, weight=3, uniform='balance')
        ttk.Label(self.major_frame, text='大項目').grid(column=0, row=0, padx=10, pady=5, sticky=E)
        major_om = ttk.OptionMenu(self.major_frame, self.input_major, self.input_major.get(), *[major_tuple[1] for major_tuple in self.major_list], command=self.initialize_minor)
        major_om.config(width=20)
        major_om.grid(column=1, row=0, padx=10, pady=5, sticky=W)

        self.initialize_minor()
        self.initialize_amount()

    # 日付を1日に設定
    def set_day_1(self, *args):
        self.initialize_date_frame()
        ttk.OptionMenu(self.date_frame, self.input_day, 1, *range(1, monthrange(self.input_year.get(), self.input_month.get())[1]+1)).grid(column=4, row=0)
        ttk.Label(self.date_frame, text='日').grid(column=5, row=0)

    # 日付を今日に設定
    def set_today(self):
        self.input_year.set(date.today().year)
        self.input_month.set(date.today().month)
        self.input_day.set(date.today().day)
        self.initialize_date_frame()

    # 小項目フォームの初期化
    def initialize_minor(self, *args):
        # データベースから小項目テーブルを取得
        self.minor_list = select_minor(major_item=self.input_major.get(), year=self.input_year.get())
        self.input_minor.set(self.minor_list[0][1])
        self.input_amount_sign.set(self.minor_list[0][3])

        # 小項目フレームの初期化
        if 'minor_frame' in self.__dict__.keys():
            self.minor_frame.destroy()
        self.minor_frame = ttk.Frame(self)
        self.minor_frame.grid(column=0, columnspan=2, row=4, sticky=NSEW)
        self.minor_frame.columnconfigure(0, weight=1, uniform='balance')
        self.minor_frame.columnconfigure(1, weight=3, uniform='balance')
        ttk.Label(self.minor_frame, text='小項目').grid(column=0, row=0, padx=10, pady=5, sticky=E)
        minor_om = ttk.OptionMenu(self.minor_frame, self.input_minor, self.input_minor.get(), *[minor_tuple[1] for minor_tuple in self.minor_list], command=self.initialize_amount)
        minor_om.config(width=20)
        minor_om.grid(column=1, row=0, padx=10, pady=5, sticky=W)

        self.initialize_amount()

    # 金額フォームの初期化
    def initialize_amount(self, *args):
        # 選択されている小項目の符号を取得
        self.input_amount_sign.set(self.minor_list[[minor_tuple[1] for minor_tuple in self.minor_list].index(self.input_minor.get())][3])

        ttk.Label(self, text='金額').grid(column=0, row=6, padx=10, pady=5, sticky=E)

        # 金額フレームの初期化
        if 'amount_frame' in self.__dict__.keys():
            self.amount_frame.destroy()
        self.amount_frame = ttk.Frame(self)
        self.amount_frame.grid(column=1, row=6, padx=10, pady=5, sticky=W)
        ttk.Label(self.amount_frame, text=self.input_amount_sign.get()).grid(column=0, row=0)
        Spinbox(self.amount_frame, textvariable=self.input_amount, from_=0, to=10**12, increment=1).grid(column=1, row=0)  # 最大1兆
        ttk.OptionMenu(self.amount_frame, self.input_currency, self.input_currency.get(), *[currency[1] for currency in self.currency_list]).grid(column=2, row=0)
        self.initialize_bank_frame()

    # 金融機関フレームの初期化
    def initialize_bank_frame(self, *args):
        if 'bank_frame' in self.__dict__.keys():
            self.bank_frame.destroy()
        self.bank_frame = ttk.Frame(self)
        self.bank_frame.grid(column=0, columnspan=2, row=5, sticky=NSEW)
        self.bank_frame.columnconfigure(0, weight=1, uniform='balance')
        self.bank_frame.columnconfigure(1, weight=3, uniform='balance')
        if self.input_amount_sign.get() == '+':
            ttk.Label(self.bank_frame, text='金融機関').grid(column=0, row=0, padx=10, pady=5, sticky=E)
            bank_to_om = ttk.OptionMenu(self.bank_frame, self.input_bank_to, self.input_bank_to.get(), *[bank_tuple[1] for bank_tuple in self.bank_list], command=self.initialize_purpose_to)
            bank_to_om.config(width=20)
            bank_to_om.grid(column=1, row=0, padx=10, pady=5, sticky=W)
            self.initialize_purpose_to()
        elif self.input_amount_sign.get() == '-':
            ttk.Label(self.bank_frame, text='金融機関').grid(column=0, row=0, padx=10, pady=5, sticky=E)
            bank_from_om = ttk.OptionMenu(self.bank_frame, self.input_bank_from, self.input_bank_from.get(), *[bank_tuple[1] for bank_tuple in self.bank_list], command=self.initialize_purpose_from)
            bank_from_om.config(width=20)
            bank_from_om.grid(column=1, row=0, padx=10, pady=5, sticky=W)
            self.initialize_purpose_from()
        elif self.input_amount_sign.get() == '±':
            ttk.Label(self.bank_frame, text='金融機関').grid(column=0, row=0, padx=10, pady=5, sticky=E)
            bank_from_om = ttk.OptionMenu(self.bank_frame, self.input_bank_from, self.input_bank_from.get(), *[bank_tuple[1] for bank_tuple in self.bank_list], command=self.initialize_purpose_from_to)
            bank_from_om.config(width=20)
            bank_from_om.grid(column=1, row=0, padx=10, pady=5, sticky=W)
            ttk.Label(self.bank_frame, text='↓').grid(column=0, columnspan=2, row=2)
            ttk.Label(self.bank_frame, text='金融機関').grid(column=0, row=3, padx=10, pady=5, sticky=E)
            bank_to_om = ttk.OptionMenu(self.bank_frame, self.input_bank_to, self.input_bank_to.get(), *[bank_tuple[1] for bank_tuple in self.bank_list], command=self.initialize_purpose_from_to)
            bank_to_om.config(width=20)
            bank_to_om.grid(column=1, row=3, padx=10, pady=5, sticky=W)
            self.initialize_purpose_from_to()
        else:
            raise AmountSignError()

    # 収入を登録する目的フォームの初期化
    def initialize_purpose_to(self, *args):
        self.purpose_list_to = select_purpose(bank_name=self.input_bank_to.get(), year=self.input_year.get())
        self.input_purpose_to.set(self.purpose_list_to[0][1])

        ttk.Label(self.bank_frame, text='目的').grid(column=0, row=1, padx=10, pady=5, sticky=E)
        purpose_to_om = ttk.OptionMenu(self.bank_frame, self.input_purpose_to, self.input_purpose_to.get(), *[purpose_tuple[1] for purpose_tuple in self.purpose_list_to])
        purpose_to_om.config(width=20)
        purpose_to_om.grid(column=1, row=1, padx=10, pady=5, sticky=W)

    # 支出を登録する目的フォームの初期化
    def initialize_purpose_from(self, *args):
        self.purpose_list_from = select_purpose(bank_name=self.input_bank_from.get(), year=self.input_year.get())
        self.input_purpose_from.set(self.purpose_list_from[0][1])

        ttk.Label(self.bank_frame, text='目的').grid(column=0, row=1, padx=10, pady=5, sticky=E)
        purpose_from_om = ttk.OptionMenu(self.bank_frame, self.input_purpose_from, self.input_purpose_from.get(), *[purpose_tuple[1] for purpose_tuple in self.purpose_list_from])
        purpose_from_om.config(width=20)
        purpose_from_om.grid(column=1, row=1, padx=10, pady=5, sticky=W)

    # 収入と支出を登録する目的フォームの初期化
    def initialize_purpose_from_to(self, *args):
        self.purpose_list_from = select_purpose(bank_name=self.input_bank_from.get(), year=self.input_year.get())
        self.input_purpose_from.set(self.purpose_list_from[0][1])
        self.purpose_list_to = select_purpose(bank_name=self.input_bank_to.get(), year=self.input_year.get())
        self.input_purpose_to.set(self.purpose_list_to[0][1])

        ttk.Label(self.bank_frame, text='目的').grid(column=0, row=1, padx=10, pady=5, sticky=E)
        purpose_from_om = ttk.OptionMenu(self.bank_frame, self.input_purpose_from, self.input_purpose_from.get(), *[purpose_tuple[1] for purpose_tuple in self.purpose_list_from])
        purpose_from_om.config(width=20)
        purpose_from_om.grid(column=1, row=1, padx=10, pady=5, sticky=W)
        ttk.Label(self.bank_frame, text='目的').grid(column=0, row=4, padx=10, pady=5, sticky=E)
        purpose_to_om = ttk.OptionMenu(self.bank_frame, self.input_purpose_to, self.input_purpose_to.get(), *[purpose_tuple[1] for purpose_tuple in self.purpose_list_to])
        purpose_to_om.config(width=20)
        purpose_to_om.grid(column=1, row=4, padx=10, pady=5, sticky=W)

    # 入力されたデータを登録
    def confirm_balance(self):
        if self.input_amount.get() == '0':
            messagebox.showwarning(title='ecAdmin - 金額エラー', message='金額が 0 です')
            return

        if self.input_connection.get() != '':
            self.connection = self.input_connection.get()
        else:
            self.connection = None

        if self.input_content.get('1.0', 'end-1c') != '':
            self.content = self.input_content.get('1.0', 'end-1c')
        else:
            self.content = None

        if self.input_amount_sign.get() == '+':
            self.amount_to = float(self.input_amount.get())
            insert_balance(
                balance_date=date(self.input_year.get(), self.input_month.get(), self.input_day.get()),
                connection=self.connection,
                content=self.content,
                major_item=self.input_major.get(),
                minor_item=self.input_minor.get(),
                bank_name=self.input_bank_to.get(),
                purpose_name=self.input_purpose_to.get(),
                currency=self.input_currency.get(),
                amount=self.amount_to
            )
        elif self.input_amount_sign.get() == '-':
            self.amount_from = -1 * float(self.input_amount.get())
            insert_balance(
                balance_date=date(self.input_year.get(), self.input_month.get(), self.input_day.get()),
                connection=self.connection,
                content=self.content,
                major_item=self.input_major.get(),
                minor_item=self.input_minor.get(),
                bank_name=self.input_bank_from.get(),
                purpose_name=self.input_purpose_from.get(),
                currency=self.input_currency.get(),
                amount=self.amount_from
            )
        elif self.input_amount_sign.get() == '±':
            self.amount_from = -1 * float(self.input_amount.get())
            self.amount_to = float(self.input_amount.get())
            insert_balance(
                balance_date=date(self.input_year.get(), self.input_month.get(), self.input_day.get()),
                connection=self.connection,
                content=self.content,
                major_item=self.input_major.get(),
                minor_item=self.input_minor.get(),
                bank_name=self.input_bank_from.get(),
                purpose_name=self.input_purpose_from.get(),
                currency=self.input_currency.get(),
                amount=self.amount_from
            )
            insert_balance(
                balance_date=date(self.input_year.get(), self.input_month.get(), self.input_day.get()),
                connection=self.connection,
                content=self.content,
                major_item=self.input_major.get(),
                minor_item=self.input_minor.get(),
                bank_name=self.input_bank_to.get(),
                purpose_name=self.input_purpose_to.get(),
                currency=self.input_currency.get(),
                amount=self.amount_to
            )
        else:
            raise AmountSignError()

        self.initialize_widgets()

    # 金額フォームに入力された値をチェック
    def check_amount(self, *args):
        if not self.input_amount.get() == '':
            try:
                float(self.input_amount.get())
            except ValueError:
                self.input_amount.set('0')

if __name__ == "__main__":
    root = Tk()
    root.title('ecAdmin - 収支表入力')
    root.resizable(FALSE, FALSE)
    InputBalanceFrame(root)
    root.mainloop()

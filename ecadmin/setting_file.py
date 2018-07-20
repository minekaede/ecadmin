#! /usr/bin/env/ python
# -*- coding: utf-8 -*-

import os
import json
import shutil
import configparser

# 親ディレクトリの絶対パスを取得
def get_parent_dir():
    return path.dirname(os.path.abspath(__file__)) + '../'

# setting.iniとsetting.jsonの初期化
def _initialize_setting_file():
    if not os.path.exists('../setting.ini'):
        config = configparser.ConfigParser()
        config['DEFAULT'] = {'currency': 'JPY'}
        with open('../setting.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    if not os.path.exists('../setting.json'):
        shutil.copyfile('default.json', '../setting.json')

# setting.iniの[DEFAULT]からデータを取り出す
def get_default(item):
    config = configparser.ConfigParser()
    config.read('../setting.ini')
    if item in list(config['DEFAULT'].keys()):
        return config['DEFAULT'][item]
    else:
        return None

# setting.jsonからデータを取り出す
def get_json(item):
    with open('../setting.json', 'r', encoding='utf-8') as f:
        json_dict = json.load(f)

    if item in json_dict.keys():
        res = json_dict[item]
    else:
        res = None

    return res

# importされた時の初期化
_initialize_setting_file()

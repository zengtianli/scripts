#!/usr/bin/env python3
"""
编码工具 - 统一的编码规范化和生成功能

提供河流编码、流域编码、堤防编码等水利业务编码处理。
"""

import re

import pandas as pd

from .config import (
    BASIN_NAME_TO_CODE,
    BASIN_NAME_TO_CODE_LONG,
    RIVER_NAME_TO_CODE,
    RIVER_TO_BASIN,
)


def normalize_code(code, to_upper=True):
    """
    规范化编码格式

    Args:
        code: 原始编码（字符串或数字）
        to_upper: 是否转换为大写（默认True）

    Returns:
        str: 规范化后的编码
    """
    if pd.isna(code) or code is None or code == '':
        return ''

    code_str = str(code).strip()
    return code_str.upper() if to_upper else code_str


def get_river_code(river_name, uppercase=True):
    """
    根据河流名称获取编码

    Args:
        river_name: 河流名称
        uppercase: 是否返回大写（默认True，兼容 xlsx_common 行为）

    Returns:
        str: 河流编码，未找到返回空字符串
    """
    if pd.isna(river_name) or river_name == '':
        return ''

    river_name = str(river_name).strip()
    code = RIVER_NAME_TO_CODE.get(river_name, '')
    return code.upper() if uppercase and code else code


def get_basin_code(basin_name, use_long=False):
    """
    根据流域名称获取编码

    Args:
        basin_name: 流域名称
        use_long: 是否使用长版本编码（如 'QTJLY'）

    Returns:
        str: 流域编码，未找到返回空字符串
    """
    if pd.isna(basin_name) or basin_name == '':
        return ''

    basin_name = str(basin_name).strip()
    if use_long:
        return BASIN_NAME_TO_CODE_LONG.get(basin_name, '')
    else:
        return BASIN_NAME_TO_CODE.get(basin_name, '')


def get_basin_name(river_name):
    """
    根据河流名称获取所属流域名称

    Args:
        river_name: 河流名称

    Returns:
        str: 流域名称，未找到返回空字符串
    """
    if pd.isna(river_name) or river_name == '':
        return ''

    river_name = str(river_name).strip()
    return RIVER_TO_BASIN.get(river_name, '')


def generate_dike_code(river_code, dike_name):
    """
    生成堤防编码

    格式: {河流编码}{堤防名称中的数字}D
    例如: "SX1D" (熟溪 + "一堤" -> "1" -> "SX1D")
    """
    if pd.isna(river_code) or river_code == '' or pd.isna(dike_name) or dike_name == '':
        return ''

    dike_number = extract_dike_number(dike_name)
    if dike_number:
        return f"{river_code}{dike_number}D"
    return ''


def extract_dike_number(dike_name):
    """
    从堤防名称中提取数字

    处理中文数字（一、二、三等）和阿拉伯数字
    """
    if pd.isna(dike_name):
        return ''

    dike_name = str(dike_name).strip()

    chinese_to_arabic = {
        '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
        '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'
    }

    for chinese, arabic in chinese_to_arabic.items():
        if chinese in dike_name:
            return arabic

    numbers = re.findall(r'\d+', dike_name)
    if numbers:
        return numbers[0]

    return ''


def natural_sort_key(text):
    """
    自然排序的键函数

    使得 "dm1", "dm2", "dm10" 按正确顺序排列
    """
    if pd.isna(text):
        return []

    text = str(text)
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]

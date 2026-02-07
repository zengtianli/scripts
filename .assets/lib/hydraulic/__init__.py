#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水利领域专用库

提供河流/流域编码映射、编码规范化工具等水利业务功能。
QGIS 相关配置通过 hydraulic.qgis_config 和 hydraulic.qgis_fields 访问。
"""

from .config import (
    # 河流映射
    RIVER_CODE_MAPPING,
    RIVER_NAME_TO_CODE,
    CHINESE_TO_PINYIN,
    RIVER_TO_BASIN,
    BASIN_NAME_TO_CODE,
    BASIN_NAME_TO_CODE_LONG,
    DISTRICT_NAME_TO_CODE,
    COUNTY_TO_CITY,
)

from .code_utils import (
    normalize_code,
    get_river_code,
    get_basin_code,
    get_basin_name,
    generate_dike_code,
    extract_dike_number,
    natural_sort_key,
)

__all__ = [
    # Config
    'RIVER_CODE_MAPPING',
    'RIVER_NAME_TO_CODE',
    'CHINESE_TO_PINYIN',
    'RIVER_TO_BASIN',
    'BASIN_NAME_TO_CODE',
    'BASIN_NAME_TO_CODE_LONG',
    'DISTRICT_NAME_TO_CODE',
    'COUNTY_TO_CITY',

    # Code Utils
    'normalize_code',
    'get_river_code',
    'get_basin_code',
    'get_basin_name',
    'generate_dike_code',
    'extract_dike_number',
    'natural_sort_key',
]

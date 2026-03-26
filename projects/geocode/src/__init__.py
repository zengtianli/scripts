# -*- coding: utf-8 -*-
"""
地理编码工具集

基于高德地图 API 的坐标与地址转换工具

模块:
    - reverse_geocode: 逆地理编码（经纬度 → 地址）
    - geocode_by_address: 正向编码（地址 → 经纬度）
    - search_by_company: 企业搜索（公司名 → 位置）
    - compare_results: 结果比对
"""

from .reverse_geocode import reverse_geocode, wgs84_to_gcj02
from .geocode_by_address import geocode_by_address
from .search_by_company import search_by_company

__all__ = [
    'reverse_geocode',
    'geocode_by_address', 
    'search_by_company',
    'wgs84_to_gcj02',
]


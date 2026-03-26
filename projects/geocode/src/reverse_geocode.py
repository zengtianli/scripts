#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逆地理编码工具 - 经纬度 → 地址
使用高德地图 API 将经纬度坐标转换为详细地址

支持 WGS-84 坐标自动转换为 GCJ-02（高德坐标系）

用法:
    python reverse_geocode.py <输入CSV> <输出CSV> [--gcj02]
    
    默认假设输入是 WGS-84 坐标，自动转换
    加 --gcj02 表示输入已经是 GCJ-02，跳过转换

输入CSV需要包含 '经度'/'JD'/'lng' 和 '纬度'/'WD'/'lat' 列

环境变量:
    AMAP_API_KEY: 高德地图 API Key
"""

import os
import time
import sys
import math
import csv
import requests
from typing import Dict, Any, Tuple

AMAP_REGEO_URL = "https://restapi.amap.com/v3/geocode/regeo"


# ============================================================
# WGS-84 → GCJ-02 坐标转换
# ============================================================

def _transform_lat(lng: float, lat: float) -> float:
    """纬度转换辅助函数"""
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 *
            math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * math.pi) + 40.0 *
            math.sin(lat / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * math.pi) + 320 *
            math.sin(lat * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(lng: float, lat: float) -> float:
    """经度转换辅助函数"""
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * math.pi) + 20.0 *
            math.sin(2.0 * lng * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * math.pi) + 40.0 *
            math.sin(lng / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * math.pi) + 300.0 *
            math.sin(lng / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def _out_of_china(lng: float, lat: float) -> bool:
    """判断是否在中国境外"""
    return not (73.66 < lng < 135.05 and 3.86 < lat < 53.55)


def wgs84_to_gcj02(lng: float, lat: float) -> Tuple[float, float]:
    """
    WGS-84 坐标转 GCJ-02（火星坐标/高德坐标）
    
    参数:
        lng: WGS-84 经度
        lat: WGS-84 纬度
    
    返回:
        (gcj02_lng, gcj02_lat): GCJ-02 坐标
    """
    if _out_of_china(lng, lat):
        return lng, lat
    
    a = 6378245.0  # 长半轴
    ee = 0.00669342162296594323  # 偏心率平方
    
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
    
    gcj_lng = lng + dlng
    gcj_lat = lat + dlat
    
    return gcj_lng, gcj_lat


def reverse_geocode(lng: float, lat: float, api_key: str) -> Dict[str, Any]:
    """
    调用高德逆地理编码 API，把经纬度转换为地址。
    
    参数:
        lng: 经度 (GCJ-02坐标系)
        lat: 纬度 (GCJ-02坐标系)
        api_key: 高德 API Key
    
    返回:
        {
            "lng": float,
            "lat": float,
            "formatted_address": str,  # 格式化地址
            "province": str,           # 省
            "city": str,               # 市
            "district": str,           # 区/县
            "township": str,           # 乡镇/街道
            "street": str,             # 街道名
            "number": str,             # 门牌号
            "adcode": str,             # 区域编码
            "description": str,        # 位置描述（距离最近的POI等）
            "error": str 或 None
        }
    """
    params = {
        "key": api_key,
        "location": f"{lng},{lat}",
        "extensions": "base",  # base返回基本信息，all返回详细信息
        "output": "json",
    }

    try:
        resp = requests.get(AMAP_REGEO_URL, params=params, timeout=10)
    except requests.RequestException as e:
        return {
            "lng": lng,
            "lat": lat,
            "formatted_address": None,
            "province": None,
            "city": None,
            "district": None,
            "township": None,
            "street": None,
            "number": None,
            "adcode": None,
            "description": None,
            "error": f"network_error: {e}",
        }

    if resp.status_code != 200:
        return {
            "lng": lng,
            "lat": lat,
            "formatted_address": None,
            "province": None,
            "city": None,
            "district": None,
            "township": None,
            "street": None,
            "number": None,
            "adcode": None,
            "description": None,
            "error": f"http_status_{resp.status_code}",
        }

    data = resp.json()
    if data.get("status") != "1":
        return {
            "lng": lng,
            "lat": lat,
            "formatted_address": None,
            "province": None,
            "city": None,
            "district": None,
            "township": None,
            "street": None,
            "number": None,
            "adcode": None,
            "description": None,
            "error": f"amap_error: {data.get('info', 'unknown')}",
        }

    regeocode = data.get("regeocode", {})
    if not regeocode:
        return {
            "lng": lng,
            "lat": lat,
            "formatted_address": None,
            "province": None,
            "city": None,
            "district": None,
            "township": None,
            "street": None,
            "number": None,
            "adcode": None,
            "description": None,
            "error": "no_result",
        }

    addr_component = regeocode.get("addressComponent", {})
    
    # 处理可能为空列表的字段
    def safe_get(obj, key, default=""):
        val = obj.get(key, default)
        if isinstance(val, list):
            return ""
        return val if val else default

    return {
        "lng": lng,
        "lat": lat,
        "formatted_address": regeocode.get("formatted_address", ""),
        "province": safe_get(addr_component, "province"),
        "city": safe_get(addr_component, "city"),
        "district": safe_get(addr_component, "district"),
        "township": safe_get(addr_component, "township"),
        "street": safe_get(addr_component.get("streetNumber", {}), "street"),
        "number": safe_get(addr_component.get("streetNumber", {}), "number"),
        "adcode": safe_get(addr_component, "adcode"),
        "description": regeocode.get("formatted_address", ""),
        "error": None,
    }


def reverse_geocode_single(lng: float, lat: float, api_key: str, convert_wgs84: bool = True) -> None:
    """单个坐标查询并打印结果"""
    print(f"\n原始坐标 (WGS-84): ({lng}, {lat})")
    
    if convert_wgs84:
        gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
        print(f"转换坐标 (GCJ-02): ({gcj_lng:.6f}, {gcj_lat:.6f})")
    else:
        gcj_lng, gcj_lat = lng, lat
    
    print("-" * 50)
    
    result = reverse_geocode(gcj_lng, gcj_lat, api_key)
    
    if result.get("error"):
        print(f"❌ 错误: {result['error']}")
    else:
        print(f"📍 格式化地址: {result['formatted_address']}")
        print(f"   省份: {result['province']}")
        print(f"   城市: {result['city']}")
        print(f"   区县: {result['district']}")
        print(f"   乡镇/街道: {result['township']}")
        if result['street']:
            print(f"   街道: {result['street']} {result['number']}")
        print(f"   区域编码: {result['adcode']}")


def process_csv(input_file: str, output_file: str, api_key: str, convert_wgs84: bool = True) -> None:
    """
    批量处理CSV文件
    
    参数:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径
        api_key: 高德API Key
        convert_wgs84: 是否将 WGS-84 转换为 GCJ-02（默认True）
    """
    rows = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    coord_type = "WGS-84 → GCJ-02" if convert_wgs84 else "GCJ-02（不转换）"
    print(f"读取到 {len(rows)} 条记录")
    print(f"坐标模式: {coord_type}")
    print(f"开始逆地理编码...\n")

    for i, row in enumerate(rows, 1):
        # 尝试不同的列名
        lng = row.get('经度') or row.get('JD') or row.get('lng') or row.get('longitude') or ''
        lat = row.get('纬度') or row.get('WD') or row.get('lat') or row.get('latitude') or ''
        
        if lng and lat:
            try:
                lng_f = float(lng)
                lat_f = float(lat)
            except ValueError:
                print(f"处理 {i}/{len(rows)}: ⚠️ 坐标格式错误 ({lng}, {lat})")
                row['地址'] = ''
                continue
            
            # WGS-84 → GCJ-02 坐标转换
            if convert_wgs84:
                gcj_lng, gcj_lat = wgs84_to_gcj02(lng_f, lat_f)
                row['GCJ02_经度'] = f"{gcj_lng:.6f}"
                row['GCJ02_纬度'] = f"{gcj_lat:.6f}"
                print(f"处理 {i}/{len(rows)}: WGS84({lng_f:.6f}, {lat_f:.6f}) → GCJ02({gcj_lng:.6f}, {gcj_lat:.6f})")
            else:
                gcj_lng, gcj_lat = lng_f, lat_f
                print(f"处理 {i}/{len(rows)}: ({lng_f:.6f}, {lat_f:.6f})")
            
            # 添加重试机制
            max_retries = 3
            retry_count = 0
            result = None
            
            while retry_count < max_retries:
                result = reverse_geocode(gcj_lng, gcj_lat, api_key)
                
                if result.get('error') and 'EXCEEDED_THE_LIMIT' in result.get('error', ''):
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 * retry_count
                        print(f"  ⏳ API频率限制，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                    else:
                        print(f"  ❌ 重试失败: {result.get('error')}")
                else:
                    break
            
            if result and not result.get('error'):
                print(f"  ✓ {result['formatted_address']}")
                row['地址'] = result['formatted_address']
                row['省'] = result['province']
                row['市'] = result['city']
                row['区县'] = result['district']
            else:
                if result and result.get('error'):
                    print(f"  ❌ {result.get('error')}")
                row['地址'] = ''
                row['省'] = ''
                row['市'] = ''
                row['区县'] = ''
            
            time.sleep(0.3)  # 速率限制
        else:
            row['地址'] = ''
            row['省'] = ''
            row['市'] = ''
            row['区县'] = ''
            if convert_wgs84:
                row['GCJ02_经度'] = ''
                row['GCJ02_纬度'] = ''

    # 写入输出CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(f"\n✅ 完成！结果已保存到 {output_file}")


def main():
    api_key = os.getenv("AMAP_API_KEY")
    
    # 检查是否有 --gcj02 参数（跳过坐标转换）
    convert_wgs84 = "--gcj02" not in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--gcj02"]
    
    # 交互式单点查询模式: python reverse_geocode.py 120.15 30.27
    if len(args) == 2 and '.' in args[0] and '.' in args[1]:
        try:
            lng = float(args[0])
            lat = float(args[1])
            if not api_key:
                print("请设置环境变量 AMAP_API_KEY")
                sys.exit(1)
            reverse_geocode_single(lng, lat, api_key, convert_wgs84)
            return
        except ValueError:
            pass
    
    # CSV批量处理模式
    if len(args) < 2:
        print("=" * 60)
        print("逆地理编码工具 - 经纬度 → 地址（支持 WGS-84 自动转换）")
        print("=" * 60)
        print("\n用法:")
        print("  单点查询: python reverse_geocode.py <经度> <纬度>")
        print("  批量处理: python reverse_geocode.py <输入CSV> <输出CSV>")
        print("\n参数:")
        print("  --gcj02    输入已经是 GCJ-02 坐标，跳过转换")
        print("             （默认假设输入是 WGS-84，自动转换）")
        print("\n示例:")
        print("  # WGS-84 坐标（默认，自动转换）")
        print("  python reverse_geocode.py 120.1551 30.2741")
        print("  python reverse_geocode.py input.csv output.csv")
        print("")
        print("  # 已经是 GCJ-02 坐标，跳过转换")
        print("  python reverse_geocode.py input.csv output.csv --gcj02")
        print("\n输入CSV需包含 '经度'/'JD'/'lng' 和 '纬度'/'WD'/'lat' 列")
        print("\n环境变量: AMAP_API_KEY（高德地图 API Key）")
        sys.exit(1)

    input_file = args[0]
    output_file = args[1]
    
    if not api_key:
        if len(args) >= 3:
            api_key = args[2]
        else:
            print("请通过环境变量 AMAP_API_KEY 或命令行参数提供高德 API Key")
            sys.exit(1)

    process_csv(input_file, output_file, api_key, convert_wgs84)


if __name__ == "__main__":
    main()


# filename: search_by_company.py
import os
import time
import sys
import json
import csv
import requests
from typing import List, Dict, Any, Optional

AMAP_POI_SEARCH_URL = "https://restapi.amap.com/v3/place/text"
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"

def geocode_as_address(company_name: str, api_key: str, city: Optional[str] = None) -> Dict[str, Any]:
    """
    备用方案：把公司名当作地址进行地理编码
    """
    params = {
        "key": api_key,
        "address": company_name,
        "batch": "false",
        "city": city if city else "",
    }

    try:
        resp = requests.get(AMAP_GEOCODE_URL, params=params, timeout=10)
    except requests.RequestException as e:
        return {
            "company_name": company_name,
            "address": None,
            "location": None,
            "lng": None,
            "lat": None,
            "error": f"network_error: {e}",
        }

    if resp.status_code != 200:
        return {
            "company_name": company_name,
            "address": None,
            "location": None,
            "lng": None,
            "lat": None,
            "error": f"http_status_{resp.status_code}",
        }

    data = resp.json()
    if data.get("status") != "1":
        return {
            "company_name": company_name,
            "address": None,
            "location": None,
            "lng": None,
            "lat": None,
            "error": f"amap_error: {data.get('info', 'unknown')}",
        }

    geocodes = data.get("geocodes", [])
    if not geocodes:
        return {
            "company_name": company_name,
            "address": None,
            "location": None,
            "lng": None,
            "lat": None,
            "error": "no_result",
        }

    g = geocodes[0]
    location = g.get("location")
    lng = lat = None
    if location and "," in location:
        try:
            lng_str, lat_str = location.split(",")
            lng = float(lng_str)
            lat = float(lat_str)
        except ValueError:
            pass

    # 构造详细地址
    province = g.get("province", "")
    city_name = g.get("city", "")
    district = g.get("district", "")
    street = g.get("street", "")
    number = g.get("number", "")
    address = f"{province}{city_name}{district}{street}{number}".strip()

    return {
        "company_name": company_name,
        "address": address if address else g.get("formatted_address"),
        "location": location,
        "lng": lng,
        "lat": lat,
        "error": None,
    }

def search_company(company_name: str, api_key: str, city: Optional[str] = None) -> Dict[str, Any]:
    """
    调用高德POI搜索API，通过公司名称查找地址和经纬度。
    返回:
      {
        "company_name": 原始公司名,
        "address": str 或 None,    # 详细地址
        "location": "lng,lat" 或 None,
        "lng": float 或 None,
        "lat": float 或 None,
        "province": str 或 None,   # 省份
        "city": str 或 None,       # 城市
        "district": str 或 None,   # 区县
        "adcode": str 或 None,     # 区域编码
        "type": str 或 None,       # POI类型
        "raw": dict                # 原始返回
      }
    """
    params = {
        "key": api_key,
        "keywords": company_name,
        "types": "120000|190000",  # 商务住宅|公司企业
        "city": city if city else "",
        "citylimit": "true" if city else "false",  # 是否限制在指定城市
        "output": "json",
        "extensions": "base",
    }

    try:
        resp = requests.get(AMAP_POI_SEARCH_URL, params=params, timeout=10)
    except requests.RequestException as e:
        return {
            "company_name": company_name,
            "address": None,
            "location": None,
            "lng": None,
            "lat": None,
            "province": None,
            "city": None,
            "district": None,
            "adcode": None,
            "type": None,
            "error": f"network_error: {e}",
            "raw": None,
        }

    if resp.status_code != 200:
        return {
            "company_name": company_name,
            "address": None,
            "location": None,
            "lng": None,
            "lat": None,
            "province": None,
            "city": None,
            "district": None,
            "adcode": None,
            "type": None,
            "error": f"http_status_{resp.status_code}",
            "raw": None,
        }

    data = resp.json()
    if data.get("status") != "1":
        return {
            "company_name": company_name,
            "address": None,
            "location": None,
            "lng": None,
            "lat": None,
            "province": None,
            "city": None,
            "district": None,
            "adcode": None,
            "type": None,
            "error": f"amap_error: {data.get('info', 'unknown')}",
            "raw": data,
        }

    pois = data.get("pois", [])
    if not pois:
        return {
            "company_name": company_name,
            "address": None,
            "location": None,
            "lng": None,
            "lat": None,
            "province": None,
            "city": None,
            "district": None,
            "adcode": None,
            "type": None,
            "error": "no_result",
            "raw": data,
        }

    # 取第一条匹配结果
    poi = pois[0]
    location = poi.get("location")
    lng = lat = None
    if location and "," in location:
        try:
            lng_str, lat_str = location.split(",")
            lng = float(lng_str)
            lat = float(lat_str)
        except ValueError:
            pass

    # 拼接完整地址：省+市+区+详细地址
    province = poi.get("pname", "")
    city = poi.get("cityname", "")
    district = poi.get("adname", "")
    detail_address = poi.get("address", "")
    
    # 组合完整地址（去掉重复部分）
    full_address_parts = []
    if province and province not in ["", "[]"]:
        full_address_parts.append(province)
    if city and city not in ["", "[]"] and city != province:
        full_address_parts.append(city)
    if district and district not in ["", "[]"] and district != city:
        full_address_parts.append(district)
    if detail_address and detail_address not in ["", "[]"]:
        full_address_parts.append(detail_address)
    
    full_address = "".join(full_address_parts) if full_address_parts else None

    return {
        "company_name": company_name,
        "address": full_address,  # 完整地址
        "location": location,
        "lng": lng,
        "lat": lat,
        "province": province,
        "city": city,
        "district": district,
        "adcode": poi.get("adcode"),
        "type": poi.get("type"),
        "raw": poi,
    }

def main():
    # 读取 API Key：优先环境变量 AMAP_API_KEY，其次命令行参数
    api_key = os.getenv("AMAP_API_KEY")
    if not api_key:
        if len(sys.argv) >= 4:
            api_key = sys.argv[3]
        else:
            print("请通过环境变量 AMAP_API_KEY 或命令行参数提供高德 API Key。例如：")
            print("  AMAP_API_KEY=你的key python search_by_company.py input.csv output.csv")
            print("或")
            print("  python search_by_company.py input.csv output.csv 你的key")
            sys.exit(1)

    # 读取输入输出文件名
    if len(sys.argv) < 3:
        print("用法: python search_by_company.py <输入CSV文件> <输出CSV文件> [API_KEY]")
        print("示例: python search_by_company.py companies.csv output.csv")
        print("\n输入CSV需要包含'公司名称'或'用水户名称'列")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # 为提高匹配准确度，给出 city_hint（可选）
    city_hint = "衢州市"

    # 读取CSV文件（使用utf-8-sig自动处理BOM）
    rows = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"读取到 {len(rows)} 条记录，开始搜索公司信息...")

    # 对每个公司名进行搜索
    for i, row in enumerate(rows, 1):
        # 尝试不同的列名（添加更多常见列名）
        company_name = (row.get('公司名称') or row.get('用水户名称') or 
                       row.get('企业名称') or row.get('QYMC') or 
                       row.get('名称') or row.get('单位名称') or '')
        
        if company_name:
            print(f"处理 {i}/{len(rows)}: {company_name}")
            
            # 添加重试机制
            max_retries = 3
            retry_count = 0
            result = None
            
            while retry_count < max_retries:
                result = search_company(company_name.strip(), api_key, city=city_hint)
                
                # 如果遇到频率限制，等待后重试
                if result.get('error') and 'EXCEEDED_THE_LIMIT' in result.get('error', ''):
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 * retry_count  # 递增等待时间
                        print(f"  ⏳ API频率限制，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                    else:
                        print(f"  ❌ 重试失败: {result.get('error')}")
                else:
                    break
            
            # 调试：显示返回结果
            if result:
                if result.get('error') and 'EXCEEDED_THE_LIMIT' not in result.get('error', ''):
                    print(f"  ❌ 错误: {result.get('error')}")
                    row['地址'] = ''
                    row['经度'] = ''
                    row['纬度'] = ''
                elif result['lng'] and result['lat']:
                    print(f"  ✓ 地址: {result['address']}")
                    print(f"  ✓ 经度: {result['lng']}, 纬度: {result['lat']}")
                    row['地址'] = result['address'] if result['address'] else ''
                    row['经度'] = result['lng'] if result['lng'] is not None else ''
                    row['纬度'] = result['lat'] if result['lat'] is not None else ''
                else:
                    print(f"  ⚠️  未找到该公司")
                    row['地址'] = ''
                    row['经度'] = ''
                    row['纬度'] = ''
            else:
                row['地址'] = ''
                row['经度'] = ''
                row['纬度'] = ''
            
            time.sleep(0.5)  # 降低请求频率
        else:
            row['地址'] = ''
            row['经度'] = ''
            row['纬度'] = ''

    # 写入输出CSV文件
    if rows:
        fieldnames = list(rows[0].keys())
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(f"\n完成！结果已保存到 {output_file}")

if __name__ == "__main__":
    main()


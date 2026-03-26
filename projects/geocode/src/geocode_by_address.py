# filename: geocode_amap.py
import os
import time
import sys
import json
import csv
import requests
from typing import List, Dict, Any, Optional

AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"

def geocode_address(address: str, api_key: str, city: Optional[str] = None) -> Dict[str, Any]:
    """
    调用高德地理编码 API，把地址转换为经纬度（GCJ-02）。
    返回:
      {
        "address": 原始地址,
        "location": "lng,lat" 或 None,
        "lng": float 或 None,
        "lat": float 或 None,
        "level": str 或 None,   # 高德返回的匹配级别，如 "门牌号"、"道路" 等
        "confidence": int 或 None,
        "precise": int 或 None, # 1 精确 0 不精确
        "citycode": str 或 None,
        "adcode": str 或 None,
        "raw": dict              # 原始返回
      }
    """
    params = {
        "key": api_key,
        "address": address,
        "batch": "false",
        "sig": "",  # 如开启数字签名可用；默认不需要
    }
    # 提高匹配准确度：限定到市或省（本例为浙江省衢州市）
    # 高德支持 "city" 参数：可以是城市名或 adcode。这里传 city 名字。
    if city:
        params["city"] = city

    try:
        resp = requests.get(AMAP_GEOCODE_URL, params=params, timeout=10)
    except requests.RequestException as e:
        return {
            "address": address,
            "location": None,
            "lng": None,
            "lat": None,
            "level": None,
            "confidence": None,
            "precise": None,
            "citycode": None,
            "adcode": None,
            "error": f"network_error: {e}",
            "raw": None,
        }

    if resp.status_code != 200:
        return {
            "address": address,
            "location": None,
            "lng": None,
            "lat": None,
            "level": None,
            "confidence": None,
            "precise": None,
            "citycode": None,
            "adcode": None,
            "error": f"http_status_{resp.status_code}",
            "raw": None,
        }

    data = resp.json()
    if data.get("status") != "1":
        return {
            "address": address,
            "location": None,
            "lng": None,
            "lat": None,
            "level": None,
            "confidence": None,
            "precise": None,
            "citycode": None,
            "adcode": None,
            "error": f"amap_error: {data.get('info', 'unknown')}",
            "raw": data,
        }

    geocodes = data.get("geocodes", [])
    if not geocodes:
        return {
            "address": address,
            "location": None,
            "lng": None,
            "lat": None,
            "level": None,
            "confidence": None,
            "precise": None,
            "citycode": None,
            "adcode": None,
            "error": "no_result",
            "raw": data,
        }

    g = geocodes[0]  # 取第一条匹配
    location = g.get("location")
    lng = lat = None
    if location and "," in location:
        try:
            lng_str, lat_str = location.split(",")
            lng = float(lng_str)
            lat = float(lat_str)
        except ValueError:
            pass

    return {
        "address": address,
        "location": location,
        "lng": lng,
        "lat": lat,
        "level": g.get("level"),
        "confidence": int(g.get("confidence")) if g.get("confidence") and g.get("confidence").isdigit() else None,
        "precise": int(g.get("precise")) if g.get("precise") and str(g.get("precise")).isdigit() else None,
        "citycode": g.get("citycode"),
        "adcode": g.get("adcode"),
        "raw": g,
    }

def batch_geocode(addresses: List[str], api_key: str, city_hint: Optional[str] = None, sleep_sec: float = 0.2) -> List[Dict[str, Any]]:
    results = []
    for addr in addresses:
        res = geocode_address(addr.strip(), api_key, city=city_hint)
        results.append(res)
        time.sleep(sleep_sec)  # 简单速率限制
    return results

def main():
    # 读取 API Key：优先环境变量 AMAP_API_KEY，其次命令行参数
    api_key = os.getenv("AMAP_API_KEY")
    if not api_key:
        if len(sys.argv) >= 3:
            api_key = sys.argv[2]
        else:
            print("请通过环境变量 AMAP_API_KEY 或命令行参数提供高德 API Key。例如：")
            print("  AMAP_API_KEY=你的key python geocode.py input.csv output.csv")
            print("或")
            print("  python geocode.py input.csv output.csv 你的key")
            sys.exit(1)

    # 读取输入输出文件名
    if len(sys.argv) < 3:
        print("用法: python geocode.py <输入CSV文件> <输出CSV文件> [API_KEY]")
        print("示例: python geocode.py Book1.csv output.csv")
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

    print(f"读取到 {len(rows)} 条记录，开始地理编码...")

    # 对每条地址进行地理编码
    for i, row in enumerate(rows, 1):
        address = row.get('地址', '')
        if address:
            print(f"处理 {i}/{len(rows)}: {address}")
            
            # 添加重试机制
            max_retries = 3
            retry_count = 0
            result = None
            
            while retry_count < max_retries:
                result = geocode_address(address.strip(), api_key, city=city_hint)
                
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
                elif result['lng'] and result['lat']:
                    print(f"  ✓ 经度: {result['lng']}, 纬度: {result['lat']}")
                else:
                    print(f"  ⚠️  未获取到坐标")
                    print(f"  原始返回: {json.dumps(result.get('raw', {}), ensure_ascii=False)}")
                
                row['经度'] = result['lng'] if result['lng'] is not None else ''
                row['纬度'] = result['lat'] if result['lat'] is not None else ''
            else:
                row['经度'] = ''
                row['纬度'] = ''
            
            time.sleep(0.5)  # 增加到0.5秒，降低请求频率
        else:
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


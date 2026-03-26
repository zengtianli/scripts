#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv

# 读取新结果
new_data = {}
with open('坐标有误_新结果.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        company = row['QYMC'].strip()
        new_data[company] = {
            'address': row['地址'],
            'lng': row['经度'],
            'lat': row['纬度']
        }

# 读取旧结果
old_data = {}
with open('b.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        company = row['用水户名称'].strip()
        old_data[company] = {
            'address': row['地址'],
            'lng': row['经度'],
            'lat': row['纬度']
        }

# 对比结果
print("=" * 100)
print(f"{'公司名称':<40} {'状态':<10} {'旧经度':<12} {'新经度':<12} {'旧纬度':<12} {'新纬度':<12}")
print("=" * 100)

changed_count = 0
unchanged_count = 0
new_found_count = 0
not_found_count = 0

for company in new_data:
    new_info = new_data[company]
    
    if company in old_data:
        old_info = old_data[company]
        
        # 检查是否有变化
        if old_info['lng'] != new_info['lng'] or old_info['lat'] != new_info['lat']:
            status = "✓ 已更新"
            changed_count += 1
            print(f"{company:<40} {status:<10} {old_info['lng']:<12} {new_info['lng']:<12} {old_info['lat']:<12} {new_info['lat']:<12}")
        else:
            status = "  未变化"
            unchanged_count += 1
    else:
        # 旧数据中没有
        if new_info['lng'] and new_info['lat']:
            status = "★ 新获取"
            new_found_count += 1
            print(f"{company:<40} {status:<10} {'无':<12} {new_info['lng']:<12} {'无':<12} {new_info['lat']:<12}")
        else:
            status = "✗ 未找到"
            not_found_count += 1
            print(f"{company:<40} {status:<10}")

print("=" * 100)
print(f"\n统计结果：")
print(f"  已更新坐标：{changed_count} 个")
print(f"  坐标未变化：{unchanged_count} 个")
print(f"  新获取坐标：{new_found_count} 个")
print(f"  仍未找到：{not_found_count} 个")
print(f"  总计：{len(new_data)} 个公司")


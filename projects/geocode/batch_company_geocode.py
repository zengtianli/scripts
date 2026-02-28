#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量企业坐标查询（带去重优化）

功能：
- 读取 xlsx，提取唯一名称
- 批量查询坐标（每个名称只查一次）
- 结果映射回原表
- 输出 xlsx

用法：
    python batch_company_geocode.py <输入.xlsx> <输出.xlsx>

来源：有税号用户用水量报表坐标查询需求
"""
import os
import sys
import time
import pandas as pd
from pathlib import Path

# 添加 src 目录
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from search_by_company import search_company


def log(msg):
    """实时输出"""
    print(msg, flush=True)


def batch_geocode_with_dedup(input_file: str, output_file: str):
    """带去重的批量企业坐标查询"""
    
    # 检查 API Key
    api_key = os.getenv('AMAP_API_KEY')
    if not api_key:
        log("❌ 请设置环境变量 AMAP_API_KEY")
        sys.exit(1)
    
    # 读取数据
    log(f"📖 读取文件: {input_file}")
    df = pd.read_excel(input_file)
    total_rows = len(df)
    log(f"   总行数: {total_rows}")
    
    # 识别名称列
    name_col = None
    for col in ['名称', '公司名称', '用水户名称', '企业名称', 'QYMC', '单位名称']:
        if col in df.columns:
            name_col = col
            break
    
    if not name_col:
        log("❌ 未找到名称列（名称/公司名称/用水户名称/企业名称）")
        sys.exit(1)
    
    log(f"   名称列: {name_col}")
    
    # 提取唯一名称
    unique_names = df[name_col].dropna().unique().tolist()
    unique_count = len(unique_names)
    log(f"   唯一名称数: {unique_count}（节省 {total_rows - unique_count} 次查询）")
    
    # 预计时间
    est_minutes = unique_count * 0.5 / 60
    log(f"   预计时间: {est_minutes:.1f} 分钟")
    log("")
    
    # 批量查询唯一名称
    log("🔍 开始查询...")
    results = {}  # name -> {地址, 经度, 纬度}
    success_count = 0
    fail_count = 0
    
    for i, name in enumerate(unique_names, 1):
        name = str(name).strip()
        if not name:
            continue
        
        # 进度显示（每 50 条或最后一条）
        if i % 50 == 0 or i == unique_count:
            log(f"   进度: {i}/{unique_count} ({i/unique_count*100:.1f}%)")
        
        # 查询（不限制城市）
        max_retries = 3
        retry_count = 0
        result = None
        
        while retry_count < max_retries:
            result = search_company(name, api_key, city=None)
            
            # 频率限制重试
            if result.get('error') and 'EXCEEDED_THE_LIMIT' in str(result.get('error', '')):
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 * retry_count
                    log(f"   ⏳ API 限频，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                continue
            break
        
        # 记录结果
        if result and result.get('lng') and result.get('lat'):
            results[name] = {
                '地址': result.get('address', ''),
                '经度': result['lng'],
                '纬度': result['lat']
            }
            success_count += 1
        else:
            results[name] = {
                '地址': '',
                '经度': '',
                '纬度': ''
            }
            fail_count += 1
        
        time.sleep(0.5)  # API 频率控制
    
    log("")
    log(f"✅ 查询完成: 成功 {success_count}, 失败 {fail_count}")
    log(f"   成功率: {success_count/unique_count*100:.1f}%")
    
    # 映射回原表
    log("")
    log("📝 映射结果到原表...")
    
    df['地址'] = df[name_col].apply(lambda x: results.get(str(x).strip(), {}).get('地址', ''))
    df['经度'] = df[name_col].apply(lambda x: results.get(str(x).strip(), {}).get('经度', ''))
    df['纬度'] = df[name_col].apply(lambda x: results.get(str(x).strip(), {}).get('纬度', ''))
    
    # 保存
    df.to_excel(output_file, index=False)
    log(f"💾 已保存: {output_file}")
    
    # 统计
    has_coord = df['经度'].apply(lambda x: x != '' and pd.notna(x)).sum()
    log(f"   有坐标的行数: {has_coord}/{total_rows} ({has_coord/total_rows*100:.1f}%)")


def main():
    if len(sys.argv) < 3:
        log("用法: python batch_company_geocode.py <输入.xlsx> <输出.xlsx>")
        log("示例: python batch_company_geocode.py 有税号用户用水量报表.xlsx 有税号用户坐标结果.xlsx")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        log(f"❌ 文件不存在: {input_file}")
        sys.exit(1)
    
    batch_geocode_with_dedup(input_file, output_file)


if __name__ == "__main__":
    main()

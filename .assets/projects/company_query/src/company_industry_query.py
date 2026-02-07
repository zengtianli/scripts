# -*- coding: utf-8 -*-
"""
企业行业信息查询工具
使用天眼查API查询企业行业类别
"""

import pandas as pd
import requests
import time
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
import config


class CompanyIndustryQuery:
    """企业行业查询类"""
    
    def __init__(self):
        """初始化"""
        self.api_token = config.TIANYANCHA_API_TOKEN
        self.base_url = config.TIANYANCHA_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.api_token
        })
        # 禁用代理，避免连接问题
        self.session.trust_env = False
        
        # 统计信息
        self.stats = {
            "total": 0,           # 总数
            "api_success": 0,     # API查询成功
            "api_failed": 0,      # API查询失败
            "institution": 0,     # 事业单位识别
            "empty": 0            # 空行
        }
    
    def identify_institution(self, company_name: str) -> Optional[str]:
        """
        智能识别事业单位类型
        
        Args:
            company_name: 企业/单位名称
            
        Returns:
            如果是事业单位，返回行业类别；否则返回None
        """
        if not company_name or company_name.strip() == "":
            return None
            
        for industry, keywords in config.INSTITUTION_INDUSTRY_MAP.items():
            for keyword in keywords:
                if keyword in company_name:
                    return industry
        
        return None
    
    def query_tianyancha_api(self, company_name: str) -> Tuple[Optional[str], str, dict]:
        """
        调用天眼查API查询企业信息
        
        Args:
            company_name: 企业名称
            
        Returns:
            (行业类别, 查询状态, 完整数据)
        """
        params = {
            "keyword": company_name
        }
        
        for attempt in range(config.MAX_RETRY_TIMES):
            try:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=config.REQUEST_TIMEOUT
                )
                
                # 检查HTTP状态
                if response.status_code != 200:
                    if attempt < config.MAX_RETRY_TIMES - 1:
                        time.sleep(2)
                        continue
                    return None, f"HTTP错误: {response.status_code}", {}
                
                # 解析响应
                data = response.json()
                
                # 检查API返回状态
                if data.get("error_code") == 0:
                    result = data.get("result", {})
                    industry = result.get("industry", "未知")
                    
                    # 提取有用的信息
                    company_info = {
                        "企业名称": result.get("name", company_name),
                        "行业类别": industry,
                        "经营状态": result.get("regStatus", ""),
                        "法定代表人": result.get("legalPersonName", ""),
                        "成立日期": result.get("estiblishTime", ""),
                        "注册资本": result.get("regCapital", ""),
                        "统一社会信用代码": result.get("creditCode", "")
                    }
                    
                    return industry, "API查询成功", company_info
                else:
                    error_msg = data.get("reason", "未知错误")
                    return None, f"API返回错误: {error_msg}", {}
                    
            except requests.exceptions.Timeout:
                if attempt < config.MAX_RETRY_TIMES - 1:
                    time.sleep(2)
                    continue
                return None, "请求超时", {}
                
            except requests.exceptions.RequestException as e:
                if attempt < config.MAX_RETRY_TIMES - 1:
                    time.sleep(2)
                    continue
                return None, f"网络错误: {str(e)}", {}
                
            except Exception as e:
                return None, f"未知错误: {str(e)}", {}
        
        return None, "重试次数耗尽", {}
    
    def query_single_company(self, company_name: str) -> Dict:
        """
        查询单个企业信息（智能识别+API）
        
        Args:
            company_name: 企业名称
            
        Returns:
            包含企业信息的字典
        """
        # 处理空值
        if not company_name or pd.isna(company_name) or str(company_name).strip() == "":
            self.stats["empty"] += 1
            return {
                "企业名称": "",
                "行业类别": "",
                "查询状态": "空行",
                "数据来源": "-"
            }
        
        company_name = str(company_name).strip()
        
        # 先尝试智能识别事业单位
        institution_industry = self.identify_institution(company_name)
        if institution_industry:
            self.stats["institution"] += 1
            return {
                "企业名称": company_name,
                "行业类别": institution_industry,
                "查询状态": "智能识别成功",
                "数据来源": "关键词识别",
                "经营状态": "事业单位",
                "法定代表人": "",
                "成立日期": "",
                "注册资本": "",
                "统一社会信用代码": ""
            }
        
        # 调用天眼查API查询
        print(f"正在查询: {company_name}")
        industry, status, company_info = self.query_tianyancha_api(company_name)
        
        if industry:
            self.stats["api_success"] += 1
            result = {
                "企业名称": company_info.get("企业名称", company_name),
                "行业类别": company_info.get("行业类别", ""),
                "查询状态": status,
                "数据来源": "天眼查API",
                "经营状态": company_info.get("经营状态", ""),
                "法定代表人": company_info.get("法定代表人", ""),
                "成立日期": company_info.get("成立日期", ""),
                "注册资本": company_info.get("注册资本", ""),
                "统一社会信用代码": company_info.get("统一社会信用代码", "")
            }
        else:
            self.stats["api_failed"] += 1
            result = {
                "企业名称": company_name,
                "行业类别": "",
                "查询状态": status,
                "数据来源": "查询失败",
                "经营状态": "",
                "法定代表人": "",
                "成立日期": "",
                "注册资本": "",
                "统一社会信用代码": ""
            }
        
        # 添加请求间隔，避免频率限制
        time.sleep(config.REQUEST_INTERVAL)
        
        return result
    
    def process_csv(self, input_file: str, output_file: str):
        """
        处理CSV文件，批量查询企业信息
        
        Args:
            input_file: 输入CSV文件路径
            output_file: 输出Excel文件路径
        """
        print("=" * 60)
        print("🚀 企业行业信息查询工具")
        print("=" * 60)
        print(f"📂 读取文件: {input_file}")
        
        # 读取CSV文件
        try:
            df = pd.read_csv(input_file, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(input_file, encoding='gbk')
        
        # 获取企业名称列
        if '企业名称' not in df.columns:
            print("❌ 错误: CSV文件中没有找到'企业名称'列")
            return
        
        total_count = len(df)
        self.stats["total"] = total_count
        
        print(f"📊 共找到 {total_count} 条记录")
        print(f"⚙️  API Token: {'已配置' if self.api_token != 'your_api_token_here' else '未配置（请在config.py中设置）'}")
        print("=" * 60)
        print()
        
        # 批量查询
        results = []
        for idx, row in df.iterrows():
            company_name = row.get('企业名称', '')
            print(f"[{idx + 1}/{total_count}] ", end="")
            
            result = self.query_single_company(company_name)
            results.append(result)
            
            # 显示进度
            if result["查询状态"] == "API查询成功":
                print(f"✅ {result['企业名称']} → {result['行业类别']}")
            elif result["查询状态"] == "智能识别成功":
                print(f"🎯 {result['企业名称']} → {result['行业类别']} (智能识别)")
            elif result["查询状态"] == "空行":
                print("⏭️  跳过空行")
            else:
                print(f"⚠️  {company_name} → {result['查询状态']}")
        
        # 创建结果DataFrame
        result_df = pd.DataFrame(results)
        
        # 保存为Excel
        print()
        print("=" * 60)
        print(f"💾 保存结果到: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 主结果表
            result_df.to_excel(writer, sheet_name='查询结果', index=False)
            
            # 统计信息表
            stats_df = pd.DataFrame([
                {"项目": "总记录数", "数量": self.stats["total"]},
                {"项目": "API查询成功", "数量": self.stats["api_success"]},
                {"项目": "智能识别成功", "数量": self.stats["institution"]},
                {"项目": "查询失败", "数量": self.stats["api_failed"]},
                {"项目": "空行", "数量": self.stats["empty"]},
                {"项目": "查询时间", "数量": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            ])
            stats_df.to_excel(writer, sheet_name='统计信息', index=False)
        
        # 显示统计信息
        print()
        print("📈 查询统计:")
        print(f"   - 总记录数: {self.stats['total']}")
        print(f"   - API查询成功: {self.stats['api_success']}")
        print(f"   - 智能识别成功: {self.stats['institution']}")
        print(f"   - 查询失败: {self.stats['api_failed']}")
        print(f"   - 空行: {self.stats['empty']}")
        print()
        print("✨ 完成！")
        print("=" * 60)


def main():
    """主函数"""
    # 检查API Token配置
    if config.TIANYANCHA_API_TOKEN == "your_api_token_here":
        print("⚠️  警告: 未配置天眼查API Token")
        print("   请在 config.py 文件中设置 TIANYANCHA_API_TOKEN")
        print("   目前将仅使用智能识别功能")
        print()
        response = input("是否继续？(y/n): ")
        if response.lower() != 'y':
            return
    
    # 创建查询对象
    query = CompanyIndustryQuery()
    
    # 执行查询
    query.process_csv(config.INPUT_CSV, config.OUTPUT_EXCEL)


if __name__ == "__main__":
    main()


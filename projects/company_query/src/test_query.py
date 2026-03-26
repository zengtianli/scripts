# -*- coding: utf-8 -*-
"""
测试脚本 - 用于测试API是否正常工作
在运行完整查询前，建议先运行此脚本测试
"""

from company_industry_query import CompanyIndustryQuery
import config


def test_single_query():
    """测试单个企业查询"""
    print("=" * 60)
    print("🧪 测试天眼查API查询")
    print("=" * 60)
    print()
    
    # 检查配置
    if config.TIANYANCHA_API_TOKEN == "your_api_token_here":
        print("⚠️  警告: 未配置API Token")
        print("   将仅测试智能识别功能")
        print()
    else:
        print(f"✅ API Token已配置")
        print()
    
    # 创建查询对象
    query = CompanyIndustryQuery()
    
    # 测试案例
    test_cases = [
        "嵊州市公安局交通警察大队",  # 政府机关 - 应该被智能识别
        "嵊州市人民医院",            # 医疗机构 - 应该被智能识别
        "嵊州中学",                  # 教育机构 - 应该被智能识别
        "浙江巴贝领带有限公司",      # 企业 - 需要API查询
        "嵊州越剧小镇文化旅游有限公司"  # 企业 - 需要API查询
    ]
    
    print("开始测试查询...\n")
    
    results = []
    for idx, company_name in enumerate(test_cases, 1):
        print(f"测试 {idx}/{len(test_cases)}: {company_name}")
        result = query.query_single_company(company_name)
        results.append(result)
        
        print(f"   结果: {result['行业类别']}")
        print(f"   状态: {result['查询状态']}")
        print(f"   来源: {result['数据来源']}")
        print()
    
    # 显示统计
    print("=" * 60)
    print("📊 测试统计:")
    print(f"   - 智能识别成功: {query.stats['institution']}")
    print(f"   - API查询成功: {query.stats['api_success']}")
    print(f"   - 查询失败: {query.stats['api_failed']}")
    print("=" * 60)
    print()
    
    # 判断是否可以继续
    if query.stats['api_success'] > 0 or query.stats['institution'] > 0:
        print("✅ 测试通过！可以运行完整查询")
        print("   运行命令: python company_industry_query.py")
    elif config.TIANYANCHA_API_TOKEN == "your_api_token_here":
        print("⚠️  未配置API Token")
        print("   智能识别功能正常，但无法查询企业工商信息")
        print("   请在 config.py 中配置您的API Token")
    else:
        print("❌ API查询失败")
        print("   请检查:")
        print("   1. API Token是否正确")
        print("   2. 网络连接是否正常")
        print("   3. API额度是否用完")


if __name__ == "__main__":
    test_single_query()



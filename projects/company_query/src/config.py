# -*- coding: utf-8 -*-
"""
配置文件
请在这里填写您的天眼查API密钥
"""
import os

# ==================== 天眼查API配置 ====================
# 请在这里填写您从天眼查开放平台获取的API Token
TIANYANCHA_API_TOKEN = os.getenv("TIANYANCHA_API_TOKEN", "")

# 天眼查API基础URL
TIANYANCHA_BASE_URL = "http://open.api.tianyancha.com/services/open/ic/baseinfo/2.0"

# ==================== 查询配置 ====================
# 请求间隔时间（秒），避免请求过快被限流
REQUEST_INTERVAL = 1.0

# 失败重试次数
MAX_RETRY_TIMES = 3

# 超时时间（秒）
REQUEST_TIMEOUT = 10

# ==================== 文件路径配置 ====================
# 输入CSV文件路径
INPUT_CSV = "发曾田力-企业名称_Sheet1.csv"

# 输出Excel文件路径
OUTPUT_EXCEL = "企业信息查询结果.xlsx"

# ==================== 事业单位关键词配置 ====================
# 用于智能识别政府机关、学校、医院等查不到工商信息的单位
GOVERNMENT_KEYWORDS = [
    "公安局", "派出所", "交警", "看守所", "监狱", "消防",
    "政府", "人民法院", "检察院", "司法局", "市场监管局",
    "城管", "管理服务中心", "事务服务中心", "行政执法"
]

EDUCATION_KEYWORDS = [
    "学校", "中学", "小学", "幼儿园", "大学", "学院", 
    "职业技术", "职教中心", "教育中心", "培训中心"
]

HOSPITAL_KEYWORDS = [
    "医院", "卫生院", "诊所", "中医院", "人民医院",
    "妇幼保健", "疾控中心", "医疗中心"
]

# 事业单位行业分类映射
INSTITUTION_INDUSTRY_MAP = {
    "政府机关": GOVERNMENT_KEYWORDS,
    "教育": EDUCATION_KEYWORDS,
    "医疗卫生": HOSPITAL_KEYWORDS
}


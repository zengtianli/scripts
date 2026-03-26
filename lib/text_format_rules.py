"""
文本格式化规则引擎 — 引号、标点、单位的统一替换逻辑

供 docx_text_formatter / md_tools / pptx_tools 共用
"""

import re

# ── 标点映射 ──────────────────────────────────────────────────

PUNCTUATION_MAP = {
    ",": "，",
    ":": "：",
    ";": "；",
    "!": "！",
    "?": "？",
    "(": "（",
    ")": "）",
}

# ── 单位映射（按键长度降序排列，优先匹配长的） ──────────────

UNITS_MAP = {
    # 面积
    "平方公里": "km²",
    "平方千米": "km²",
    "平方厘米": "cm²",
    "平方毫米": "mm²",
    "平方米": "m²",
    # 体积
    "立方公里": "km³",
    "立方千米": "km³",
    "立方厘米": "cm³",
    "立方毫米": "mm³",
    "立方米": "m³",
    # 长度
    "公里": "km",
    "千米": "km",
    "厘米": "cm",
    "毫米": "mm",
    "微米": "μm",
    "纳米": "nm",
    # 质量
    "公斤": "kg",
    "千克": "kg",
    "毫克": "mg",
    "微克": "μg",
    # 容量
    "毫升": "mL",
    "微升": "μL",
    # 时间
    "小时": "h",
    "分钟": "min",
    "秒钟": "s",
    # 温度
    "摄氏度": "℃",
    "华氏度": "℉",
    # 上标
    "km2": "km²",
    "km3": "km³",
    "m2": "m²",
    "m3": "m³",
}

# 按键长度降序排列，保证长匹配优先
_UNITS_SORTED = sorted(UNITS_MAP.items(), key=lambda x: len(x[0]), reverse=True)

# ── 引号模式 ─────────────────────────────────────────────────

QUOTE_PATTERN = '[""\u201c\u201d\u300c\u300d]'


def fix_quotes(content: str, counter: int = 0) -> tuple[str, int, int]:
    """
    替换所有双引号为中文标准引号（奇数→左"，偶数→右"）

    counter: 外部传入的计数器，用于跨 run 保持引号配对（DOCX 场景）
    返回: (结果文本, 本次替换数, 更新后的 counter)
    """
    count = len(re.findall(QUOTE_PATTERN, content))

    def replace_quote(_match):
        nonlocal counter
        counter += 1
        return "\u201c" if counter % 2 == 1 else "\u201d"

    result = re.sub(QUOTE_PATTERN, replace_quote, content)
    return result, count, counter


def fix_punctuation(content: str) -> tuple[str, int]:
    """英文标点 → 中文标点，返回 (结果, 替换次数)"""
    result = content
    total = 0
    for eng, chn in PUNCTUATION_MAP.items():
        escaped = re.escape(eng)
        n = len(re.findall(escaped, result))
        total += n
        result = re.sub(escaped, chn, result)
    return result, total


def fix_units(content: str) -> tuple[str, int]:
    """中文单位 → 标准符号，返回 (结果, 替换次数)"""
    result = content
    total = 0
    for unit_cn, unit_sym in _UNITS_SORTED:
        n = result.count(unit_cn)
        total += n
        result = result.replace(unit_cn, unit_sym)
    return result, total

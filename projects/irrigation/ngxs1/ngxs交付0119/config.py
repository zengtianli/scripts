"""
系统配置文件，包含各种全局配置参数
"""

# 计算模式: 
# "crop"(旱地作物模式 dryland), 
# "irrigation"(水稻灌溉模式 paddy), 
# "both"(综合模式，同时计算旱地和水稻)
CALCULATION_MODE = "both"

# 模式常量定义（提供给导入模块使用）
DRYLAND_MODE = "crop"       # 旱地作物模式
PADDY_MODE = "irrigation"   # 水稻灌溉模式 
BOTH_MODE = "both"          # 综合模式

OUTPUT_DIR = "data"
WARMUP_DAYS = 30

# 不同作物的开花期配置
FLOWERING_PERIODS = {
    '单季稻': {'start': '/06/26', 'end': '/10/22'},
    '双季稻': {'start': '/04/18', 'end': '/10/22'}
}

# 灌溉系统配置
IRRIGATION_SYSTEMS = {
    # 单季稻灌溉系统参数
    '单季稻': {
        'periods': 20,                # 生长期数量
        'data_slice': slice(0, 5)     # 数据在文件中的列范围
    },
    # 双季稻灌溉系统参数
    '双季稻': {
        'periods': 20, 
        'data_slice': slice(5, 10)
    }
}

# 静态灌溉制度文件配置
STATIC_IRRIGATION_FILES = {
    '单季稻': 'static_single_crop.txt',  # 单季稻灌溉制度表
    '双季稻': 'static_double_crop.txt'   # 双季稻灌溉制度表
}

# 是否使用静态灌溉制度文件
USE_STATIC_IRRIGATION = True

# 输入文件配置
INPUT_FILES = {
    'time_config': "in_TIME.txt",          # 时间配置文件
    'area_config': "static_fenqu.txt",     # 区域配置文件
    'irrigation_system': "static_single_crop.txt", # 使用静态灌溉制度文件代替
    'rainfall': "in_JYGC.txt",             # 降雨量数据文件
    'evaporation': "in_ZFGC.txt",          # 蒸发量数据文件
    'crop': "static_irrigation_quota.txt",  # 作物月度灌溉定额文件
    'dry_area': "in_dry_crop_area.txt",    # 旱地面积数据文件
    'fenqu': "static_fenqu.txt"            # 分区数据文件
}

# 输出文件名配置
OUTPUT_FILES = {
    'irrigation': 'OUT_GGXS.txt',         # 灌溉输出文件
    'drainage': 'OUT_PYCS.txt'            # 排水输出文件
}

# 日志配置
LOG_CONFIG = {
    'enabled': True,                      # 是否启用日志 (总开关)
    'verbose': False,                     # 是否输出详细调试信息
    'levels': {
        'file_io': False,                 # 文件IO操作日志
        'calculation': False,             # 计算过程日志
        'crop_details': False,            # 作物详情计算日志
        'irrigation_details': False,      # 灌溉详情计算日志
        'area_processing': False,         # 区域处理日志
        'warnings': True,                 # 警告信息
        'errors': True                    # 错误信息
    }
}

# 不同模式的输出文件配置
MODE_OUTPUT_FILES = {
    # 旱地作物模式输出文件 (dryland)
    'crop': {
        'irrigation': 'OUT_GGXS_C.txt',   # 旱地作物灌溉结果
        'drainage': 'OUT_PYCS_C.txt'      # 旱地作物排水结果
    },
    # 水稻灌溉模式输出文件 (paddy)
    'irrigation': {
        'irrigation': 'OUT_GGXS_I.txt',   # 水稻灌溉结果
        'drainage': 'OUT_PYCS_I.txt'      # 水稻灌溉排水结果
    }
}

# 水位平衡数据输出文件配置

# 作物类型水位平衡文件
CROP_WATER_BALANCE_FILES = {
    'single_crop': 'water_balance_single_crop.txt',  # 单季稻水位平衡
    'double_crop': 'water_balance_double_crop.txt'   # 双季稻水位平衡
}

# 作物类型灌溉需水文件
CROP_IRRIGATION_FILES = {
    'single_crop': 'irrigation_single_crop.txt',     # 单季稻灌溉需水
    'double_crop': 'irrigation_double_crop.txt'      # 双季稻灌溉需水
}

# 合并结果输出文件
TOTAL_OUTPUT_FILES = {
    'irrigation': 'OUT_GGXS_TOTAL.txt',   # 合并灌溉结果
    'drainage': 'OUT_PYCS_TOTAL.txt'      # 合并排水结果
}

# 日志输出工具函数
def log(level, message):
    """
    根据配置输出日志
    
    参数:
        level: 日志级别，对应LOG_CONFIG['levels']中的键
        message: 日志消息
    """
    if not LOG_CONFIG['enabled']:
        return
    
    if level in LOG_CONFIG['levels'] and LOG_CONFIG['levels'][level]:
        print(message)
    elif level not in LOG_CONFIG['levels'] and (LOG_CONFIG['levels']['errors'] or LOG_CONFIG['verbose']):
        # 未知日志级别作为错误处理
        print(f"[错误日志级别: {level}] {message}")

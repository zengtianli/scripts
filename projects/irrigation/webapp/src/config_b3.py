"""
B3 案例数据配置

B3 灌区特点：
- 单灌区（254万亩实灌面积）
- 按县区分（县区1-4）
- 数据格式：NC + Excel
- 时间范围：4月-9月（灌溉季）
"""

# ==============================================================================
# B3 模式开关
# ==============================================================================

B3_MODE = True  # 设为 True 启用 B3 数据格式

# ==============================================================================
# NC 文件配置
# ==============================================================================

# NC 文件名模板（{year} 会被替换为实际年份）
NC_FILES = {
    'rain': 'rain_{year}.nc',           # 降雨量
    'temp_avg': 'temp_avg_{year}.nc',   # 平均气温
    'temp_max': 'temp_max_{year}.nc',   # 最高气温
    'temp_min': 'temp_min_{year}.nc',   # 最低气温
    'wind_speed': 'wind_speed_{year}.nc',  # 风速
    'pressure': 'pressure_{year}.nc',   # 大气压
    'humidity': 'humidity_{year}.nc',   # 湿度
    'sun_hours': 'sun_hours_{year}.nc', # 日照时数
    'et0': 'et0_{year}.nc',             # 参考蒸发蒸腾量
    'crops': 'crops_{year}.nc',         # 作物面积
    'output': 'output_{year}.nc'        # 输出：旬毛需水量
}

# NC 变量名映射
NC_VARIABLES = {
    'rain': 'RAIN',                 # 降雨量 (mm)
    'temp_avg': 'TEMP_AVG',         # 平均气温 (℃)
    'temp_max': 'TEMP_MAX',         # 最高气温 (℃)
    'temp_min': 'TEMP_MIN',         # 最低气温 (℃)
    'wind_speed': 'WIND_SPEED',     # 风速 (m/s)
    'pressure': 'PRESSURE',         # 大气压 (kPa)
    'humidity': 'HUMIDITY',         # 湿度 (%)
    'sun_hours': 'SUN_HOURS',       # 日照时数 (h)
    'et0': 'ET0',                   # ET0 (mm/day)
    'crops_name': 'NAME',           # 作物名称
    'crops_area': 'AREA',           # 作物面积 (亩)
    'irrigation': 'IRRIGATION_WATER'  # 毛需水量 (m³)
}

# ==============================================================================
# 作物类型映射
# ==============================================================================

# B3 作物类型 → ngxs 模型作物类型
CROP_MAPPING = {
    '早稻': '双季稻',    # 早稻属于双季稻系统
    '中稻': '单季稻',    # 中稻属于单季稻系统
    '单晚': '单季稻',    # 单晚属于单季稻系统
    '双晚': '双季稻',    # 双晚属于双季稻系统
}

# 反向映射（ngxs → B3）
CROP_MAPPING_REVERSE = {
    '单季稻': ['中稻', '单晚'],
    '双季稻': ['早稻', '双晚'],
}

# ==============================================================================
# 灌区基本信息
# ==============================================================================

B3_IRRIGATION_DISTRICT = {
    'name': 'B3灌区',
    'latitude_range': '北纬31°30′～32°40′',
    'elevation_avg': 25,            # 平均海拔 (m)
    'elevation_range': (10, 200),   # 海拔范围 (m)
    'design_area': 2730000,         # 设计灌溉面积 (亩)
    'effective_area': 2540000,      # 实灌面积 (亩)
    'efficiency': 0.5328,           # 灌溉水利用系数
    'slope_max': 25,                # 最大坡度 (°)
}

# 县区信息
B3_COUNTIES = {
    '县区1': {'design_area': 1834000, 'effective_area': 1730000},
    '县区2': {'design_area': 560000, 'effective_area': 510000},
    '县区3': {'design_area': 306000, 'effective_area': 270000},
    '县区4': {'design_area': 30000, 'effective_area': 30000},
}

# ==============================================================================
# 时间配置
# ==============================================================================

TIME_CONFIG = {
    'irrigation_start_month': 4,    # 灌溉季起始月（4月）
    'irrigation_end_month': 9,      # 灌溉季结束月（9月）
    'warmup_days': 0,               # 预热期天数（B3数据从灌溉季开始，无需预热）
}

# ==============================================================================
# 内置灌溉制度参数（不依赖外部文件）
# ==============================================================================

# 单季稻灌溉制度参数（按月份）
# kc: 蒸发系数, h_min: 水位下限(mm), storage: 设计蓄水位(mm), h_max: 水位上限(mm)
B3_SINGLE_CROP_PARAMS = {
    4: {'kc': 0.60, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 30},  # 4月-泡田插秧
    5: {'kc': 1.10, 'h_min': -35.0, 'storage': -15.0, 'h_max': 10.0, 'days': 31},  # 5月-返青分蘖
    6: {'kc': 0.50, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 30},  # 6月-分蘖后期(梅雨)
    7: {'kc': 0.30, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 31},  # 7月-拔节孕穗(梅雨)
    8: {'kc': 1.20, 'h_min': 10.0,  'storage': 30.0,  'h_max': 50.0, 'days': 31},  # 8月-抽穗开花
    9: {'kc': 1.00, 'h_min': -20.0, 'storage': 0.0,   'h_max': 10.0, 'days': 30},  # 9月-灌浆成熟
}

# 双季稻灌溉制度参数（B3案例主要是单季稻，双季稻用占位参数）
B3_DOUBLE_CROP_PARAMS = {
    4: {'kc': 0.50, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 30},
    5: {'kc': 0.50, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 31},
    6: {'kc': 0.50, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 30},
    7: {'kc': 0.50, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 31},
    8: {'kc': 0.50, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 31},
    9: {'kc': 0.50, 'h_min': -45.0, 'storage': -25.0, 'h_max': 0.0,  'days': 30},
}

def get_irrigation_params(month: int, crop_type: str = '单季稻') -> dict:
    """
    获取指定月份的灌溉制度参数
    
    参数:
        month: 月份 (4-9)
        crop_type: 作物类型 ('单季稻' 或 '双季稻')
    
    返回:
        {'kc': 蒸发系数, 'h_min': 水位下限, 'storage': 设计蓄水位, 'h_max': 水位上限, 'days': 天数}
    """
    if crop_type == '双季稻':
        params = B3_DOUBLE_CROP_PARAMS
    else:
        params = B3_SINGLE_CROP_PARAMS
    
    if month not in params:
        # 默认返回5月参数
        return params.get(5, {'kc': 1.0, 'h_min': -35.0, 'storage': -15.0, 'h_max': 10.0, 'days': 30})
    
    return params[month]

# ==============================================================================
# 单位转换
# ==============================================================================

UNIT_CONVERSION = {
    'mu_to_km2': 1 / 1500,          # 亩 → km²
    'mu_to_ha': 1 / 15,             # 亩 → 公顷
    'mm_to_m3_per_mu': 0.6667,      # mm → m³/亩 (1亩=666.67m²)
}

# ==============================================================================
# 辅助函数
# ==============================================================================

def get_nc_filename(data_type: str, year: int) -> str:
    """
    获取 NC 文件名
    
    参数:
        data_type: 数据类型 (rain, et0, crops, ...)
        year: 年份
        
    返回:
        文件名
    """
    if data_type not in NC_FILES:
        raise ValueError(f"未知数据类型: {data_type}, 可用: {list(NC_FILES.keys())}")
    return NC_FILES[data_type].format(year=year)


def map_crop_type(b3_crop: str) -> str:
    """
    将 B3 作物类型映射到 ngxs 模型类型
    
    参数:
        b3_crop: B3 作物名称
        
    返回:
        ngxs 模型作物类型
    """
    return CROP_MAPPING.get(b3_crop, b3_crop)


def mu_to_km2(area_mu: float) -> float:
    """亩转平方公里"""
    return area_mu * UNIT_CONVERSION['mu_to_km2']


def mm_to_m3(depth_mm: float, area_mu: float) -> float:
    """
    水深(mm) + 面积(亩) → 水量(m³)
    
    参数:
        depth_mm: 水深 (mm)
        area_mu: 面积 (亩)
        
    返回:
        水量 (m³)
    """
    # 1亩 = 666.67 m², 1mm = 0.001m
    # m³ = mm * 0.001 * 亩 * 666.67
    return depth_mm * area_mu * 0.6667

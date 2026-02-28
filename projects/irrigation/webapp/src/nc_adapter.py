"""
NC 数据适配器 - 将 B3 NC 格式转换为 ngxs 模型格式

功能：
1. 读取 B3 NC 文件（气象数据、作物面积）
2. 转换为 ngxs 模型所需的数据格式
3. 提供统一的数据访问接口
"""

import os
import sys
import pandas as pd
import xarray as xr
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 导入 B3 配置
from config_b3 import (
    NC_FILES, NC_VARIABLES, CROP_MAPPING,
    B3_IRRIGATION_DISTRICT, TIME_CONFIG,
    get_nc_filename, map_crop_type, mm_to_m3
)


class NCDataAdapter:
    """
    NC 数据适配器
    
    将 B3 案例的 NC 格式数据转换为 ngxs 模型所需格式
    """
    
    def __init__(self, data_dir: str, year: int = None):
        """
        初始化适配器
        
        参数:
            data_dir: NC 文件所在目录
            year: 数据年份（如果为 None，则自动检测）
        """
        self.data_dir = data_dir
        self.year = year or self._detect_year()
        self._cache = {}  # 数据缓存
        
    def _detect_year(self) -> int:
        """自动检测数据年份"""
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.nc'):
                # 从文件名提取年份，如 rain_2020.nc
                parts = filename.replace('.nc', '').split('_')
                for part in parts:
                    if part.isdigit() and len(part) == 4:
                        return int(part)
        raise ValueError(f"无法从 {self.data_dir} 检测数据年份")
    
    def _get_nc_path(self, data_type: str) -> str:
        """获取 NC 文件完整路径"""
        filename = get_nc_filename(data_type, self.year)
        return os.path.join(self.data_dir, filename)
    
    def _check_file_exists(self, data_type: str) -> bool:
        """检查 NC 文件是否存在"""
        path = self._get_nc_path(data_type)
        return os.path.exists(path)
    
    # =========================================================================
    # 核心数据读取方法
    # =========================================================================
    
    def load_timeseries(self, data_type: str) -> pd.Series:
        """
        加载时间序列数据
        
        参数:
            data_type: 数据类型 (rain, et0, temp_avg, ...)
            
        返回:
            pandas Series，索引为日期
        """
        cache_key = f"ts_{data_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        nc_path = self._get_nc_path(data_type)
        var_name = NC_VARIABLES.get(data_type, data_type.upper())
        
        if not os.path.exists(nc_path):
            raise FileNotFoundError(f"NC 文件不存在: {nc_path}")
        
        ds = xr.open_dataset(nc_path)
        
        # 获取数据
        if var_name not in ds.data_vars:
            available = list(ds.data_vars)
            ds.close()
            raise ValueError(f"变量 '{var_name}' 不存在于 {nc_path}，可用: {available}")
        
        data = ds[var_name].values.flatten()
        
        # 构建时间索引
        if 'BGTM' in ds.attrs:
            start_time = pd.to_datetime(ds.attrs['BGTM'])
            time_index = pd.date_range(start=start_time, periods=len(data), freq='D')
        else:
            # 默认从年初开始
            start_time = pd.Timestamp(f'{self.year}-01-01')
            time_index = pd.date_range(start=start_time, periods=len(data), freq='D')
        
        series = pd.Series(data, index=time_index, name=data_type)
        ds.close()
        
        self._cache[cache_key] = series
        return series
    
    def load_crop_areas(self) -> Dict[str, float]:
        """
        加载作物面积数据
        
        返回:
            Dict: {模型作物类型: 面积(亩)}
            例如: {'单季稻': 1760000, '双季稻': 780000}
        """
        cache_key = "crop_areas"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        nc_path = self._get_nc_path('crops')
        
        if not os.path.exists(nc_path):
            raise FileNotFoundError(f"作物面积 NC 文件不存在: {nc_path}")
        
        ds = xr.open_dataset(nc_path)
        
        # 获取作物名称和面积
        name_var = NC_VARIABLES['crops_name']
        area_var = NC_VARIABLES['crops_area']
        
        crop_names = ds[name_var].values
        crop_areas = ds[area_var].values.flatten()
        
        # 按模型作物类型汇总
        areas = {}
        for name, area in zip(crop_names, crop_areas):
            name_str = str(name).strip()
            if isinstance(name, bytes):
                name_str = name.decode('utf-8').strip()
            
            # 映射到模型作物类型
            model_type = map_crop_type(name_str)
            
            if model_type in areas:
                areas[model_type] += float(area)
            else:
                areas[model_type] = float(area)
        
        ds.close()
        
        self._cache[cache_key] = areas
        return areas
    
    # =========================================================================
    # 气象数据接口（适配 ngxs 模型）
    # =========================================================================
    
    def get_rainfall(self, area_name: str = None) -> pd.Series:
        """
        获取降雨量数据
        
        参数:
            area_name: 灌区名称（B3 是单灌区，忽略此参数）
            
        返回:
            降雨量 Series (mm)
        """
        return self.load_timeseries('rain')
    
    def get_evaporation(self, area_name: str = None) -> pd.Series:
        """
        获取蒸发量数据（使用 ET0）
        
        参数:
            area_name: 灌区名称（B3 是单灌区，忽略此参数）
            
        返回:
            ET0 Series (mm/day)
        """
        return self.load_timeseries('et0')
    
    def get_weather_data(self, area_name: str = None) -> Tuple[pd.Series, pd.Series]:
        """
        获取气象数据，返回格式与 ngxs 原有接口兼容
        
        参数:
            area_name: 灌区名称（B3 是单灌区，忽略此参数）
            
        返回:
            (降雨量 Series, 蒸发量 Series)
        """
        rainfall = self.get_rainfall(area_name)
        evaporation = self.get_evaporation(area_name)
        return rainfall, evaporation
    
    def get_all_weather(self) -> Dict[str, pd.Series]:
        """
        获取所有气象数据
        
        返回:
            Dict: {数据类型: Series}
        """
        weather_types = ['rain', 'temp_avg', 'temp_max', 'temp_min', 
                        'wind_speed', 'pressure', 'humidity', 'sun_hours', 'et0']
        
        result = {}
        for wtype in weather_types:
            if self._check_file_exists(wtype):
                try:
                    result[wtype] = self.load_timeseries(wtype)
                except Exception as e:
                    print(f"警告: 加载 {wtype} 失败: {e}")
        
        return result
    
    # =========================================================================
    # 转换为模型格式
    # =========================================================================
    
    def to_model_format(self) -> Dict:
        """
        转换为 ngxs 模型输入格式
        
        返回:
            Dict: 包含所有模型所需数据
        """
        rainfall = self.get_rainfall()
        evaporation = self.get_evaporation()
        crop_areas = self.load_crop_areas()
        
        return {
            'rainfall': rainfall,
            'evaporation': evaporation,
            'crop_areas': crop_areas,
            'district_info': B3_IRRIGATION_DISTRICT,
            'start_time': rainfall.index[0],
            'end_time': rainfall.index[-1],
            'days': len(rainfall),
            'year': self.year,
        }
    
    def get_time_config(self) -> Tuple[datetime, int]:
        """
        获取时间配置（兼容 ngxs load_time_config 接口）
        
        返回:
            (起始时间, 预测天数)
        """
        rainfall = self.get_rainfall()
        start_time = rainfall.index[0].to_pydatetime()
        days = len(rainfall)
        return start_time, days
    
    # =========================================================================
    # 灌区配置接口
    # =========================================================================
    
    def get_irrigation_area_config(self) -> List:
        """
        获取灌区配置（兼容 ngxs load_irrigation_area_config 接口）
        
        返回:
            灌区配置列表（单灌区）
        """
        crop_areas = self.load_crop_areas()
        district = B3_IRRIGATION_DISTRICT
        
        # 构建与 ngxs 兼容的配置格式
        # [序号, 名称, 单季稻面积, 双季稻面积, 旱地面积, 杂地面积, 水面面积, 
        #  平原面积, 水田渗漏, 旱地渗漏, 春花种植比例, 轮灌批次]
        
        single_crop_area = crop_areas.get('单季稻', 0) / 1500  # 亩 → km²
        double_crop_area = crop_areas.get('双季稻', 0) / 1500
        
        config = [
            1,                          # 序号
            district['name'],           # 名称
            single_crop_area,           # 单季稻面积 (km²)
            double_crop_area,           # 双季稻面积 (km²)
            0,                          # 旱地面积
            0,                          # 杂地面积
            0,                          # 水面面积
            district['effective_area'] / 1500,  # 平原面积 (km²)
            2,                          # 水田渗漏 (mm/day)
            2,                          # 旱地渗漏 (mm/day)
            0,                          # 春花种植比例
            10,                         # 轮灌批次
        ]
        
        return [config]
    
    # =========================================================================
    # 信息输出
    # =========================================================================
    
    def print_summary(self):
        """打印数据摘要"""
        print(f"\n{'='*60}")
        print(f"B3 NC 数据适配器 - 数据摘要")
        print(f"{'='*60}")
        print(f"数据目录: {self.data_dir}")
        print(f"数据年份: {self.year}")
        
        # 检查可用文件
        print(f"\n可用 NC 文件:")
        for dtype in NC_FILES.keys():
            exists = "✅" if self._check_file_exists(dtype) else "❌"
            print(f"  {exists} {dtype}: {get_nc_filename(dtype, self.year)}")
        
        # 时间范围
        try:
            rainfall = self.get_rainfall()
            print(f"\n时间范围: {rainfall.index[0].date()} ~ {rainfall.index[-1].date()}")
            print(f"总天数: {len(rainfall)}")
        except:
            pass
        
        # 作物面积
        try:
            crop_areas = self.load_crop_areas()
            print(f"\n作物面积 (亩):")
            for crop, area in crop_areas.items():
                print(f"  {crop}: {area:,.0f}")
        except:
            pass
        
        print(f"{'='*60}\n")


# =============================================================================
# 便捷函数
# =============================================================================

def load_b3_data(data_dir: str, year: int = None) -> Dict:
    """
    加载 B3 格式数据（便捷函数）
    
    参数:
        data_dir: NC 文件目录
        year: 数据年份（可选，自动检测）
        
    返回:
        模型输入数据字典
    """
    adapter = NCDataAdapter(data_dir, year)
    return adapter.to_model_format()


def create_adapter(data_dir: str, year: int = None) -> NCDataAdapter:
    """
    创建 NC 数据适配器（便捷函数）
    
    参数:
        data_dir: NC 文件目录
        year: 数据年份（可选，自动检测）
        
    返回:
        NCDataAdapter 实例
    """
    return NCDataAdapter(data_dir, year)


# =============================================================================
# 命令行测试
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='B3 NC 数据适配器测试')
    parser.add_argument('data_dir', help='NC 文件目录')
    parser.add_argument('--year', type=int, help='数据年份')
    
    args = parser.parse_args()
    
    adapter = NCDataAdapter(args.data_dir, args.year)
    adapter.print_summary()
    
    # 测试数据加载
    print("测试数据加载...")
    model_data = adapter.to_model_format()
    print(f"降雨数据: {len(model_data['rainfall'])} 天")
    print(f"蒸发数据: {len(model_data['evaporation'])} 天")
    print(f"作物面积: {model_data['crop_areas']}")

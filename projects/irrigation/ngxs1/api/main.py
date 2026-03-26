"""
农田灌溉需水计算 API 服务
部署到 Railway，供前端调用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os

# 添加父目录到路径，以便导入计算模块
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

app = FastAPI(
    title="农田灌溉需水计算API",
    description="浙东河网农田灌溉需水量计算服务",
    version="1.0.0"
)

# CORS 配置，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tianlizeng.cloud",
        "https://www.tianlizeng.cloud",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 数据模型
# ============================================================================

class CalculateRequest(BaseModel):
    start_date: str = "2025/07/15"
    forecast_days: int = 16
    guarantee_rate: int = 90  # 50, 75, 90
    mode: str = "both"  # crop, irrigation, both


class DailyData(BaseModel):
    date: str
    irrigation: float
    drainage: float
    crops: Dict[str, float] = {}  # 各作物需水量 {"单季稻": 100, "蔬菜": 50, ...}


class AreaData(BaseModel):
    name: str
    single_crop_area: float
    double_crop_area: float
    dry_land_area: float
    irrigation: float


class ActiveCrop(BaseModel):
    name: str
    quota: int
    unit: str = "m³/km²/月"


class ParameterPreview(BaseModel):
    start_date: str
    forecast_days: int
    warmup_days: int
    guarantee_rate: int
    mode: str
    active_crops: List[ActiveCrop]
    total_single_crop: float
    total_double_crop: float
    total_dry_land: float
    current_period: str
    eva_ratio: float
    leakage: float
    rotation_batches: int


class CropBreakdown(BaseModel):
    """单个作物的需水详情"""
    name: str           # 作物名称
    area: float         # 种植面积 (km²)
    quota: Optional[float] = None  # 月定额 (m³/km²/月)，水稻为 None
    total: float        # 总需水量 (m³)
    daily_avg: float    # 日均需水量 (m³/日)
    method: str = "定额法"  # 计算方法


class CategorySummary(BaseModel):
    """分类汇总"""
    category: str       # 分类名称（水稻灌溉/旱地作物）
    total: float        # 总需水量
    percentage: float   # 占比 (%)
    crops: List[CropBreakdown]  # 作物明细


class CalculateResponse(BaseModel):
    success: bool
    total_irrigation: float
    total_drainage: float
    daily_data: List[DailyData]
    area_data: List[AreaData]
    breakdown: List[CategorySummary]  # 新增：分类详情
    parameters: ParameterPreview
    message: str = ""


# ============================================================================
# 工具函数
# ============================================================================

def read_file_lines(filename: str) -> List[str]:
    """读取文件内容"""
    filepath = os.path.join(parent_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def get_areas() -> List[Dict]:
    """获取灌区列表"""
    lines = read_file_lines('static_fenqu.txt')
    areas = []
    for line in lines[1:]:  # 跳过表头
        fields = line.split('\t')
        if len(fields) >= 11:
            areas.append({
                'name': fields[0],
                'single_crop_area': float(fields[1]),
                'double_crop_area': float(fields[2]),
                'dry_land_area': float(fields[3]),
                'paddy_leakage': float(fields[7]),
                'rotation_batches': int(fields[10]) if len(fields) > 10 else 10
            })
    return areas


def get_guarantee_rate() -> int:
    """获取保证率"""
    lines = read_file_lines('in_dry_crop_area.txt')
    if len(lines) > 1:
        fields = lines[1].split('\t')
        if len(fields) > 1:
            return int(fields[1])
    return 90


def get_active_crops(month: int, guarantee_rate: int) -> List[Dict]:
    """获取当月有灌溉需求的旱地作物
    
    返回:
        [{"name": "蔬菜", "quota": 1500, "unit": "m³/km²/月"}, ...]
    """
    dryland_crops = ['蔬菜', '小麦', '油菜', '瓜果', '豆类']
    lines = read_file_lines('static_irrigation_quota.txt')
    active = []
    
    prob_map = {50: 0.5, 75: 0.75, 90: 0.9}
    target_prob = prob_map.get(guarantee_rate, 0.9)
    
    for line in lines[1:]:
        fields = line.split('\t')
        if len(fields) >= 14:
            crop_name = fields[0]
            if crop_name not in dryland_crops:
                continue
            prob = float(fields[1]) if fields[1] else 0
            if abs(prob - target_prob) < 0.01:
                month_quota = float(fields[month + 1]) if fields[month + 1] else 0
                if month_quota > 0:
                    active.append({
                        "name": crop_name,
                        "quota": int(month_quota),
                        "unit": "m³/km²/月"
                    })
    return active


def update_guarantee_rate(rate: int) -> None:
    """更新所有灌区的保证率"""
    filepath = os.path.join(parent_dir, 'in_dry_crop_area.txt')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    header_found = False
    
    for line in lines:
        # 保留注释行
        if line.strip().startswith('#'):
            new_lines.append(line)
            continue
        
        # 第一个非注释行是表头
        if not header_found:
            new_lines.append(line)
            header_found = True
            continue
        
        # 数据行：更新保证率
        if line.strip():
            fields = line.strip().split('\t')
            if len(fields) > 1:
                fields[1] = str(rate)  # 更新保证率列
                new_lines.append('\t'.join(fields) + '\n')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


def get_current_period(start_date: datetime) -> tuple:
    """获取当前生育期信息"""
    lines = read_file_lines('static_single_crop.txt')
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 7:
            try:
                period_start = datetime.strptime(parts[0], '%Y/%m/%d')
                period_end = datetime.strptime(parts[1], '%Y/%m/%d')
                if period_start <= start_date <= period_end:
                    return (
                        f"{parts[0]} ~ {parts[1]}",
                        float(parts[3]),  # eva_ratio
                        f"{parts[4]}-{parts[5]}-{parts[6]}"  # 水位控制
                    )
            except:
                pass
    return ("未知", 1.0, "")


def calculate_crop_breakdown(
    mode: str, 
    guarantee_rate: int, 
    forecast_days: int,
    month: int,
    daily_by_crop: Dict[str, Dict[str, float]] = None
) -> List[CategorySummary]:
    """
    计算各作物的需水量分解
    
    统一从 daily_by_crop 汇总数据，确保总量、明细、趋势图一致
    """
    if daily_by_crop is None:
        daily_by_crop = {}
    
    breakdown = []
    
    # 从 daily_by_crop 汇总各作物总需水量
    crop_totals = {}  # {作物名: 总需水量}
    for date, crops in daily_by_crop.items():
        for crop_name, water in crops.items():
            if crop_name not in crop_totals:
                crop_totals[crop_name] = 0.0
            crop_totals[crop_name] += water
    
    # 分类作物
    rice_names = ['单季稻', '双季稻']
    dryland_names = ['蔬菜', '小麦', '油菜', '瓜果', '豆类']
    
    # 读取面积数据
    rice_areas = _get_rice_areas()
    dryland_areas = _get_dryland_areas()
    dryland_quotas = _get_dryland_quotas(guarantee_rate, month)
    
    # 计算总量
    rice_total = sum(crop_totals.get(name, 0) for name in rice_names)
    dryland_total = sum(crop_totals.get(name, 0) for name in dryland_names)
    total_all = rice_total + dryland_total
    
    # 1. 水稻灌溉分解
    if mode in ["irrigation", "both"]:
        rice_crops = []
        for name in rice_names:
            crop_total = crop_totals.get(name, 0)
            area = rice_areas.get(name, 0)
            if area > 0 or crop_total > 0:
                rice_crops.append(CropBreakdown(
                    name=name,
                    area=round(area, 2),
                    quota=None,
                    total=round(crop_total, 2),
                    daily_avg=round(crop_total / forecast_days, 2) if forecast_days > 0 else 0,
                    method="水量平衡法"
                ))
        
        if rice_crops:
            breakdown.append(CategorySummary(
                category="水稻灌溉",
                total=round(rice_total, 2),
                percentage=round(rice_total / total_all * 100, 1) if total_all > 0 else 0,
                crops=rice_crops
            ))
    
    # 2. 旱地作物分解
    if mode in ["crop", "both"]:
        dryland_crops = []
        for name in dryland_names:
            crop_total = crop_totals.get(name, 0)
            area = dryland_areas.get(name, 0)
            quota = dryland_quotas.get(name, 0)
            
            if area > 0:
                dryland_crops.append(CropBreakdown(
                    name=name,
                    area=round(area, 2),
                    quota=round(quota, 0) if quota > 0 else None,
                    total=round(crop_total, 2),
                    daily_avg=round(crop_total / forecast_days, 2) if forecast_days > 0 else 0,
                    method="定额法" if quota > 0 else "无需求"
                ))
        
        # 按需水量排序
        dryland_crops.sort(key=lambda x: x.total, reverse=True)
        
        if dryland_crops:
            breakdown.append(CategorySummary(
                category="旱地作物",
                total=round(dryland_total, 2),
                percentage=round(dryland_total / total_all * 100, 1) if total_all > 0 else 0,
                crops=dryland_crops
            ))
    
    return breakdown


def _get_rice_areas() -> Dict[str, float]:
    """获取水稻面积"""
    lines = read_file_lines('static_fenqu.txt')
    total_single = 0.0
    total_double = 0.0
    for line in lines[1:]:
        fields = line.split('\t')
        if len(fields) >= 3:
            try:
                total_single += float(fields[1])
                total_double += float(fields[2])
            except:
                pass
    return {'单季稻': total_single, '双季稻': total_double}


def _get_dryland_areas() -> Dict[str, float]:
    """获取旱地作物面积"""
    dryland_names = ['蔬菜', '小麦', '油菜', '瓜果', '豆类']
    area_lines = read_file_lines('in_dry_crop_area.txt')
    header = area_lines[0].split('\t')
    
    crop_indices = {}
    for i, name in enumerate(header):
        if name in dryland_names:
            crop_indices[name] = i
    
    crop_areas = {name: 0.0 for name in dryland_names}
    for line in area_lines[1:]:
        fields = line.split('\t')
        for crop_name, idx in crop_indices.items():
            if idx < len(fields):
                try:
                    crop_areas[crop_name] += float(fields[idx])
                except:
                    pass
    return crop_areas


def _get_dryland_quotas(guarantee_rate: int, month: int) -> Dict[str, float]:
    """获取旱地作物定额"""
    dryland_names = ['蔬菜', '小麦', '油菜', '瓜果', '豆类']
    quota_lines = read_file_lines('static_irrigation_quota.txt')
    prob_map = {50: 0.5, 75: 0.75, 90: 0.9}
    target_prob = prob_map.get(guarantee_rate, 0.9)
    
    crop_quotas = {}
    for line in quota_lines[1:]:
        fields = line.split('\t')
        if len(fields) >= 14:
            crop_name = fields[0]
            if crop_name in dryland_names:
                prob = float(fields[1]) if fields[1] else 0
                if abs(prob - target_prob) < 0.01:
                    month_quota = float(fields[month + 1]) if fields[month + 1] else 0
                    crop_quotas[crop_name] = month_quota
    return crop_quotas


# ============================================================================
# API 端点
# ============================================================================

@app.get("/")
def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "农田灌溉需水计算API",
        "version": "1.0.0"
    }


@app.get("/api/areas")
def api_get_areas():
    """获取灌区列表"""
    try:
        areas = get_areas()
        return {"success": True, "areas": areas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/crops")
def api_get_crops():
    """获取作物列表"""
    try:
        lines = read_file_lines('static_irrigation_quota.txt')
        crops = []
        seen = set()
        for line in lines[1:]:
            fields = line.split('\t')
            if fields[0] not in seen:
                seen.add(fields[0])
                crops.append(fields[0])
        return {"success": True, "crops": crops}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/preview")
def api_get_preview():
    """获取参数预览"""
    try:
        from config import WARMUP_DAYS, CALCULATION_MODE
        
        # 读取时间配置
        time_lines = read_file_lines('in_TIME.txt')
        start_date_str = time_lines[0].split('\t')[1] if time_lines else "2025/07/15"
        forecast_days = int(time_lines[1].split('\t')[1]) if len(time_lines) > 1 else 16
        
        start_date = datetime.strptime(start_date_str, '%Y/%m/%d')
        month = start_date.month
        
        # 获取灌区数据
        areas = get_areas()
        total_single = sum(a['single_crop_area'] for a in areas)
        total_double = sum(a['double_crop_area'] for a in areas)
        total_dry = sum(a['dry_land_area'] for a in areas)
        
        # 获取保证率
        guarantee_rate = get_guarantee_rate()
        
        # 获取有效作物
        active_crops = get_active_crops(month, guarantee_rate)
        
        # 获取当前生育期
        period, eva_ratio, water_level = get_current_period(start_date)
        
        # 获取渗漏系数和轮灌批次
        leakage = areas[0]['paddy_leakage'] if areas else 2.0
        rotation = areas[0]['rotation_batches'] if areas else 10
        
        preview = ParameterPreview(
            start_date=start_date_str,
            forecast_days=forecast_days,
            warmup_days=WARMUP_DAYS,
            guarantee_rate=guarantee_rate,
            mode=CALCULATION_MODE,
            active_crops=active_crops,
            total_single_crop=total_single,
            total_double_crop=total_double,
            total_dry_land=total_dry,
            current_period=period,
            eva_ratio=eva_ratio,
            leakage=leakage,
            rotation_batches=rotation
        )
        
        return {"success": True, "preview": preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 面积编辑 API
# ============================================================================

class CropAreasResponse(BaseModel):
    """作物面积响应"""
    success: bool
    rice: Dict[str, float]      # {"单季稻": 551.01, "双季稻": 164.42}
    dryland: Dict[str, float]   # {"小麦": 45.0, ...}


class UpdateAreasRequest(BaseModel):
    """更新面积请求"""
    areas: Dict[str, float]  # {"单季稻": 500, "蔬菜": 80, ...}


@app.get("/api/crop-areas", response_model=CropAreasResponse)
def api_get_crop_areas():
    """获取各作物当前面积"""
    try:
        rice_areas = _get_rice_areas()
        dryland_areas = _get_dryland_areas()
        
        return CropAreasResponse(
            success=True,
            rice=rice_areas,
            dryland=dryland_areas
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/crop-areas")
def api_update_crop_areas(request: UpdateAreasRequest):
    """更新作物面积（持久化写入文件）"""
    try:
        rice_names = ['单季稻', '双季稻']
        dryland_names = ['小麦', '油菜', '蔬菜', '瓜果', '豆类']
        
        # 分离水稻和旱地作物
        rice_updates = {k: v for k, v in request.areas.items() if k in rice_names}
        dryland_updates = {k: v for k, v in request.areas.items() if k in dryland_names}
        
        # 更新水稻面积
        if rice_updates:
            _update_rice_areas(rice_updates)
        
        # 更新旱地作物面积
        if dryland_updates:
            _update_dryland_areas(dryland_updates)
        
        return {"success": True, "message": "面积已更新"}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"{str(e)}\n{traceback.format_exc()}")


def _update_rice_areas(updates: Dict[str, float]):
    """
    更新水稻面积到 static_fenqu.txt
    按原有比例分配到各灌区
    """
    filepath = os.path.join(parent_dir, 'static_fenqu.txt')
    lines = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 计算当前总面积
    current_single = 0.0
    current_double = 0.0
    data_lines = []
    
    for i, line in enumerate(lines):
        if i == 0:  # 表头
            continue
        fields = line.strip().split('\t')
        if len(fields) >= 3:
            try:
                current_single += float(fields[1])
                current_double += float(fields[2])
                data_lines.append((i, fields))
            except:
                pass
    
    # 计算缩放比例
    new_single = updates.get('单季稻', current_single)
    new_double = updates.get('双季稻', current_double)
    
    single_ratio = new_single / current_single if current_single > 0 else 1.0
    double_ratio = new_double / current_double if current_double > 0 else 1.0
    
    # 按比例更新各灌区
    for idx, fields in data_lines:
        try:
            fields[1] = str(round(float(fields[1]) * single_ratio, 3))
            fields[2] = str(round(float(fields[2]) * double_ratio, 3))
            lines[idx] = '\t'.join(fields) + '\n'
        except:
            pass
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def _update_dryland_areas(updates: Dict[str, float]):
    """
    更新旱地作物面积到 in_dry_crop_area.txt
    按原有比例分配到各灌区
    """
    filepath = os.path.join(parent_dir, 'in_dry_crop_area.txt')
    lines = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到表头和数据行
    header_idx = None
    header_fields = None
    data_start = None
    
    for i, line in enumerate(lines):
        if line.startswith('#'):
            continue
        if header_idx is None:
            header_idx = i
            header_fields = line.strip().split('\t')
            data_start = i + 1
            break
    
    if header_fields is None:
        return
    
    # 找到各作物的列索引
    crop_indices = {}
    for crop_name in ['小麦', '油菜', '蔬菜', '瓜果', '豆类']:
        if crop_name in header_fields:
            crop_indices[crop_name] = header_fields.index(crop_name)
    
    # 计算当前总面积
    current_totals = {name: 0.0 for name in crop_indices.keys()}
    data_lines = []
    
    for i in range(data_start, len(lines)):
        line = lines[i]
        if not line.strip() or line.startswith('#'):
            continue
        fields = line.strip().split('\t')
        data_lines.append((i, fields))
        
        for crop_name, col_idx in crop_indices.items():
            if col_idx < len(fields):
                try:
                    current_totals[crop_name] += float(fields[col_idx])
                except:
                    pass
    
    # 计算缩放比例并更新
    for crop_name, new_total in updates.items():
        if crop_name not in crop_indices:
            continue
        
        col_idx = crop_indices[crop_name]
        current = current_totals.get(crop_name, 0)
        ratio = new_total / current if current > 0 else 1.0
        
        for idx, fields in data_lines:
            if col_idx < len(fields):
                try:
                    old_val = float(fields[col_idx])
                    fields[col_idx] = str(round(old_val * ratio, 2))
                except:
                    pass
    
    # 写回文件
    for idx, fields in data_lines:
        lines[idx] = '\t'.join(fields) + '\n'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)


@app.post("/api/calculate", response_model=CalculateResponse)
def api_calculate(request: CalculateRequest):
    """执行灌溉需水计算"""
    try:
        from calculator import Calculator
        from config import WARMUP_DAYS
        from utils import combine_results
        
        # 1. 更新时间配置文件
        time_config = f"ForcastDate\t{request.start_date}\nForcastDays\t{request.forecast_days}\n"
        time_file = os.path.join(parent_dir, 'in_TIME.txt')
        with open(time_file, 'w', encoding='utf-8') as f:
            f.write(time_config)
        
        # 2. 更新保证率
        update_guarantee_rate(request.guarantee_rate)
        
        # 3. 执行计算
        calculator = Calculator(parent_dir, verbose=False)
        calculator.load_data()
        
        # 根据模式执行计算
        results = {}
        if request.mode in ["crop", "both"]:
            calculator.set_mode("crop", "OUT_GGXS_C.txt", "OUT_PYCS_C.txt")
            calculator.run_calculation()
            results['crop'] = calculator.export_results(return_data=True)
        
        if request.mode in ["irrigation", "both"]:
            calculator.set_mode("irrigation", "OUT_GGXS_I.txt", "OUT_PYCS_I.txt")
            calculator.run_calculation()
            results['irrigation'] = calculator.export_results(return_data=True)
        
        # 4. 计算总量（从结果字典中提取）
        def sum_daily_totals(data_dict: Dict) -> float:
            """计算逐日数据的总和"""
            total = 0.0
            for date_key, day_data in data_dict.items():
                # day_data 是 {日期: xxx, 灌区1: 值, 灌区2: 值, ...}
                for k, v in day_data.items():
                    if k != '日期':
                        total += float(v)
            return total
        
        # 分别计算水稻和旱地需水量
        rice_irrigation = 0.0
        dryland_irrigation = 0.0
        daily_by_crop = {}  # 各作物逐日数据
        
        if request.mode == "both":
            total_irrigation, total_drainage = combine_results(
                parent_dir,
                results['crop']['irrigation'],
                results['irrigation']['irrigation'],
                results['crop']['drainage'],
                results['irrigation']['drainage']
            )
            dryland_irrigation = sum_daily_totals(results['crop']['irrigation'])
            rice_irrigation = sum_daily_totals(results['irrigation']['irrigation'])
            # 合并逐作物数据
            if 'daily_by_crop' in results.get('crop', {}):
                daily_by_crop = results['crop']['daily_by_crop']
            if 'daily_by_crop' in results.get('irrigation', {}):
                for date, crops in results['irrigation']['daily_by_crop'].items():
                    if date not in daily_by_crop:
                        daily_by_crop[date] = {}
                    daily_by_crop[date].update(crops)
        elif request.mode == "crop":
            total_irrigation = sum_daily_totals(results['crop']['irrigation'])
            total_drainage = sum_daily_totals(results['crop']['drainage'])
            dryland_irrigation = total_irrigation
            daily_by_crop = results['crop'].get('daily_by_crop', {})
        else:
            total_irrigation = sum_daily_totals(results['irrigation']['irrigation'])
            total_drainage = sum_daily_totals(results['irrigation']['drainage'])
            rice_irrigation = total_irrigation
            daily_by_crop = results['irrigation'].get('daily_by_crop', {})
        
        # 5. 构建逐日数据
        daily_data = []
        
        # 选择数据源
        if request.mode == "both":
            # 从文件读取合并后的数据
            output_file = os.path.join(parent_dir, 'data', 'OUT_GGXS_TOTAL.txt')
            drainage_file = os.path.join(parent_dir, 'data', 'OUT_PYCS_TOTAL.txt')
        elif request.mode == "crop":
            output_file = os.path.join(parent_dir, 'data', 'OUT_GGXS_C.txt')
            drainage_file = os.path.join(parent_dir, 'data', 'OUT_PYCS_C.txt')
        else:
            output_file = os.path.join(parent_dir, 'data', 'OUT_GGXS_I.txt')
            drainage_file = os.path.join(parent_dir, 'data', 'OUT_PYCS_I.txt')
        
        # 读取灌溉数据
        irrigation_by_date = {}
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:  # 跳过表头
                    fields = line.strip().split('\t')
                    if len(fields) >= 2:
                        date = fields[0]
                        total = float(fields[-1])  # 最后一列是合计
                        irrigation_by_date[date] = total
        
        # 读取排水数据
        drainage_by_date = {}
        if os.path.exists(drainage_file):
            with open(drainage_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:
                    fields = line.strip().split('\t')
                    if len(fields) >= 2:
                        date = fields[0]
                        total = float(fields[-1])
                        drainage_by_date[date] = total
        
        # 合并数据（以 daily_by_crop 为准）
        for date in sorted(daily_by_crop.keys()):
            crops_data = daily_by_crop.get(date, {})
            # 日灌溉总量 = 该日各作物需水量之和
            daily_irrigation = sum(crops_data.values())
            
            daily_data.append(DailyData(
                date=date,
                irrigation=daily_irrigation,
                drainage=drainage_by_date.get(date, 0),
                crops=crops_data
            ))
        
        # 获取灌区数据
        areas = get_areas()
        area_data = [
            AreaData(
                name=a['name'],
                single_crop_area=a['single_crop_area'],
                double_crop_area=a['double_crop_area'],
                dry_land_area=a['dry_land_area'],
                irrigation=0  # TODO: 计算各灌区灌溉量
            )
            for a in areas
        ]
        
        # 获取参数预览
        start_date = datetime.strptime(request.start_date, '%Y/%m/%d')
        month = start_date.month
        period, eva_ratio, _ = get_current_period(start_date)
        active_crops = get_active_crops(month, request.guarantee_rate)
        
        parameters = ParameterPreview(
            start_date=request.start_date,
            forecast_days=request.forecast_days,
            warmup_days=WARMUP_DAYS,
            guarantee_rate=request.guarantee_rate,
            mode=request.mode,
            active_crops=active_crops,
            total_single_crop=sum(a['single_crop_area'] for a in areas),
            total_double_crop=sum(a['double_crop_area'] for a in areas),
            total_dry_land=sum(a['dry_land_area'] for a in areas),
            current_period=period,
            eva_ratio=eva_ratio,
            leakage=areas[0]['paddy_leakage'] if areas else 2.0,
            rotation_batches=areas[0]['rotation_batches'] if areas else 10
        )
        
        # 计算分类详情（从 daily_by_crop 统一汇总）
        breakdown = calculate_crop_breakdown(
            mode=request.mode,
            guarantee_rate=request.guarantee_rate,
            forecast_days=request.forecast_days,
            month=month,
            daily_by_crop=daily_by_crop
        )
        
        # 从 daily_by_crop 计算真正的总灌溉需水量
        total_irrigation_from_crops = sum(
            sum(crops.values()) for crops in daily_by_crop.values()
        )
        
        return CalculateResponse(
            success=True,
            total_irrigation=total_irrigation_from_crops,
            total_drainage=total_drainage,
            daily_data=daily_data,
            area_data=area_data,
            breakdown=breakdown,
            parameters=parameters,
            message="计算完成"
        )
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        return CalculateResponse(
            success=False,
            total_irrigation=0,
            total_drainage=0,
            daily_data=[],
            area_data=[],
            breakdown=[],
            parameters=ParameterPreview(
                start_date=request.start_date,
                forecast_days=request.forecast_days,
                warmup_days=30,
                guarantee_rate=request.guarantee_rate,
                mode=request.mode,
                active_crops=[],
                total_single_crop=0,
                total_double_crop=0,
                total_dry_land=0,
                current_period="",
                eva_ratio=0,
                leakage=0,
                rotation_batches=0
            ),
            message=error_msg
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

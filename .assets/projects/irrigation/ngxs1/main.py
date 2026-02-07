import os
import time
import sys
import argparse

# 定义文件复制函数
def copy_files_to_root():
    """将结果文件复制到根目录"""
    import shutil
    import os
    
    print("\n=== 复制文件到根目录 ===")
    
    # 定义需要复制的文件
    files_to_copy = [
        'OUT_PYCS_TOTAL.txt',
        'OUT_GGXS_TOTAL.txt'
    ]
    
    # 源目录
    source_dir = 'data'
    
    for filename in files_to_copy:
        source_path = os.path.join(source_dir, filename)
        dest_path = filename
        
        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
                print(f"复制: {filename}")
            elif os.path.exists(dest_path):
                print(f"文件已存在: {filename}")
            else:
                print(f"源文件不存在: {source_path}")
        except Exception as e:
            print(f"复制 {filename} 失败: {e}")
    
    print("文件复制完成")

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 导入重构后的模块
try:
    from calculator import Calculator
except ImportError as e:
    print(f"导入Calculator失败: {e}")
    sys.exit(1)
    
from utils import combine_results
from config import (
    CALCULATION_MODE, OUTPUT_DIR, WARMUP_DAYS,
    MODE_OUTPUT_FILES, CROP_WATER_BALANCE_FILES, CROP_IRRIGATION_FILES,
    TOTAL_OUTPUT_FILES, INPUT_FILES, LOG_CONFIG
)


def print_parameter_preview(calculator):
    """打印计算参数预览，让用户清楚知道使用了哪些数据"""
    from datetime import datetime
    
    print("\n" + "=" * 70)
    print("                         计算参数预览")
    print("=" * 70)
    
    # === 时间配置 ===
    print("\n【时间配置】")
    print(f"  起始日期: {calculator.current_time.strftime('%Y/%m/%d')}")
    print(f"  预测天数: {calculator.forecast_days} 天")
    print(f"  预热天数: {WARMUP_DAYS} 天")
    
    current_month = calculator.current_time.month
    
    # === 旱地作物参数 ===
    if CALCULATION_MODE in ["crop", "both"]:
        print("\n【旱地作物参数】")
        
        # 读取保证率
        try:
            with open(INPUT_FILES['dry_area'], 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip()]
                if len(lines) > 1:
                    first_data = lines[1].split('\t')
                    if len(first_data) > 1:
                        guarantee_rate = first_data[1]
                        print(f"  灌溉保证率: {guarantee_rate}%    ← 来自 {INPUT_FILES['dry_area']}")
        except:
            print("  灌溉保证率: 读取失败")
        
        # 读取当月有需水的作物（只显示旱地作物，排除水稻类）
        dryland_crops = ['蔬菜', '小麦', '油菜', '瓜果', '豆类']
        try:
            with open(INPUT_FILES['crop'], 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
                if lines:
                    active_crops = []
                    for line in lines[1:]:
                        fields = line.split('\t')
                        if len(fields) >= 14:
                            crop_name = fields[0]
                            if crop_name not in dryland_crops:
                                continue  # 跳过非旱地作物
                            prob = float(fields[1]) if fields[1] else 0
                            if prob == 0.9:  # 只显示90%保证率
                                month_quota = float(fields[current_month + 1]) if fields[current_month + 1] else 0
                                if month_quota > 0:
                                    active_crops.append(f"{crop_name}({int(month_quota)}m³/亩)")
                    if active_crops:
                        print(f"  {current_month}月有效作物: {', '.join(active_crops)}")
                    else:
                        print(f"  {current_month}月有效作物: 无（当月定额为0）")
        except Exception as e:
            print(f"  作物定额: 读取失败 ({e})")
        
        # 旱地面积统计
        total_dry = sum(area.dry_land_area for area in calculator.irrigation_manager.irrigation_areas)
        print(f"  旱地总面积: {total_dry:.1f} km²")
    
    # === 水稻灌溉参数 ===
    if CALCULATION_MODE in ["irrigation", "both"]:
        print("\n【水稻灌溉参数】")
        
        # 单季稻
        total_single = sum(area.single_crop_area for area in calculator.irrigation_manager.irrigation_areas)
        if total_single > 0:
            print(f"  单季稻面积: {total_single:.1f} km²")
            try:
                with open('static_single_crop.txt', 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip() and not l.startswith('#') and not l.startswith('-')]
                    for line in lines[1:]:  # 跳过表头
                        parts = line.split()
                        if len(parts) >= 7:
                            start_date = parts[0]
                            end_date = parts[1]
                            eva_ratio = parts[3]
                            h_min = parts[4]
                            h_design = parts[5]
                            h_max = parts[6]
                            # 检查当前日期是否在此期间
                            try:
                                start = datetime.strptime(start_date, '%Y/%m/%d')
                                end = datetime.strptime(end_date, '%Y/%m/%d')
                                if start <= calculator.current_time <= end:
                                    print(f"    当前生育期: {start_date} ~ {end_date}")
                                    print(f"    蒸发系数: {eva_ratio}    ← 来自 static_single_crop.txt")
                                    print(f"    水位控制: {h_min}-{h_design}-{h_max} mm (下限-设计-上限)")
                                    break
                            except:
                                pass
            except Exception as e:
                print(f"    生育期参数: 读取失败 ({e})")
        
        # 双季稻
        total_double = sum(area.double_crop_area for area in calculator.irrigation_manager.irrigation_areas)
        if total_double > 0:
            print(f"  双季稻面积: {total_double:.1f} km²")
        
        # 渗漏系数和轮灌批次
        if calculator.irrigation_manager.irrigation_areas:
            first_area = calculator.irrigation_manager.irrigation_areas[0]
            print(f"  渗漏系数: {first_area.paddy_leakage} mm/d    ← 来自 static_fenqu.txt")
            print(f"  轮灌批次: {first_area.rotation_batches}    ← 来自 static_fenqu.txt")
    
    # === 气象数据 ===
    print("\n【气象数据】")
    if calculator.irrigation_manager.irrigation_areas:
        first_area = calculator.irrigation_manager.irrigation_areas[0]
        rain_days = len(first_area.rainfall_data)
        eva_days = len(first_area.evaporation_data)
        print(f"  降雨数据: {INPUT_FILES['rainfall']} ({rain_days} 天)")
        print(f"  蒸发数据: {INPUT_FILES['evaporation']} ({eva_days} 天)")
    
    print("\n" + "=" * 70)
    print("  如需修改参数，请编辑对应文件后重新运行")
    print("=" * 70)

def setup_logging(args):
    """设置日志级别"""
    # 根据命令行参数设置日志级别
    if args.quiet:
        # 安静模式，仅输出错误
        LOG_CONFIG['enabled'] = True
        for key in LOG_CONFIG['levels']:
            LOG_CONFIG['levels'][key] = False
        LOG_CONFIG['levels']['errors'] = True
    elif args.verbose:
        # 详细模式，输出所有信息
        LOG_CONFIG['enabled'] = True
        for key in LOG_CONFIG['levels']:
            LOG_CONFIG['levels'][key] = True
        LOG_CONFIG['verbose'] = True
    else:
        # 自定义特定的日志级别
        if args.log_levels:
            for level in args.log_levels:
                if level in LOG_CONFIG['levels']:
                    LOG_CONFIG['levels'][level] = True
    
    # 调试模式
    if args.debug:
        LOG_CONFIG['verbose'] = True
        LOG_CONFIG['levels']['file_io'] = True
        LOG_CONFIG['levels']['errors'] = True
        LOG_CONFIG['levels']['warnings'] = True

def check_required_files():
    """检查必要的输入文件是否存在"""
    from utils import read_data_file
    from config import log
    
    log('file_io', "\n=== 检查必要文件 ===")
    required_files = [
        'time_config',     # 时间配置
        'area_config',     # 区域配置
        'fenqu'            # 分区数据
    ]
    
    if CALCULATION_MODE in ["crop", "both"]:
        required_files.extend(['crop', 'dry_area'])
    
    missing_files = []
    for key in required_files:
        file_name = INPUT_FILES[key]
        try:
            # 仅检查文件是否可读
            read_data_file(file_name, debug=LOG_CONFIG['levels'].get('file_io', False))
            log('file_io', f"✓ {file_name} - 已找到")
        except SystemExit:
            missing_files.append(file_name)
    
    if missing_files:
        log('errors', "\n警告: 以下必要文件未找到:")
        for file in missing_files:
            log('errors', f"  - {file}")
        log('errors', "\n请确保这些文件在正确的位置，否则程序可能无法正常工作。")
        return False
    
    log('file_io', "所有必要文件已找到")
    return True

def print_calculator_info(calculator):
    # 使用更清晰的模式名称
    mode_display_names = {
        "crop": "旱地作物(dryland)",
        "irrigation": "水稻灌溉(paddy)",
        "both": "综合(both)"
    }
    display_mode = mode_display_names.get(CALCULATION_MODE, CALCULATION_MODE)
    
    print(f"\n计算器信息:")
    print(f"- 使用重构模块: 是")
    print(f"- 灌区数量: {len(calculator.irrigation_manager.irrigation_areas)}")
    print(f"- 灌溉系统: {list(calculator.irrigation_manager.irrigation_systems.keys())}")
    print(f"- 计算模式: {display_mode}")
    print(f"- 计算起始时间: {calculator.current_time}")
    print(f"- 预测天数: {calculator.forecast_days}")

def run_mode(calculator, mode_name):
    # 使用更清晰的模式名称
    mode_display_names = {
        "crop": "旱地作物(dryland)",
        "irrigation": "水稻灌溉(paddy)",
        "both": "综合(both)"
    }
    display_name = mode_display_names.get(mode_name, mode_name)
    
    print(f"\n=== 执行{display_name}模式计算 ===")
    calculator.set_mode(
        mode_name,
        MODE_OUTPUT_FILES[mode_name]['irrigation'],
        MODE_OUTPUT_FILES[mode_name]['drainage']
    )
    calculator.run_calculation()
    # 不使用 return_data=True，确保文件被保存
    results = calculator.export_results(return_data=False)
    # 同时返回数据以便合并
    results = calculator.export_results(return_data=True)
    print(f"{display_name}模式计算完成")
    return results


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='农田灌溉需水计算系统')
    
    # 添加数据目录参数
    parser.add_argument('data_dir', nargs='?', default=None,
                      help='数据目录路径，如不提供则使用当前目录')
    
    # 日志控制
    log_group = parser.add_argument_group('日志控制')
    log_group.add_argument('-q', '--quiet', action='store_true', help='安静模式，只显示错误信息')
    log_group.add_argument('-v', '--verbose', action='store_true', help='详细模式，显示所有调试信息')
    log_group.add_argument('-d', '--debug', action='store_true', help='调试模式')
    log_group.add_argument('--log-levels', nargs='+', choices=list(LOG_CONFIG['levels'].keys()),
                         help='启用特定的日志级别 (可指定多个)')
    
    return parser.parse_args()

def main():
    # 解析命令行参数
    args = parse_args()
    setup_logging(args)
    
    try:
        start_time = time.time()
        print("\n=== 开始执行灌溉计算 ===")
        
        # 获取数据目录
        data_path = args.data_dir if args.data_dir else os.getcwd()
        print(f"使用数据目录: {data_path}")
        
        if not os.path.exists(data_path):
            print(f"错误: 找不到数据目录 {data_path}")
            return
            
        # 将当前工作目录设置为数据目录，这样文件读写都会在正确的目录
        if args.data_dir:
            print(f"切换工作目录到: {data_path}")
            os.chdir(data_path)
        
        # 检查必要文件
        if not check_required_files():
            print("\n警告: 缺少部分必要文件，但尝试继续执行...")
            
        # 启用详细输出以便调试
        verbose = LOG_CONFIG['verbose']
        calculator = Calculator(data_path, verbose=verbose)
        print("\n1. 初始化计算器完成")
        
        # 先加载数据，再打印信息，以便显示正确的时间和预测天数
        calculator.load_data()
        print_parameter_preview(calculator)
        print_calculator_info(calculator)
        
        if CALCULATION_MODE in ["crop", "irrigation"]:
            run_mode(calculator, CALCULATION_MODE)
        else:
            crop_results = run_mode(calculator, "crop")
            irrigation_results = run_mode(calculator, "irrigation")
            print("\n=== 合并计算结果 ===")
            ggxs_total, pycs_total = combine_results(
                data_path,
                crop_results['irrigation'],
                irrigation_results['irrigation'],
                crop_results['drainage'],
                irrigation_results['drainage']
            )
            print(f"总灌溉需水量: {ggxs_total:.6f}")
            print(f"总排水量: {pycs_total:.6f}")
            print("结果合并完成")
        end_time = time.time()
        print(f"\n=== 计算完成! 总耗时: {end_time - start_time:.2f} 秒 ===")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        print("\n详细错误信息:")
        import traceback
        print(traceback.format_exc())
    finally:
        copy_files_to_root()

if __name__ == "__main__":
    main()
import os
import sys
import pandas as pd
import shutil
from scipy import interpolate
from functools import lru_cache
from pathlib import Path

# 从config_mappings.py整合的常量
INPUT_FILES = {
    'HQ_ZQ': 'static_HQ_ZQ.txt',
    'HQ_SK': 'static_HQ_SK.txt',
    'SK': 'input_SK.txt',
    'SW_CS': 'input_SW_CS.txt',
    'SW_PS': 'static_SW_PS.txt',
    'SW_MB': 'input_SW_MB.txt',
    'FQJL': 'input_FQJL.txt',
    'LS_QT': 'input_LS_QT.txt',
    'XS_FN': 'input_XS_FN.txt',
    'XS_ST': 'input_XS_ST.txt',
    'GPS_GGXS': 'input_GPS_GGXS.txt',
    'GPS_PYCS': 'input_GPS_PYCS.txt',
    'FSSN_RULES': 'static_FSSN_RULES.txt'
}

FILE_CATEGORIES = {
    'demand': ['XS_FN', 'XS_ST', 'GPS_GGXS'],
    'inflow': ['FQJL', 'LS_QT', 'SK', 'GPS_PYCS'],
    'other': ['HQ_ZQ', 'HQ_SK', 'FSSN_RULES', 'SW_CS', 'SW_PS', 'SW_MB']
}

DEFAULT_VOLUME_COLUMNS = ['死库容', '低库容', '中库容', '高库容', '超蓄库容']
DEFAULT_LEVEL_COLUMNS = ['死水位', '低水位', '中水位', '高水位', '超蓄水位']

DISTRICT_NAME_MAPPING = {
    "丰惠平原区": "output_hq_FHPYQ",
    "余姚平原上河区": "output_hq_YYPYSHQ",
    "余姚平原下河区": "output_hq_YYPYXHQ",
    "余姚平原姚江上游区": "output_hq_YYPYYJSYQ",
    "余姚平原姚江下游区": "output_hq_YYPYYJXYQ",
    "余姚平原马渚中河区": "output_hq_YYPYMZZHQ",
    "南沙平原区": "output_hq_NSPYQ",
    "姚江沿线大工业用水区": "output_hq_YJYXDGYYSQ",
    "慈溪平原东河区": "output_hq_CXPYDHQ",
    "慈溪平原中河区": "output_hq_CXPYZHQ",
    "慈溪平原西河区": "output_hq_CXPYXHQ",
    "江北镇海平原区": "output_hq_JBZHPYQ",
    "海曙平原区": "output_hq_HSPYQ",
    "绍虞平原区": "output_hq_SYPYQ",
    "舟山大陆用水区": "output_hq_ZSDLYSQ",
    "虞北平原上河区": "output_hq_YBPYSHQ",
    "虞北平原中河区": "output_hq_YBPYZHQ",
    "蜀山平原区": "output_hq_SSPYQ",
    "鄞州调水区": "output_hq_YZTSQ"
}

SLUICE_NAME_MAPPING = {
    "三兴闸.txt": "output_sn_SXZ.txt",
    "上虞枢纽.txt": "output_sn_SYSN.txt",
    "四塘闸_七塘闸.txt": "output_sn_STZQTZ.txt",
    "浦前闸.txt": "output_sn_PQZ.txt",
    "牟山闸.txt": "output_sn_MOUSZ.txt",
    "萧山枢纽.txt": "output_sn_XSSN.txt"
}

SUMMARY_COLUMNS = [
    '平原产水', '其他外供', '河网供水', '水库供水', '合计来水',
    '农业需水', '其他生态需水', '非农需水', '需水量', '净流量',
    '目标容积', '日初容积', '日中容积', '日末容积', '排末容积', '水位生态需水',
    '初河蓄水', '蓄水消后', '缺水(浙东需供)', '末河蓄水', '排河蓄水',
    '排水容积', '河区排水', '容积变化', '排后变化', '纳蓄能力', '低水位以上蓄水量', '总蓄水量', 
    '生态需水', '总需水量', '本地可供水量', '展示本地可供水量'
]
class Config:
    BASE_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent.absolute()))
    INPUT_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / 'data'
    INFLOW_OUT_DIR = DATA_DIR / '01_inflow'
    DEMAND_OUT_DIR = DATA_DIR / '02_demand'
    CALCULATED_OUT_DIR = DATA_DIR / '03_calculated'
    FINAL_OUT_DIR = DATA_DIR / '04_final'
    FILE_SEPARATOR = '\t'
    DATE_COLUMN = '日期'
    INPUT_FILES = INPUT_FILES
    FILE_CATEGORIES = FILE_CATEGORIES
    VOLUME_COLUMNS = DEFAULT_VOLUME_COLUMNS.copy()
    LEVEL_COLUMNS = DEFAULT_LEVEL_COLUMNS.copy()
    FSSN_RULES = {}
    INITIAL_LEVEL_DF = None
    DRAINAGE_LEVEL_DF = None
    TARGET_LEVEL_DF = None
    @classmethod
    def get_input_path(cls, file_key):
        return cls.INPUT_DIR / cls.INPUT_FILES[file_key]
    @classmethod
    def get_output_path(cls, output_dir, filename):
        return output_dir / filename
    @classmethod
    def initialize(cls):
        hq_zq_path = cls.get_input_path('HQ_ZQ')
        try:
            if os.path.exists(hq_zq_path):
                with open(hq_zq_path, 'r', encoding='utf-8') as f:
                    header = f.readline().strip().split(cls.FILE_SEPARATOR)
                cls.VOLUME_COLUMNS = [col for col in header if '库容' in col]
                cls.LEVEL_COLUMNS = [col for col in header if '水位' in col]
                print(f"从文件中读取的库容列: {cls.VOLUME_COLUMNS}")
                print(f"从文件中读取的水位列: {cls.LEVEL_COLUMNS}")
            else:
                print(f"警告: 文件 {hq_zq_path} 不存在，使用默认的库容和水位列")
        except Exception as e:
            print(f"初始化配置时出错: {e}，使用默认的库容和水位列")
    @classmethod
    def ensure_directories(cls):
        dirs = [cls.DATA_DIR, cls.INFLOW_OUT_DIR, cls.DEMAND_OUT_DIR, cls.CALCULATED_OUT_DIR,
                cls.FINAL_OUT_DIR]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
    @classmethod
    def load_level_data(cls):
        cls.INITIAL_LEVEL_DF = DataLoader.read_data(cls.get_input_path('SW_CS'))
        cls.DRAINAGE_LEVEL_DF = DataLoader.read_data(cls.get_input_path('SW_PS'))
        cls.TARGET_LEVEL_DF = DataLoader.read_data(cls.get_input_path('SW_MB'))
    @classmethod
    def load_fssn_rules(cls):
        try:
            fssn_rules_path = cls.get_input_path('FSSN_RULES')
            if os.path.exists(fssn_rules_path):
                fssn_df = DataLoader.read_data(fssn_rules_path)
                cls.FSSN_RULES = {}
                for _, row in fssn_df.iterrows():
                    sluice_name = row['分水枢纽名称']
                    count = int(row['包含区域数量'])
                    if count <= 0:
                        continue
                    districts = []
                    for i in range(count):
                        column_name = f'区域{i+1}'
                        if column_name in row and pd.notna(row[column_name]):
                            districts.append(row[column_name])
                    if districts:
                        cls.FSSN_RULES[sluice_name] = districts
                print(f"已成功加载分水枢纽规则: {len(cls.FSSN_RULES)}个枢纽")
            else:
                print(f"警告: 分水枢纽规则文件 {fssn_rules_path} 不存在，无法加载分水枢纽规则")
        except Exception as e:
            print(f"加载分水枢纽规则时出错: {str(e)}")
class DataLoader:
    @staticmethod
    def read_data(filename):
        return pd.read_csv(filename, sep=Config.FILE_SEPARATOR)
    @staticmethod
    @lru_cache(maxsize=1)
    def load_storage_curves():
        file_path = Config.get_input_path('HQ_ZQ')
        storage_curves = {}
        try:
            df = DataLoader.read_data(file_path)
            for _, row in df.iterrows():
                district = row['分区名称']
                volumes = [row[col] for col in Config.VOLUME_COLUMNS]
                levels = [row[col] for col in Config.LEVEL_COLUMNS]
                storage_curves[district] = {
                    'level_to_volume': interpolate.interp1d(
                        levels, volumes, kind='linear',
                        bounds_error=False, fill_value=(volumes[0], volumes[-1])
                    ),
                    'volume_to_level': interpolate.interp1d(
                        volumes, levels, kind='linear',
                        bounds_error=False, fill_value=(levels[0], levels[-1])
                    )
                }
            return storage_curves
        except Exception as e:
            print(f'加载蓄水曲线时出错: {e}')
            return {}
class ReservoirInflowGenerator:
    @staticmethod
    def generate():
        Config.ensure_directories()
        hq_sk_df = DataLoader.read_data(Config.get_input_path('HQ_SK'))
        sk_df = DataLoader.read_data(Config.get_input_path('SK'))
        district_reservoir_inflow = {}
        for _, row in hq_sk_df.iterrows():
            district = row['分区名称']
            count = int(row['包含水库数量'])
            if count <= 0:
                continue
            print(f"处理河区: {district}, 水库数量: {count}")
            reservoirs = []
            for i in range(count):
                col_name = f'Unnamed: {i+2}'
                if col_name in row and pd.notna(row[col_name]):
                    reservoirs.append(row[col_name])
            if not reservoirs:
                continue
            if district not in district_reservoir_inflow:
                district_reservoir_inflow[district] = pd.Series(0.0, index=range(len(sk_df)))
            for reservoir in reservoirs:
                if reservoir in sk_df.columns:
                    district_reservoir_inflow[district] += sk_df[reservoir].fillna(0)
        print(f"已生成各分区水库来水数据")
        return district_reservoir_inflow
class DistrictDataProcessor:
    @staticmethod
    def collect_district_data(file_category, district):
        result = {}
        for file_key in Config.FILE_CATEGORIES.get(file_category, []):
            try:
                file_path = Config.get_input_path(file_key)
                df = DataLoader.read_data(file_path)
                if district in df.columns:
                    file_name = Config.INPUT_FILES[file_key].split('.')[0]
                    file_name = file_name.replace('static_', '').replace('input_', '')
                    result[file_name] = df[district]
            except Exception as e:
                print(f"从 {file_key} 中获取 {district} 数据时出错: {e}")
        return result
    @staticmethod
    def process_district_data(district, dates, storage_curves, reservoir_inflow=None):
        demand_data = DistrictDataProcessor.collect_district_data('demand', district)
        inflow_data = DistrictDataProcessor.collect_district_data('inflow', district)
        demand_df = pd.DataFrame({Config.DATE_COLUMN: dates})
        inflow_df = pd.DataFrame({Config.DATE_COLUMN: dates})
        demand_mapping = {
            'GPS_GGXS': '农业需水',
            'XS_ST': '其他生态需水',
            'XS_FN': '非农需水'
        }
        for source_key, target_col in demand_mapping.items():
            demand_df[target_col] = demand_data.get(source_key, 0.0)
        demand_df['需水量'] = demand_df['农业需水'] + demand_df['非农需水']
        inflow_mapping = {
            'GPS_PYCS': '平原产水',
            'LS_QT': '其他外供',
            'FQJL': '河网供水',
            'SK': '水库供水'
        }
        for source_key, target_col in inflow_mapping.items():
            if source_key == 'SK' and reservoir_inflow and district in reservoir_inflow:
                inflow_df[target_col] = reservoir_inflow[district].values
            else:
                inflow_df[target_col] = inflow_data.get(source_key, 0.0)
        
        # 定义需要动态平衡的河区（净流量=0）
        BALANCED_DISTRICTS = ['南沙平原区', '海曙平原区', '绍虞平原区', '蜀山平原区']
        
        # 对特殊河区进行动态平衡处理
        if district in BALANCED_DISTRICTS:
            # 计算总需水量（需水量 + 生态需水）
            total_demand = demand_df['需水量'] + demand_df['其他生态需水']
            
            # 动态计算其他外供，确保净流量=0
            # 其他外供 = 总需水量 - 河网供水 - 水库供水
            inflow_df['其他外供'] = total_demand - inflow_df['河网供水'] - inflow_df['水库供水']
            
            print(f"河区 {district} 启用动态平衡模式，其他外供已调整为动态计算值")
        
        inflow_df['合计来水'] = inflow_df[['其他外供', '河网供水', '水库供水']].sum(axis=1)
        save_path = lambda dir_config, filename: Config.get_output_path(dir_config, f"{filename}.txt")
        inflow_df.to_csv(save_path(Config.INFLOW_OUT_DIR, district), sep=Config.FILE_SEPARATOR, index=False)
        demand_df.to_csv(save_path(Config.DEMAND_OUT_DIR, district), sep=Config.FILE_SEPARATOR, index=False)
        df_dict = {'inflow': inflow_df, 'demand': demand_df}
        WaterBalanceCalculator.calculate(district, dates, df_dict, storage_curves)
    @staticmethod
    def generate_categorized_data(reservoir_inflow=None):
        Config.ensure_directories()
        storage_curves = DataLoader.load_storage_curves()
        df_demand = DataLoader.read_data(Config.get_input_path('XS_ST'))
        dates = df_demand[Config.DATE_COLUMN]
        df_level = DataLoader.read_data(Config.get_input_path('SW_CS'))
        districts = [col for col in df_level.columns if col != Config.DATE_COLUMN]
        for district in districts:
            DistrictDataProcessor.process_district_data(district, dates, storage_curves, reservoir_inflow)
class WaterBalanceCalculator:
    @staticmethod
    def calculate(district, dates, df_dict, storage_curves):
        """主计算方法 - 采用main.py中的简化逻辑"""
        # 初始化数据框架
        balance_df = pd.DataFrame({Config.DATE_COLUMN: dates})
        balance_df["合计来水"] = df_dict['inflow']["合计来水"]
        balance_df["需水量"] = df_dict['demand']["需水量"]

        # 首先计算生态需水相关字段
        balance_df["其他生态需水"] = df_dict['demand']["其他生态需水"]
        balance_df["水位生态需水"] = 0.0  # 简化后设为0
        balance_df["生态需水"] = balance_df["其他生态需水"] + balance_df["水位生态需水"]
        balance_df["总需水量"] = balance_df["需水量"] + balance_df["生态需水"]

        # 净流量 = 合计来水 - 总需水量（包含生态需水）
        balance_df["净流量"] = balance_df["合计来水"] - balance_df["总需水量"]
        
        # 初始化所有字段
        for col in ["目标容积", "日初容积", "日中容积", "日末容积", "排末容积", 
                    "水位生态需水", "初河蓄水", "蓄水消后", "缺水(浙东需供)", 
                    "末河蓄水", "排河蓄水", "排水容积", "河区排水", 
                    "容积变化", "排后变化", "纳蓄能力", "低水位以上蓄水量", "总蓄水量"]:
            balance_df[col] = 0.0
        
        # 计算总天数
        first_date = pd.to_datetime(dates.iloc[0])
        last_date = pd.to_datetime(dates.iloc[-1])
        total_days = (last_date - first_date).days 
        
        # 获取初始水位、目标水位和排水位
        first_day_level = Config.INITIAL_LEVEL_DF.loc[0, district]
        target_level = Config.TARGET_LEVEL_DF.loc[0, district]
        drainage_level = Config.DRAINAGE_LEVEL_DF.loc[0, district]
        
        # 将水位转换为对应的容积
        first_day_storage = float(storage_curves[district]['level_to_volume'](first_day_level))
        target_storage = float(storage_curves[district]['level_to_volume'](target_level))
        
        drain_level = drainage_level
        drain_storage = float(storage_curves[district]['level_to_volume'](drain_level))
        print(f"分区: {district}, 排水位: {drain_level}, 排水容积: {drain_storage}")
        
        # 获取高水位和低水位对应的容积
        hq_zq_df = DataLoader.read_data(Config.get_input_path('HQ_ZQ'))
        district_info = hq_zq_df[hq_zq_df['分区名称'] == district].iloc[0]
        high_level = district_info['高水位']
        low_level = district_info['低水位']
        
        high_level_volume = float(storage_curves[district]['level_to_volume'](high_level))
        low_level_volume = float(storage_curves[district]['level_to_volume'](low_level))
        
        print(f"分区: {district}, 高水位: {high_level}, 高水位容积: {high_level_volume}")
        print(f"分区: {district}, 低水位: {low_level}, 低水位容积: {low_level_volume}")
        
        # 对每一天进行计算
        for i in balance_df.index:
            WaterBalanceCalculator._calculate_daily_balance_optimized(
                balance_df, i, district,
                first_day_level, first_day_storage, target_storage, drain_storage,
                total_days, dates, df_dict, high_level_volume, low_level_volume
            )
        
        balance_df.to_csv(
            Config.get_output_path(Config.CALCULATED_OUT_DIR, f"{district}.txt"),
            sep=Config.FILE_SEPARATOR, index=False
        )
        print(f"保存水平衡结果: {district}")

    @staticmethod
    def _calculate_daily_balance_optimized(balance_df, i, district,
                                          first_day_level, first_day_storage, target_storage, drain_storage,
                                          total_days, dates, df_dict, high_level_volume, low_level_volume):
        """优化后的逐日水平衡计算 - 拆分为多个小函数但保持逻辑完全一致"""
        basic_data = WaterBalanceCalculator._calculate_basic_volumes(
            balance_df, i, first_day_storage, target_storage, drain_storage
        )
        eco_data = WaterBalanceCalculator._calculate_ecological_water_demand(
            balance_df, i, basic_data, total_days, dates, df_dict
        )
        supply_data = WaterBalanceCalculator._calculate_external_supply(
            balance_df, i, eco_data, df_dict
        )
        final_data = WaterBalanceCalculator._calculate_final_storage_and_drainage(
            balance_df, i, basic_data, eco_data, supply_data, 
            drain_storage, high_level_volume, low_level_volume
        )
        WaterBalanceCalculator._update_balance_dataframe(balance_df, i, basic_data, eco_data, supply_data, final_data)

    @staticmethod
    def _calculate_basic_volumes(balance_df, i, first_day_storage, target_storage, drain_storage):
        """修改后的基础容积数据计算 - 第二天日初容积=前一天排末容积"""
        net_flow = balance_df.loc[i, "净流量"]
        
        if i == 0:
            day_initial_storage = first_day_storage
        else:
            # 第二天的日初容积等于前一天的排末容积
            day_initial_storage = balance_df.loc[i-1, "排末容积"]
        
        # 计算日中容积：日初容积 + 净流量
        day_middle_storage = day_initial_storage + net_flow
        
        return {
            'net_flow': net_flow,
            'day_initial_storage': day_initial_storage,
            'day_middle_storage': day_middle_storage,
            'initial_river_storage': 0.0,
            'target_storage': target_storage,
            'drain_storage': drain_storage
        }

    @staticmethod
    def _calculate_ecological_water_demand(balance_df, i, basic_data, total_days, dates, df_dict):
        """简化后的生态需水计算 - 不再基于河区蓄水状态"""
        eco_water_demand = 0.0
        post_consumption_storage = 0.0
        
        return {
            'eco_water_demand': eco_water_demand,
            'post_consumption_storage': post_consumption_storage
        }

    @staticmethod
    def _calculate_external_supply(balance_df, i, eco_data, df_dict):
        """简化后的外部补供需求计算 - 直接使用已计算的总需水量"""
        total_demand = balance_df.loc[i, "总需水量"]
        total_inflow = balance_df.loc[i, "合计来水"]
        external_supply = max(total_demand - total_inflow, 0)
        final_eco_water_demand = 0.0
        other_eco_water = balance_df.loc[i, "其他生态需水"]

        return {
            'external_supply': external_supply,
            'final_eco_water_demand': final_eco_water_demand,
            'other_eco_water': other_eco_water,
            'total_demand': total_demand
        }

    @staticmethod
    def _calculate_final_storage_and_drainage(balance_df, i, basic_data, eco_data, supply_data, 
                                            drain_storage, high_level_volume, low_level_volume):
        """修改后的蓄水和排水计算 - 实现正确的日末容积和排末容积逻辑"""
        net_flow = basic_data['net_flow']
        volume_change = net_flow
        
        # 日中容积（已在basic_data中计算）
        day_middle_storage = basic_data['day_middle_storage']
        
        # 日末容积 = 日中容积 + 缺水(浙东需供)
        external_supply = supply_data['external_supply']
        day_end_storage = day_middle_storage + external_supply
        
        # 河区排水：超出排水容积的部分需要排掉
        drainage = max(0, day_end_storage - drain_storage)
        
        # 排末容积 = 日末容积 - 河区排水
        end_storage_after_drainage = day_end_storage - drainage
        
        post_drainage_change = volume_change - drainage
        absorption_capacity = high_level_volume - end_storage_after_drainage
        above_low_level_storage = max(0, end_storage_after_drainage - low_level_volume)
        total_storage = end_storage_after_drainage
        
        return {
            'end_river_storage': 0.0,
            'volume_change': volume_change,
            'day_middle_storage': day_middle_storage,
            'day_end_storage': day_end_storage,
            'drainage': drainage,
            'end_storage_after_drainage': end_storage_after_drainage,
            'end_river_storage_after_drainage': 0.0,
            'post_drainage_change': post_drainage_change,
            'absorption_capacity': absorption_capacity,
            'above_low_level_storage': above_low_level_storage,
            'total_storage': total_storage
        }

    @staticmethod
    def _update_balance_dataframe(balance_df, i, basic_data, eco_data, supply_data, final_data):
        """修改后的DataFrame更新 - 正确设置日中容积、日末容积和排末容积"""
        balance_df.loc[i, "目标容积"] = basic_data['target_storage']
        balance_df.loc[i, "日初容积"] = basic_data['day_initial_storage']
        balance_df.loc[i, "日中容积"] = final_data['day_middle_storage']
        balance_df.loc[i, "日末容积"] = final_data['day_end_storage']
        balance_df.loc[i, "排末容积"] = final_data['end_storage_after_drainage']
        balance_df.loc[i, "排水容积"] = basic_data['drain_storage']
        balance_df.loc[i, "初河蓄水"] = 0.0
        balance_df.loc[i, "水位生态需水"] = supply_data['final_eco_water_demand']
        balance_df.loc[i, "蓄水消后"] = 0.0
        balance_df.loc[i, "缺水(浙东需供)"] = supply_data['external_supply']
        balance_df.loc[i, "末河蓄水"] = 0.0
        balance_df.loc[i, "容积变化"] = final_data['volume_change']
        balance_df.loc[i, "河区排水"] = final_data['drainage']
        balance_df.loc[i, "排河蓄水"] = 0.0
        balance_df.loc[i, "排后变化"] = final_data['post_drainage_change']
        balance_df.loc[i, "纳蓄能力"] = final_data['absorption_capacity']
        balance_df.loc[i, "低水位以上蓄水量"] = final_data['above_low_level_storage']
        balance_df.loc[i, "总蓄水量"] = final_data['total_storage']

# 整合自fssn_data_generator.py
class FSSnDataGenerator:
    @staticmethod
    def get_all_leaf_districts(sluice_name, processed_sluices=None):
        """递归获取分水枢纽的所有叶子节点（最终分区）"""
        if processed_sluices is None:
            processed_sluices = set()
        
        # 防止循环引用
        if sluice_name in processed_sluices:
            print(f'警告: 检测到循环引用，跳过分水枢纽 {sluice_name}')
            return []
        
        processed_sluices.add(sluice_name)
        
        if sluice_name not in Config.FSSN_RULES:
            # 如果不在枢纽规则中，可能是一个最终分区
            return [sluice_name]
        
        districts = Config.FSSN_RULES[sluice_name]
        all_leaf_districts = []
        
        for district in districts:
            if district in Config.FSSN_RULES:
                # 这是一个嵌套的分水枢纽，递归获取其叶子节点
                nested_districts = FSSnDataGenerator.get_all_leaf_districts(
                    district, processed_sluices.copy()
                )
                all_leaf_districts.extend(nested_districts)
            else:
                # 这是一个最终分区
                all_leaf_districts.append(district)
        
        return all_leaf_districts
    
    @staticmethod
    def get_nested_sluice_data(sluice_name, district_supplement_data, dates, processed_sluices=None):
        """递归获取嵌套分水枢纽的缺水(浙东需供)数据"""
        if processed_sluices is None:
            processed_sluices = set()
        
        # 防止循环引用
        if sluice_name in processed_sluices:
            print(f'警告: 检测到循环引用，跳过分水枢纽 {sluice_name}')
            return pd.Series([0.0] * len(dates))
        
        processed_sluices.add(sluice_name)
        
        if sluice_name not in Config.FSSN_RULES:
            print(f'警告: 分水枢纽 {sluice_name} 的规则未找到')
            return pd.Series([0.0] * len(dates))
        
        districts = Config.FSSN_RULES[sluice_name]
        sluice_supplement = pd.Series([0.0] * len(dates))
        
        for district in districts:
            if district in district_supplement_data:
                # 这是一个实际的分区，直接使用其数据
                sluice_supplement += district_supplement_data[district]
            elif district in Config.FSSN_RULES:
                # 这是一个嵌套的分水枢纽，递归处理
                print(f'处理嵌套分水枢纽: {district}')
                nested_data = FSSnDataGenerator.get_nested_sluice_data(
                    district, district_supplement_data, dates, processed_sluices.copy()
                )
                sluice_supplement += nested_data
            else:
                print(f'警告: 区域 {district} 既不在分区数据中，也不在分水枢纽规则中')
        
        return sluice_supplement

    @staticmethod
    def generate_supplement_data():
        print("开始生成分水枢纽缺水(浙东需供)数据...")
        Config.ensure_directories()
        first_district = None
        for district_file in os.listdir(Config.CALCULATED_OUT_DIR):
            if district_file.endswith('.txt'):
                first_district = district_file.split('.')[0]
                break
        if not first_district:
            print('未找到任何分区数据文件，无法处理分水枢纽缺水(浙东需供)数据')
            return
        first_file_path = os.path.join(Config.CALCULATED_OUT_DIR, f"{first_district}.txt")
        first_df = DataLoader.read_data(first_file_path)
        dates = first_df[Config.DATE_COLUMN]
        district_supplement_data = {}
        for district_file in os.listdir(Config.CALCULATED_OUT_DIR):
            if district_file.endswith('.txt'):
                district_name = district_file.split('.')[0]
                file_path = os.path.join(Config.CALCULATED_OUT_DIR, district_file)
                district_df = DataLoader.read_data(file_path)
                if '缺水(浙东需供)' in district_df.columns:
                    district_supplement_data[district_name] = district_df['缺水(浙东需供)'].copy()
        
        # 创建临时目录存放分水枢纽数据
        fssn_dir = Config.DATA_DIR / 'fssn_data'
        os.makedirs(fssn_dir, exist_ok=True)
        
        for sluice_name, districts in Config.FSSN_RULES.items():
            try:
                sluice_df = pd.DataFrame({Config.DATE_COLUMN: dates})
                sluice_supplement = pd.Series([0.0] * len(dates))
                
                # 获取该枢纽的所有最终分区（叶子节点）
                all_leaf_districts = FSSnDataGenerator.get_all_leaf_districts(sluice_name)
                print(f'分水枢纽 {sluice_name} 管辖的所有最终分区: {all_leaf_districts}')
                
                # 为每个最终分区添加数据列并累加到总和中
                for leaf_district in all_leaf_districts:
                    if leaf_district in district_supplement_data:
                        sluice_df[leaf_district] = district_supplement_data[leaf_district]
                        sluice_supplement += district_supplement_data[leaf_district]
                        print(f'分水枢纽 {sluice_name} 包含分区: {leaf_district}')
                    else:
                        print(f'警告: 分区 {leaf_district} 的缺水数据未找到')
                
                sluice_df['日引水量(万m3)'] = sluice_supplement
                sluice_df['日均引水流量(m3/s)'] = sluice_df['日引水量(万m3)'] / 8.64
                
                # 保存分水枢纽数据到临时目录
                output_file = os.path.join(fssn_dir, f"{sluice_name}.txt")
                sluice_df.to_csv(output_file, sep=Config.FILE_SEPARATOR, index=False)
                print(f'分水枢纽 {sluice_name} 处理完成，数据保存至 {output_file}')
                print(f'分水枢纽 {sluice_name} 日缺水(浙东需供)合计: {sluice_supplement.iloc[0]:.2f} 万m³')
                print(f'分水枢纽 {sluice_name} 包含分区总数: {len(all_leaf_districts)}个')
                
            except Exception as e:
                print(f'处理分水枢纽 {sluice_name} 时出错: {str(e)}')

# 整合自data_output_processor.py
class DataOutputProcessor:
    @staticmethod
    def generate_district_summary():
        """为每个区域生成时间维度的汇总报表。类似于所有区域的汇总，但是针对每个区域单独进行处理。"""
        print("开始生成每个区域的时间维度汇总文件...")
        base_dir = str(Config.BASE_DIR)
        hq_files = [f for f in os.listdir(base_dir)
                   if f.startswith('output_hq_') and f.endswith('.txt')
                   and not f.startswith('output_hq_all_')
                   and f != 'output_hq_all.txt']
        
        if not hq_files:
            print("未找到任何区域数据文件！")
            return False
            
        print(f"找到 {len(hq_files)} 个区域数据文件")
        
        # 确保目标目录存在
        district_summary_dir = os.path.join(base_dir, "data", "05_discrict")
        os.makedirs(district_summary_dir, exist_ok=True)
        
        for hq_file in hq_files:
            file_path = os.path.join(base_dir, hq_file)
            try:
                df = pd.read_csv(file_path, sep=Config.FILE_SEPARATOR)
                
                # 生成总和汇总文件
                total_df = pd.DataFrame()
                start_date = df[Config.DATE_COLUMN].iloc[0]
                end_date = df[Config.DATE_COLUMN].iloc[-1]
                total_df['时间段'] = [f"{start_date}至{end_date}"]
                
                # 对所有数值列进行汇总，但对特殊字段单独处理
                for col in df.columns:
                    if col != Config.DATE_COLUMN and pd.api.types.is_numeric_dtype(df[col]):
                        # 对"初河蓄水"字段，只选取第一行的值而不求和
                        if col == "初河蓄水":
                            total_df[col] = [df[col].iloc[0]]
                        else:
                            total_df[col] = [df[col].sum()]
                
                # 生成输出文件名
                base_name = os.path.splitext(hq_file)[0]
                output_file = os.path.join(district_summary_dir, f"{base_name}_total.txt")
                total_df.to_csv(output_file, sep=Config.FILE_SEPARATOR, index=False)
                print(f"区域汇总文件已生成：{output_file}")
                
            except Exception as e:
                print(f"处理区域文件 {hq_file} 时出错：{str(e)}")
        
        print("所有区域汇总文件生成完成")
        return True
    
    @staticmethod
    def merge_and_output_final_data():
        Config.ensure_directories()
        try:
            calculated_files = os.listdir(Config.CALCULATED_OUT_DIR)
            district_files = [f for f in calculated_files if f.endswith('.txt')]
        except Exception as e:
            print(f"读取calculated目录文件失败: {e}")
            return
        print(f"开始合并数据并输出到final目录")
        for file in district_files:
            district = os.path.splitext(file)[0]
            try:
                calculated_file = Config.get_output_path(Config.CALCULATED_OUT_DIR, file)
                inflow_file = Config.get_output_path(Config.INFLOW_OUT_DIR, file)
                demand_file = Config.get_output_path(Config.DEMAND_OUT_DIR, file)
                calculated_df = None
                inflow_df = None
                demand_df = None
                if os.path.exists(calculated_file):
                    calculated_df = pd.read_csv(calculated_file, sep=Config.FILE_SEPARATOR)
                else:
                    print(f"找不到分区 {district} 的calculated数据文件")
                    continue
                if os.path.exists(inflow_file):
                    inflow_df = pd.read_csv(inflow_file, sep=Config.FILE_SEPARATOR)
                else:
                    print(f"找不到分区 {district} 的inflow数据文件")
                    continue
                if os.path.exists(demand_file):
                    demand_df = pd.read_csv(demand_file, sep=Config.FILE_SEPARATOR)
                else:
                    print(f"找不到分区 {district} 的demand数据文件")
                    continue
                result_df = pd.DataFrame()
                result_df[Config.DATE_COLUMN] = calculated_df[Config.DATE_COLUMN]
                inflow_cols_to_include = [col for col in inflow_df.columns
                                         if col != Config.DATE_COLUMN and col != '合计来水']
                for col in inflow_cols_to_include:
                    result_df[col] = inflow_df[col]
                result_df['合计来水'] = inflow_df['合计来水']
                demand_cols_to_include = [col for col in demand_df.columns
                                         if col != Config.DATE_COLUMN and col != '需水量']
                for col in demand_cols_to_include:
                    result_df[col] = demand_df[col]
                result_df['需水量'] = demand_df['需水量']
                calculated_cols_to_include = [col for col in calculated_df.columns
                                         if col != Config.DATE_COLUMN
                                         and col != '合计来水'
                                         and col != '需水量'
                                         and col != '缺口'
                                         and col != '水位生态需水']
                for col in calculated_cols_to_include:
                    result_df[col] = calculated_df[col]
                
                # 添加生态需水和总需水的计算
                # 确保数据列存在，如果不存在则设置为0
                if '其他生态需水' not in result_df.columns:
                    result_df['其他生态需水'] = 0
                if '水位生态需水' not in calculated_df.columns:
                    calculated_df['水位生态需水'] = 0
                    result_df['水位生态需水'] = 0
                else:
                    result_df['水位生态需水'] = calculated_df['水位生态需水']
                    
                result_df['生态需水'] = result_df['其他生态需水'] + result_df['水位生态需水']
                result_df['总需水量'] = result_df['需水量'] + result_df['生态需水']
                
                # 添加本地可供水量字段
                result_df['本地可供水量'] = result_df['合计来水'] + result_df['初河蓄水'].apply(lambda x: max(x, 0))
                
                output_file = Config.get_output_path(Config.FINAL_OUT_DIR, file)
                result_df.to_csv(output_file, sep=Config.FILE_SEPARATOR, index=False)
                print(f"完成分区 {district} 数据合并并输出到 {output_file}")
            except Exception as e:
                print(f"处理分区 {district} 时出错: {e}")
        print(f"数据合并完成")

    @staticmethod
    def copy_and_rename_files():
        src_dir = Config.FINAL_OUT_DIR
        dst_dir = Config.BASE_DIR
        name_mapping = DISTRICT_NAME_MAPPING
        copied_files = []
        for chinese_name, code_name in name_mapping.items():
            src_file = src_dir / f"{chinese_name}.txt"
            dst_file = dst_dir / f"{code_name}.txt"
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                print(f"已复制: {chinese_name}.txt -> {code_name}.txt")
                copied_files.append(f"{code_name}.txt")
            else:
                print(f"未找到源文件: {chinese_name}.txt")
        print(f">n总共复制了 {len(copied_files)} 个文件到根目录")
        return copied_files

    @staticmethod
    def copy_and_rename_fssn_files():
        """将临时枢纽目录下的文件复制到项目根目录，并按规则重命名"""
        import shutil
        # 源目录和目标目录
        src_dir = Config.DATA_DIR / 'fssn_data'
        dst_dir = Config.BASE_DIR
        
        # 如果源目录不存在，创建它
        if not os.path.exists(src_dir):
            os.makedirs(src_dir, exist_ok=True)
            print(f"创建分水枢纽源目录 {src_dir}")
        
        # 命名映射规则
        name_mapping = SLUICE_NAME_MAPPING
        
        # 复制并重命名文件
        copied_files = []
        for src_name, dst_name in name_mapping.items():
            src_file = src_dir / src_name
            dst_file = dst_dir / dst_name
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                print(f"已复制分水枢纽文件: {src_name} -> {dst_name}")
                copied_files.append(dst_name)
            else:
                print(f"未找到分水枢纽源文件: {src_name}")
        
        print(f"\n总共复制了 {len(copied_files)} 个分水枢纽文件到根目录")
        return copied_files

    @staticmethod
    def generate_all_hq_summary():
        print("开始生成河区数据汇总文件...")
        columns_to_sum = SUMMARY_COLUMNS
        base_dir = str(Config.BASE_DIR)
        
        # 明确列出要汇总的19个河区文件
        all_hq_files = [
            'output_hq_CXPYDHQ.txt',
            'output_hq_CXPYXHQ.txt',
            'output_hq_CXPYZHQ.txt',
            'output_hq_FHPYQ.txt',
            'output_hq_HSPYQ.txt',
            'output_hq_JBZHPYQ.txt',
            'output_hq_NSPYQ.txt',
            'output_hq_SSPYQ.txt',
            'output_hq_SYPYQ.txt',
            'output_hq_YBPYSHQ.txt',
            'output_hq_YBPYZHQ.txt',
            'output_hq_YJYXDGYYSQ.txt',
            'output_hq_YYPYMZZHQ.txt',
            'output_hq_YYPYSHQ.txt',
            'output_hq_YYPYXHQ.txt',
            'output_hq_YYPYYJSYQ.txt',
            'output_hq_YYPYYJXYQ.txt',
            'output_hq_YZTSQ.txt',
            'output_hq_ZSDLYSQ.txt'
        ]
        
        # 检查文件是否存在
        hq_files = [f for f in all_hq_files if os.path.exists(os.path.join(base_dir, f))]
        if not hq_files:
            print("未找到任何河区数据文件！")
            return False
        print(f"找到 {len(hq_files)} 个河区数据文件（共19个）")
        first_file = os.path.join(base_dir, hq_files[0])
        first_df = pd.read_csv(first_file, sep=Config.FILE_SEPARATOR)
        summary_df = pd.DataFrame()
        summary_df[Config.DATE_COLUMN] = first_df[Config.DATE_COLUMN]
        for col in columns_to_sum:
            summary_df[col] = 0.0
        for hq_file in hq_files:
            file_path = os.path.join(base_dir, hq_file)
            try:
                df = pd.read_csv(file_path, sep=Config.FILE_SEPARATOR)
                if not all(df[Config.DATE_COLUMN].values == summary_df[Config.DATE_COLUMN].values):
                    print(f"警告：文件 {hq_file} 的日期与第一个文件不匹配，跳过")
                    continue
                for col in columns_to_sum:
                    if col in df.columns:
                        summary_df[col] += df[col].fillna(0).values
                    else:
                        print(f"警告：文件 {hq_file} 中没有找到列 '{col}'")
                print(f"已处理文件：{hq_file}")
            except Exception as e:
                print(f"处理文件 {hq_file} 时出错：{str(e)}")
        
        # 修复容积相关字段的汇总逻辑：重新计算河区排水和排末容积
        print("正在修复全汇总文件的容积相关字段逻辑...")
        for i in summary_df.index:
            # 重新计算河区排水：max(0, 日末容积 - 排水容积)
            day_end_storage = summary_df.loc[i, "日末容积"]
            drain_capacity = summary_df.loc[i, "排水容积"]
            corrected_drainage = max(0, day_end_storage - drain_capacity)
            
            # 重新计算排末容积：日末容积 - 河区排水
            corrected_end_storage_after_drainage = day_end_storage - corrected_drainage
            
            # 重新计算容积变化：排末容积 - 日初容积  
            day_initial_storage = summary_df.loc[i, "日初容积"]
            corrected_volume_change = corrected_end_storage_after_drainage - day_initial_storage
            
            # 重新计算排后变化：容积变化 - 河区排水
            corrected_post_drainage_change = corrected_volume_change - corrected_drainage
            
            # 更新DataFrame
            summary_df.loc[i, "河区排水"] = corrected_drainage
            summary_df.loc[i, "排末容积"] = corrected_end_storage_after_drainage
            summary_df.loc[i, "容积变化"] = corrected_volume_change
            summary_df.loc[i, "排后变化"] = corrected_post_drainage_change
            summary_df.loc[i, "总蓄水量"] = corrected_end_storage_after_drainage
        
        # 已删除缺口处理逻辑，使用外供替代
        output_file = os.path.join(base_dir, 'output_hq_all.txt')
        summary_df.to_csv(output_file, sep=Config.FILE_SEPARATOR, index=False)
        print(f"每日汇总数据已保存到：{output_file}")
        cumulative_df = summary_df.copy()
        for col in columns_to_sum:
            cumulative_df[col] = summary_df[col].cumsum()
        
        # 添加生态需水和总需水的计算
        summary_df['生态需水'] = summary_df['其他生态需水'] + summary_df['水位生态需水']
        summary_df['总需水量'] = summary_df['需水量'] + summary_df['生态需水']
        
        # 添加本地可供水量字段
        summary_df['本地可供水量'] = summary_df['合计来水'] + summary_df['初河蓄水'].apply(lambda x: max(x, 0))
        
        # 添加展示本地可供水量字段（用于验证水量平衡）
        summary_df['展示本地可供水量'] = summary_df['总需水量'] - summary_df['缺水(浙东需供)']
        
        # 对新增列执行累计计算
        cumulative_df['生态需水'] = summary_df['生态需水'].cumsum()
        cumulative_df['总需水量'] = summary_df['总需水量'].cumsum()
        cumulative_df['本地可供水量'] = summary_df['本地可供水量'].cumsum()
        cumulative_df['展示本地可供水量'] = summary_df['展示本地可供水量'].cumsum()
        
        start_date = summary_df[Config.DATE_COLUMN].iloc[0]
        cumulative_df['累积时段'] = cumulative_df[Config.DATE_COLUMN].apply(
            lambda x: f"{start_date}至{x}"
        )
        cumulative_output_file = os.path.join(base_dir, 'output_hq_all_cumulative.txt')
        cumulative_df.to_csv(cumulative_output_file, sep=Config.FILE_SEPARATOR, index=False)
        print(f"累积汇总数据已保存到：{cumulative_output_file}")
        total_df = pd.DataFrame()
        start_date = summary_df[Config.DATE_COLUMN].iloc[0]
        end_date = summary_df[Config.DATE_COLUMN].iloc[-1]
        total_df['时间段'] = [f"{start_date}至{end_date}"]
        for col in columns_to_sum:
            total_df[col] = [summary_df[col].sum()]
        
        # 添加生态需水和总需水的汇总计算
        total_df['生态需水'] = [summary_df['生态需水'].sum()]
        total_df['总需水量'] = [summary_df['总需水量'].sum()]
        total_df['本地可供水量'] = [summary_df['本地可供水量'].sum()]
        total_df['展示本地可供水量'] = [summary_df['展示本地可供水量'].sum()]
        
        total_output_file = os.path.join(base_dir, 'output_hq_all_total.txt')
        total_df.to_csv(total_output_file, sep=Config.FILE_SEPARATOR, index=False)
        print(f"整体累积汇总（{start_date}至{end_date}）已保存到：{total_output_file}")
        return True

    @staticmethod
    def generate_16_hq_summary():
        """生成16个河区汇总文件"""
        print("开始生成16个河区数据汇总文件...")
        columns_to_sum = SUMMARY_COLUMNS
        base_dir = str(Config.BASE_DIR)
        
        # 明确列出要汇总的16个河区文件
        hq_16_files = [
            'output_hq_CXPYDHQ.txt',
            'output_hq_CXPYXHQ.txt',
            'output_hq_CXPYZHQ.txt',
            'output_hq_FHPYQ.txt',
            'output_hq_HSPYQ.txt',
            'output_hq_JBZHPYQ.txt',
            'output_hq_NSPYQ.txt',
            'output_hq_SSPYQ.txt',
            'output_hq_SYPYQ.txt',
            'output_hq_YBPYSHQ.txt',
            'output_hq_YBPYZHQ.txt',
            'output_hq_YYPYMZZHQ.txt',
            'output_hq_YYPYSHQ.txt',
            'output_hq_YYPYXHQ.txt',
            'output_hq_YYPYYJSYQ.txt',
            'output_hq_YYPYYJXYQ.txt'
        ]
        
        # 检查文件是否存在
        hq_files = [f for f in hq_16_files if os.path.exists(os.path.join(base_dir, f))]
        if not hq_files:
            print("未找到任何河区数据文件！")
            return False
        
        print(f"找到 {len(hq_files)} 个河区数据文件（共16个）")
        print(f"包含的河区文件: {hq_files}")
        
        first_file = os.path.join(base_dir, hq_files[0])
        first_df = pd.read_csv(first_file, sep=Config.FILE_SEPARATOR)
        summary_df = pd.DataFrame()
        summary_df[Config.DATE_COLUMN] = first_df[Config.DATE_COLUMN]
        
        for col in columns_to_sum:
            summary_df[col] = 0.0
        
        for hq_file in hq_files:
            file_path = os.path.join(base_dir, hq_file)
            try:
                df = pd.read_csv(file_path, sep=Config.FILE_SEPARATOR)
                if not all(df[Config.DATE_COLUMN].values == summary_df[Config.DATE_COLUMN].values):
                    print(f"警告：文件 {hq_file} 的日期与第一个文件不匹配，跳过")
                    continue
                for col in columns_to_sum:
                    if col in df.columns:
                        summary_df[col] += df[col].fillna(0).values
                    else:
                        print(f"警告：文件 {hq_file} 中没有找到列 '{col}'")
                print(f"已处理文件：{hq_file}")
            except Exception as e:
                print(f"处理文件 {hq_file} 时出错：{str(e)}")
        
        # 修复容积相关字段的汇总逻辑：重新计算河区排水和排末容积
        print("正在修复容积相关字段的汇总逻辑...")
        for i in summary_df.index:
            # 重新计算河区排水：max(0, 日末容积 - 排水容积)
            day_end_storage = summary_df.loc[i, "日末容积"]
            drain_capacity = summary_df.loc[i, "排水容积"]
            corrected_drainage = max(0, day_end_storage - drain_capacity)
            
            # 重新计算排末容积：日末容积 - 河区排水
            corrected_end_storage_after_drainage = day_end_storage - corrected_drainage
            
            # 重新计算容积变化：排末容积 - 日初容积  
            day_initial_storage = summary_df.loc[i, "日初容积"]
            corrected_volume_change = corrected_end_storage_after_drainage - day_initial_storage
            
            # 重新计算排后变化：容积变化 - 河区排水
            corrected_post_drainage_change = corrected_volume_change - corrected_drainage
            
            # 更新DataFrame
            summary_df.loc[i, "河区排水"] = corrected_drainage
            summary_df.loc[i, "排末容积"] = corrected_end_storage_after_drainage
            summary_df.loc[i, "容积变化"] = corrected_volume_change
            summary_df.loc[i, "排后变化"] = corrected_post_drainage_change
            summary_df.loc[i, "总蓄水量"] = corrected_end_storage_after_drainage
        
        # 添加生态需水和总需水的计算
        summary_df['生态需水'] = summary_df['其他生态需水'] + summary_df['水位生态需水']
        summary_df['总需水量'] = summary_df['需水量'] + summary_df['生态需水']
        
        # 添加本地可供水量字段
        summary_df['本地可供水量'] = summary_df['合计来水'] + summary_df['初河蓄水'].apply(lambda x: max(x, 0))
        
        # 添加展示本地可供水量字段（用于验证水量平衡）
        summary_df['展示本地可供水量'] = summary_df['总需水量'] - summary_df['缺水(浙东需供)']
        
        # 保存16个河区的汇总文件
        output_file = os.path.join(base_dir, 'output_hq_all.txt')
        summary_df.to_csv(output_file, sep=Config.FILE_SEPARATOR, index=False)
        print(f"16个河区每日汇总数据已保存到：{output_file}")
        
        # 生成16个河区的累积汇总文件
        cumulative_df = summary_df.copy()
        for col in columns_to_sum:
            cumulative_df[col] = summary_df[col].cumsum()
        
        # 对新增列执行累计计算
        cumulative_df['生态需水'] = summary_df['生态需水'].cumsum()
        cumulative_df['总需水量'] = summary_df['总需水量'].cumsum()
        cumulative_df['本地可供水量'] = summary_df['本地可供水量'].cumsum()
        cumulative_df['展示本地可供水量'] = summary_df['展示本地可供水量'].cumsum()
        
        start_date = summary_df[Config.DATE_COLUMN].iloc[0]
        cumulative_df['累积时段'] = cumulative_df[Config.DATE_COLUMN].apply(
            lambda x: f"{start_date}至{x}"
        )
        cumulative_output_file = os.path.join(base_dir, 'output_hq_all_cumulative.txt')
        cumulative_df.to_csv(cumulative_output_file, sep=Config.FILE_SEPARATOR, index=False)
        print(f"16个河区累积汇总数据已保存到：{cumulative_output_file}")
        
        # 生成16个河区的总计汇总文件
        total_df = pd.DataFrame()
        start_date = summary_df[Config.DATE_COLUMN].iloc[0]
        end_date = summary_df[Config.DATE_COLUMN].iloc[-1]
        total_df['时间段'] = [f"{start_date}至{end_date}"]
        
        # 对所有数值列进行汇总，但对"初河蓄水"字段单独处理
        for col in columns_to_sum:
            if col == "初河蓄水":
                total_df[col] = [summary_df[col].iloc[0]]  # 只取第一行值
            else:
                total_df[col] = [summary_df[col].sum()]  # 求和
        
        # 添加新增字段的汇总计算
        total_df['生态需水'] = [summary_df['生态需水'].sum()]
        total_df['总需水量'] = [summary_df['总需水量'].sum()]
        total_df['本地可供水量'] = [summary_df['本地可供水量'].sum()]
        total_df['展示本地可供水量'] = [summary_df['展示本地可供水量'].sum()]
        
        # 保存16个河区的总计文件
        total_output_file = os.path.join(base_dir, 'output_hq_all_total.txt')
        total_df.to_csv(total_output_file, sep=Config.FILE_SEPARATOR, index=False)
        print(f"16个河区总计汇总（{start_date}至{end_date}）已保存到：{total_output_file}")
        
        return True

    @staticmethod
    def correct_total_summary():
        """
        根据 output_hq_all.txt 的数据修正 output_hq_all_total.txt 的特定字段。
        - 日初容积 使用 output_hq_all.txt 第一天的值。
        - 排末容积 使用 output_hq_all.txt 最后一天的值。
        """
        print("开始修正总汇总文件的日初容积和排末容积...")
        base_dir = str(Config.BASE_DIR)
        all_hq_file = os.path.join(base_dir, 'output_hq_all.txt')
        total_hq_file = os.path.join(base_dir, 'output_hq_all_total.txt')

        try:
            if not os.path.exists(all_hq_file) or not os.path.exists(total_hq_file):
                print("警告: 汇总文件 'output_hq_all.txt' 或 'output_hq_all_total.txt' 不存在，跳过修正。")
                return

            all_df = pd.read_csv(all_hq_file, sep=Config.FILE_SEPARATOR)
            total_df = pd.read_csv(total_hq_file, sep=Config.FILE_SEPARATOR)

            if all_df.empty:
                print("警告: 'output_hq_all.txt' 文件为空，跳过修正。")
                return

            # 方案 A: 严格按照指定的列名操作
            first_day_initial_storage = all_df['日初容积'].iloc[0]

            last_valid_index = all_df[Config.DATE_COLUMN].last_valid_index()
            if last_valid_index is None:
                print("警告: 'output_hq_all.txt' 文件中没有有效数据行，跳过修正。")
                return
            last_day_end_storage = all_df['排末容积'].iloc[last_valid_index]

            print(f"从 'output_hq_all.txt' 获取的值: 日初容积={first_day_initial_storage}, 排末容积={last_day_end_storage}")

            total_df['日初容积'] = first_day_initial_storage
            total_df['排末容积'] = last_day_end_storage
            
            # 重新计算相关字段以保持数据一致性
            total_df['容积变化'] = total_df['排末容积'] - total_df['日初容积']
            total_df['排后变化'] = total_df['容积变化'] - total_df['河区排水']

            total_df.to_csv(total_hq_file, sep=Config.FILE_SEPARATOR, index=False)
            print(f"总汇总文件 '{total_hq_file}' 已成功修正并保存。")

        except Exception as e:
            print(f"修正总汇总文件时出错: {str(e)}")

class WaterResourcesManager:
    @staticmethod
    def run():
        Config.initialize()
        Config.ensure_directories()
        Config.load_fssn_rules()
        Config.load_level_data()
        storage_curves = DataLoader.load_storage_curves()
        reservoir_inflow = ReservoirInflowGenerator.generate()
        DistrictDataProcessor.generate_categorized_data(reservoir_inflow)
        FSSnDataGenerator.generate_supplement_data()
        DataOutputProcessor.merge_and_output_final_data()
        DataOutputProcessor.copy_and_rename_files()
        DataOutputProcessor.copy_and_rename_fssn_files()
        # DataOutputProcessor.generate_all_hq_summary()
        DataOutputProcessor.generate_16_hq_summary()  # 生成16个河区的汇总文件
        DataOutputProcessor.generate_district_summary()
        DataOutputProcessor.correct_total_summary()
        print("\n处理完成！")
def main():
    WaterResourcesManager.run()
if __name__ == '__main__':
    main()

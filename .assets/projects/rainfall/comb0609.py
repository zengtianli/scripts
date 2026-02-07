import re
import logging
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
# 配置和日志
class Config:
    def __init__(self, base_dir):
        self.BASE_DIR = Path(base_dir)
        self.DATA_DIR = self.BASE_DIR / 'data'
        self.dirs = {
            'csv': self.DATA_DIR / '01csv',
            'area': self.DATA_DIR / '02area', 
            'ggxs': self.DATA_DIR / '03ggxs',
            'deduct': self.DATA_DIR / '04deduct'
        }
        for d in self.dirs.values():
            d.mkdir(exist_ok=True, parents=True)
        # 日志
        log_dir = self.DATA_DIR / 'logs'
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_dir / f"rain_transfer_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8')
            ]
        )
class Processor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    def read_file(self, path, sep=None, as_text=False, **kwargs):
        """统一文件读取"""
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # 如果明确要求读取为文本，返回文本行
        if as_text:
            return lines
        # 特殊处理：如果是分区数据生成的CSV文件（非标准格式），返回文本行
        if path.suffix == '.csv' and any('分区名称：' in line for line in lines[:5]):
            return lines
        # 如果是标准CSV文件，使用pandas读取
        if path.suffix == '.csv':
            return pd.read_csv(path, **kwargs)
        # 如果指定了分隔符，解析为DataFrame
        if sep:
            headers = lines[0].strip().replace('\ufeff', '').split(sep)
            data = []
            for line in lines[1:]:
                values = line.strip().split(sep)
                if len(values) == len(headers):
                    row = {}
                    for h, v in zip(headers, values):
                        try:
                            row[h] = float(v)
                        except:
                            row[h] = v
                    data.append(row)
            return pd.DataFrame(data)
        return lines
    def write_file(self, content, path, **kwargs):
        """统一文件写入"""
        if isinstance(content, pd.DataFrame):
            content.to_csv(path, **kwargs)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                if isinstance(content, list):
                    f.writelines(line + '\n' for line in content)
                else:
                    f.write(content)
        self.logger.info(f"写入文件: {path}")
    def partition_process(self):
        """分区处理"""
        self.logger.info("开始处理分区数据")
        lines = self.read_file(self.config.BASE_DIR / 'static_PYLYSCS.txt')
        current_district = None
        district_data = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('分区') and '-名称:' in line:
                if current_district and district_data:
                    self._save_district(current_district, district_data)
                section_num = int(line[2:4])
                code = line.split(':')[1].strip().split('（')[0]
                current_district = (section_num, code)
                district_data = [f"分区名称：{line.split(':')[1].strip()}\n"]
            elif current_district:
                district_data.append(line + '\n')
        if current_district and district_data:
            self._save_district(current_district, district_data)
    def _save_district(self, district_info, data):
        section_num, code = district_info
        section_number = f"{section_num:02d}"
        # 计算面积
        total_area = 0
        percentages = []
        for line in data:
            if '包含概湖对应的面积(m2)' in line:
                try:
                    area_str = line.split(':')[1].strip()
                    areas = [float(x.strip()) for x in area_str.split(',') if x.strip()]
                    total_area = sum(areas)
                    percentages = [f"{(area / total_area * 100):.2f}" for area in areas]
                except:
                    pass
                break
        # 生成CSV
        csv_lines = []
        for line in data:
            line = line.strip()
            if any(key in line for key in ['分区名称', '包含概湖个数', '包含概湖的名称', '包含概湖对应的面积']):
                csv_lines.append(line.replace('：', ',').replace(':', ','))
        csv_lines.append(f"分区{section_number}总面积(m2),{total_area:.4f}")
        if percentages:
            csv_lines.append(f"分区{section_number}包含概湖对应的百分比," + ",".join(percentages))
        self.write_file(csv_lines, self.config.dirs['csv'] / f"{section_number}_{code}.csv")
    def area_process(self):
        """面积处理"""
        self.logger.info("开始处理面积数据")
        gaihu_data = []
        fenqu_data = []
        for file in self.config.dirs['csv'].iterdir():
            if not file.name.endswith('.csv'):
                continue
            lines = self.read_file(file, as_text=True)
            # 概湖数据
            if len(lines) >= 5:
                try:
                    lake_names = [name.strip() for name in lines[3].strip().split(',')[1:] if name.strip()]
                    area_parts = lines[4].strip().split(',')
                    for i, area_str in enumerate(area_parts[1:]):
                        if i < len(lake_names):
                            try:
                                area = float(area_str.strip())
                                gaihu_data.append({'概湖名称': lake_names[i], '面积(km2)': area})
                            except:
                                pass
                except:
                    pass
            # 分区数据
            for line in lines:
                if '分区' in line and '总面积' in line:
                    try:
                        area = float(line.strip().split(',')[1])
                        fenqu_data.append({'分区名称': file.stem, '面积(km2)': area})
                    except:
                        pass
                    break
        if gaihu_data:
            gaihu_df = pd.DataFrame(gaihu_data)
            gaihu_df = gaihu_df.sort_values('概湖名称', key=lambda x: x.map(lambda name: int(re.search(r'\d+', name).group()) if re.search(r'\d+', name) else float('inf')))
            self.write_file(gaihu_df, self.config.dirs['area'] / 'gaihu.csv', index=False)
        if fenqu_data:
            fenqu_df = pd.DataFrame(fenqu_data).sort_values('分区名称')
            self.write_file(fenqu_df, self.config.dirs['area'] / 'fenqu.csv', index=False)
    def ggxs_process(self):
        """降雨系数处理"""
        self.logger.info("开始处理降雨系数数据")
        fenqu_df = self.read_file(self.config.dirs['area'] / 'fenqu.csv')
        ggxs_df = self.read_file(self.config.BASE_DIR / 'input_FQNNGXL.txt', sep='\t')
        # 日数据转小时数据
        dates = pd.to_datetime(ggxs_df['日期'])
        hours = pd.date_range(dates.min(), dates.max() + pd.Timedelta(days=1), freq='h')[:-1]
        df_hourly = pd.DataFrame({'日期': hours, 'date': hours.floor('D')})
        ggxs_df['date'] = pd.to_datetime(ggxs_df['日期'])
        for col in ggxs_df.columns:
            if col not in ['日期', 'date']:
                daily_values = ggxs_df[['date', col]].copy()
                daily_values[col] = daily_values[col] / 24
                df_hourly = df_hourly.merge(daily_values, on='date', how='left')
        df_hourly.drop('date', axis=1, inplace=True)
        # 处理湖泊
        lake_info = []
        for file in self.config.dirs['csv'].iterdir():
            if file.name.endswith('.csv'):
                lines = self.read_file(file, as_text=True)
                for line in lines:
                    if '包含概湖的名称' in line:
                        lakes = [name.strip() for name in line.split(',')[1:] if name.strip()]
                        lake_info.extend((name, file.stem) for name in lakes)
                        break
        processed = set()
        files_created = 0
        for lake_name, partition_name in lake_info:
            if lake_name in processed or partition_name not in df_hourly.columns:
                continue
            area_km2 = fenqu_df.loc[fenqu_df['分区名称'] == partition_name, '面积(km2)'].iloc[0]
            area_m2 = area_km2 * 1_000_000
            lake_df = pd.DataFrame({
                '日期': df_hourly['日期'],
                lake_name: df_hourly[partition_name] * 10000 / area_m2 * 1000
            })
            output_file = self.config.dirs['ggxs'] / f'{lake_name}_ggxs.csv'
            header = f"# 概湖编号: {lake_name}\n# 所属分区: {partition_name}\n# 分区面积(km2): {area_km2:.4f}\n# 注意：以下数据单位为毫米(mm)\n"
            self.write_file(header, output_file)
            self.write_file(lake_df, output_file, mode='a', index=False)
            processed.add(lake_name)
            files_created += 1
        
        # 确保为所有湖泊创建文件，即使数据都是0
        if files_created == 0:
            self.logger.warning("所有输入数据为0，为所有湖泊创建默认ggxs文件")
            # 为所有湖泊创建文件
            for lake_name, partition_name in lake_info:
                if lake_name in processed:
                    continue
                # 查找对应分区的面积
                matching_areas = fenqu_df.loc[fenqu_df['分区名称'] == partition_name, '面积(km2)']
                if len(matching_areas) == 0:
                    self.logger.warning(f"未找到分区 {partition_name} 的面积信息，跳过湖泊 {lake_name}")
                    continue
                area_km2 = matching_areas.iloc[0]
                
                lake_df = pd.DataFrame({
                    '日期': df_hourly['日期'],
                    lake_name: 0.0  # 全部设为0
                })
                output_file = self.config.dirs['ggxs'] / f'{lake_name}_ggxs.csv'
                header = f"# 概湖编号: {lake_name}\n# 所属分区: {partition_name}\n# 分区面积(km2): {area_km2:.4f}\n# 注意：以下数据单位为毫米(mm)\n"
                self.write_file(header, output_file)
                self.write_file(lake_df, output_file, mode='a', index=False)
                processed.add(lake_name)
                files_created += 1
            
            self.logger.info(f"创建了 {files_created} 个默认ggxs文件")
    def intake_process(self):
        """取水处理"""
        self.logger.info("开始处理取水数据")
        gaihu_area = self.read_file(self.config.dirs['area'] / 'gaihu.csv')
        plant_gaihu = self.read_file(self.config.BASE_DIR / 'input_YSH_GH.txt', sep='\t')
        intake = self.read_file(self.config.BASE_DIR / 'input_YSH.txt', sep='\t')
        for gaihu, plants in plant_gaihu.groupby('概湖'):
            area_data = gaihu_area[gaihu_area['概湖名称'] == gaihu]['面积(km2)']
            if len(area_data) == 0:
                continue
            area = area_data.iloc[0] * 1_000_000
            plant_data = []
            for _, row in intake[intake['取水户名称'].isin(plants['取水户名称'])].iterrows():
                date = datetime.strptime(row['时间'], '%Y/%m/%d')
                for h in range(24):
                    plant_data.append({
                        '日期': (date + timedelta(hours=h)).strftime('%Y/%m/%d %H:%M'),
                        row['取水户名称']: row['小时取水量'] / area * 1000
                    })
            if plant_data:
                result = pd.DataFrame(plant_data).groupby('日期', as_index=False).first().sort_values('日期')
                result['合计'] = result.drop('日期', axis=1).sum(axis=1)
                output_file = self.config.dirs['intake'] / f'{gaihu}_intake.csv'
                header = f"# 概湖编号: {gaihu}\n# 面积(km2): {area/1_000_000:.4f}\n# 注意：以下数据单位为毫米(mm)\n"
                self.write_file(header, output_file)
                self.write_file(result, output_file, mode='a', index=False)
    def deduct_process(self):
        """扣减处理"""
        self.logger.info("开始处理扣减数据")
        for file in self.config.dirs['ggxs'].iterdir():
            if not file.name.endswith('.csv'):
                continue
            prefix = file.stem.split('_')[0]
            ggxs = self.read_file(file, comment='#')
            ggxs['ggxs_sum'] = ggxs.drop('日期', axis=1).fillna(0).sum(axis=1)
            try:
                intake = self.read_file(self.config.dirs['intake'] / f'{prefix}_intake.csv', comment='#')
                intake_df = pd.DataFrame({'日期': intake['日期'], 'intake_total': intake.iloc[:, -1].fillna(0)})
            except:
                intake_df = pd.DataFrame({'日期': ggxs['日期'], 'intake_total': 0})
            result = pd.merge(ggxs[['日期', 'ggxs_sum']], intake_df, on='日期', how='left').fillna(0)
            result['total_demand'] = result['ggxs_sum'] + result['intake_total']
            self.write_file(result, self.config.dirs['deduct'] / f'{prefix}_deduct.csv', index=False)
    def merge_final_process(self):
        """合并和最终处理"""
        self.logger.info("开始合并和最终处理")
        # 合并GGXS数据
        ggxs_files = [f for f in self.config.dirs['ggxs'].iterdir() if f.name.endswith('_ggxs.csv')]
        
        # 读取GHJYL数据
        ghjyl_df = self.read_file(self.config.BASE_DIR / 'input_GHJYL.txt', sep='\t')
        
        if not ggxs_files:
            self.logger.warning("没有找到ggxs文件，将基于GHJYL数据创建输出")
            # 如果没有ggxs文件，直接使用GHJYL数据作为输出（等同于没有扣减）
            ghjyl_df['日期'] = pd.to_datetime(ghjyl_df['日期']).dt.strftime('%Y/%m/%d %H:00')
            
            # 统一列名格式
            def normalize_column_name(col_name):
                if col_name == '日期':
                    return col_name
                match = re.search(r'G(\d+)', col_name)
                if match:
                    return f"G{int(match.group(1))}"
                return col_name
            
            ghjyl_df.columns = [normalize_column_name(col) for col in ghjyl_df.columns]
            
            # 排序列
            other_cols = [col for col in ghjyl_df.columns if col != '日期']
            other_cols.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else float('inf'))
            cols = ['日期'] + other_cols
            result_df = ghjyl_df[cols]
            
            self.write_file(result_df, self.config.DATA_DIR / 'final.csv', index=False)
            self.write_file(result_df, self.config.BASE_DIR / 'output_GHJYL.txt', sep='\t', index=False)
            return
            
        merged_df = self.read_file(ggxs_files[0], comment='#')
        for file in ggxs_files[1:]:
            df = self.read_file(file, comment='#')
            for col in df.columns:
                if col != '日期':
                    merged_df[col] = df[col]
        # 统一列名格式并排序
        def normalize_column_name_for_output(col_name):
            if col_name == '日期':
                return col_name
            match = re.search(r'G(\d+)', col_name)
            if match:
                return f"G{int(match.group(1))}"  # 不补零，直接使用数字
            return col_name
        
        # 重命名所有列为G1格式
        merged_df.columns = [normalize_column_name_for_output(col) for col in merged_df.columns]
        
        # 排序列 - 按数字顺序排序
        other_cols = [col for col in merged_df.columns if col != '日期']
        other_cols.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else float('inf'))
        cols = ['日期'] + other_cols
        merged_df = merged_df[cols]
        self.write_file(merged_df, self.config.DATA_DIR / 'merge_all.csv', index=False)
        # 处理扣减
        # 统一日期格式
        merged_df['日期'] = pd.to_datetime(merged_df['日期']).dt.strftime('%Y/%m/%d %H:00')
        ghjyl_df['日期'] = pd.to_datetime(ghjyl_df['日期']).dt.strftime('%Y/%m/%d %H:00')
        # 统一列名格式（统一为G1格式，不补零）
        def normalize_column_name(col_name):
            if col_name == '日期':
                return col_name
            match = re.search(r'G(\d+)', col_name)
            if match:
                return f"G{int(match.group(1))}"  # 不补零，直接使用数字
            return col_name
        
        # 创建列名映射字典
        ghjyl_col_mapping = {col: normalize_column_name(col) for col in ghjyl_df.columns}
        merged_col_mapping = {col: normalize_column_name(col) for col in merged_df.columns}
        
        # 重命名列
        ghjyl_df_normalized = ghjyl_df.rename(columns=ghjyl_col_mapping)
        merged_df_normalized = merged_df.rename(columns=merged_col_mapping)
        
        # 找共同列并扣减
        base_df = ghjyl_df_normalized if len(ghjyl_df_normalized) > len(merged_df_normalized) else merged_df_normalized
        common_cols_list = [col for col in ghjyl_df_normalized.columns if col != '日期' and col in merged_df_normalized.columns]
        common_cols_list.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else float('inf'))
        common_cols = ['日期'] + common_cols_list
        result_df = pd.DataFrame({'日期': base_df['日期']})
        for col in common_cols[1:]:
            ghjyl_dict = dict(zip(ghjyl_df_normalized['日期'], ghjyl_df_normalized[col]))
            merged_dict = dict(zip(merged_df_normalized['日期'], merged_df_normalized[col]))
            result_df[col] = base_df['日期'].apply(lambda date: ghjyl_dict.get(date, 0) - merged_dict.get(date, 0))
        self.write_file(result_df, self.config.DATA_DIR / 'final.csv', index=False)
        self.write_file(result_df, self.config.BASE_DIR / 'output_GHJYL.txt', sep='\t', index=False)
    def run_all(self):
        """运行所有处理步骤"""
        steps = [
            self.partition_process,
            self.area_process, 
            self.ggxs_process,
            self.intake_process,
            self.deduct_process,
            self.merge_final_process
        ]
        for step in steps:
            try:
                step()
            except Exception as e:
                self.logger.error(f"执行步骤 {step.__name__} 时发生错误: {e}")
                raise
def main():
    parser = argparse.ArgumentParser(description='概湖灌溉需水计算程序')
    parser.add_argument('base_dir', nargs='?', default=str(Path(__file__).parent.absolute()), help='基础目录路径')
    parser.add_argument('--steps', nargs='+', choices=['partition', 'area', 'ggxs', 'intake', 'deduct', 'merge_final', 'all'], default=['all'], help='指定处理步骤')
    args = parser.parse_args()
    config = Config(args.base_dir)
    processor = Processor(config)
    if 'all' in args.steps:
        processor.run_all()
    else:
        for step in args.steps:
            getattr(processor, f'{step}_process')()
    logging.getLogger(__name__).info("所有处理步骤执行完成")
if __name__ == '__main__':
    main()

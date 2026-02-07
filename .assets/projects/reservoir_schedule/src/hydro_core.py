import numpy as np
import pandas as pd
# import os
# import json
# from scipy.interpolate import interp1d
# import pyswarms as pys
from enum import Enum
import time
import re
from datetime import datetime


def format_value(x):
    """
    输出格式控制：
        超过100，不保留小数
        小于100大于10，保留一位小数
        小于10，保留两位
        等于0，不保留小数
    """
    if abs(x) > 100:
        return f"{round(x, 6):.6f}"
    elif abs(x) > 10:
        return f"{round(x, 6):.6f}"
    elif x == 0:
        return f"0"
    else:
        return f"{round(x, 6):.6f}"


def log_error(log_file="log.txt", error_message=''):
    """记录错误信息"""
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{error_message}\n")


class ComFun:
    @staticmethod
    def create_lookup_df(df_line_month, interpolate=True):
        """
        根据输入的 Date -> Value 数据插值为全年每日数据，并构建查找表
        :param df_line_month: DataFrame 或 dict，
                      "Date": pd.date_range，具体到日的日期列（例如：'2023-04-15', '2023-07-15'）
                     "Value": np.array，对应值
        :param interpolate: bool，默认 True 表示进行线性插值；False 表示不插值，恒定填充
        :return: pd.DataFrame，形如：
            Month-Day | Normal_Year_Value | Leap_Year_Value
        """

        # 转换为 DataFrame（如果输入是 dict）
        df = pd.DataFrame({
            'Date': pd.to_datetime(['2022-' + d for d in df_line_month['Date']]),
            'Value': df_line_month['Value']
        })

        df.sort_values(by='Date', ascending=True, inplace=True)

        # 如果只有一个点，无法处理
        if len(df) < 2:
            raise ValueError("至少需要两个点进行处理")

        # 获取所有点
        dates = df['Date'].tolist()
        values = df['Value'].tolist()

        # 添加下一年的第一个点，形成闭环
        next_year_first_date = dates[0] + pd.DateOffset(years=1)
        dates.append(next_year_first_date)
        values.append(values[0])

        # 初始化查找表
        lookup_table = {}

        # 分段插值
        for i in range(len(dates) - 1):
            start_date = pd.to_datetime(dates[i])
            end_date = pd.to_datetime(dates[i + 1])
            start_val = values[i]
            end_val = values[i + 1]
            # print(start_date, end_date)

            # 是否包含2月29日——如果平年包含2月28日，则意味着闰年包含2月29日
            tmp_date = pd.to_datetime(str(end_date.year)+'-2-28')
            if start_date <= tmp_date < end_date:
                if_include_2_29 = True
            else:
                if_include_2_29 = False

            # 间隔天数
            del_days = (end_date - start_date).days
            if del_days <= 0:
                continue

            # 线性插值步长
            if interpolate:
                delta_ny = (end_val - start_val) / del_days
                if if_include_2_29:  # 包含2月29日，天数多一天
                    delta_ly = (end_val - start_val) / (del_days + 1)
                else:
                    delta_ly = delta_ny
            else:
                delta_ny = 0
                delta_ly = 0

            current_date = start_date
            for j in range(del_days):
                mmdd = current_date.strftime('%m-%d')

                if if_include_2_29:  # 涉及2月29日
                    if current_date < tmp_date:  # 日期在2月28日之前
                        lookup_table[mmdd] = {
                            'normal_year': start_val + delta_ny * j,
                            'leap_year': start_val + delta_ly * j
                        }
                    elif current_date > tmp_date:  # 日期在2月28日之后（闰年加1天）
                        lookup_table[mmdd] = {
                            'normal_year': start_val + delta_ny * j,
                            'leap_year': start_val + delta_ly * (j + 1)
                        }
                    else:  # 日期正好在2月28日，闰年补充2月29日情况
                        lookup_table[mmdd] = {
                            'normal_year': start_val + delta_ny * j,
                            'leap_year': start_val + delta_ly * j
                        }
                        lookup_table['02-29'] = {
                            'normal_year': -1,
                            'leap_year': start_val + delta_ly * (j + 1)
                        }
                else:
                    lookup_table[mmdd] = {
                        'normal_year': start_val + delta_ny * j,
                        'leap_year': start_val + delta_ly * j
                    }

                # 移动到下一天
                current_date += pd.Timedelta(days=1)

        # 转换为 DataFrame
        result = []
        leap_days = pd.date_range(start=f'2020-01-01', end=f'2020-12-31', freq='D').strftime('%m-%d').tolist()
        for day in leap_days:
            result.append({
                'Month-Day': day,
                'normal_year': lookup_table[day]['normal_year'],
                'leap_year': lookup_table[day]['leap_year']
            })
        result_df = pd.DataFrame(result)
        result_df.set_index('Month-Day', inplace=True)

        return result_df

    @staticmethod
    def statistic(df_day_input, limited_value, hydro_year_start_month, hydro_year_end_month):
        """
        统计逐月过程、逐年过程（日历年）、逐年过程（水位年）
        :param df_day_input: pd.DataFrame，逐日过程，包含
                     "Date": pd.date_range，时间
                    "Value": np.array，对应值
        :param limited_value: float，缺水量判断值
        :param hydro_year_start_month: integer，水文年起始月
        :param hydro_year_end_month: integer，水文年结束月
        :return: statistic: dict，统计结果，包含
                   "Month": 包含'Date', 'Ave', 'Sum', 'LackDays', 'Last'（年-月、月平均值、月总和、月缺水天数、月末值）
                    "Year": 包含'Date', 'Ave', 'Sum', 'LackDays', 'Last'（年、年平均值、年总和、年缺水天数、年末值）
               "HydroYear": 包含'Date', 'Ave', 'Sum', 'LackDays', 'Last'（水文年、水文年平均值、水文年总和、水文年缺水天数、水文年末值）
                     "Ave": float，多年平均值
        """
        # 0、逐日过程
        df_day = df_day_input.sort_values(by='Date', ascending=True).copy()  # 根据日期列升序
        date_process = df_day['Date']
        year_process = date_process.dt.year
        month_process = date_process.dt.month
        # day_process = df_day['Value']
        # print(df_day)

        # 1、逐月过程
        statistic_month = df_day.resample('ME', on='Date').agg({
            'Value': ['mean', 'sum', lambda x: (x > limited_value).sum(), 'last']
        }).reset_index()
        statistic_month.columns = ['Date', 'Ave', 'Sum', 'Days', 'Last']
        # print(statistic_month)

        # 2、逐年过程
        statistic_year = df_day.resample('YE', on='Date').agg({
            'Value': ['mean', 'sum', lambda x: (x > limited_value).sum(), 'last']
        }).reset_index()
        statistic_year.columns = ['Date', 'Ave', 'Sum', 'Days', 'Last']
        # print(statistic_year)

        # 3、逐年过程（水文年）
        # 3-1、确定水文年
        start_year = year_process.iloc[0]
        end_year = year_process.iloc[-1]

        hydro_year = np.where(
            month_process >= hydro_year_start_month,
            year_process,
            np.where(year_process == start_year, end_year, year_process - 1)
        )

        # hydro_year_str = (
        #     hydro_year.astype(str) + f'.{hydro_year_start_month}~' +
        #     (hydro_year + 1).astype(str) + f'.{hydro_year_end_month}'
        # )
        hydro_year_series = pd.Series(hydro_year, index=year_process.index)

        # 分步拼接 - pandas 会正确处理 Series + str
        hydro_year_str = (
                hydro_year_series.astype(str) +
                f'.{hydro_year_start_month}~' +
                (hydro_year_series + 1).astype(str) +
                f'.{hydro_year_end_month}'
        )

        df_day['HydroYear'] = hydro_year_str

        # 3-2、确定水文年年末值系列
        hydro_year_series_last = statistic_month[statistic_month['Date'].dt.month ==
                                                 hydro_year_end_month]['Last'].values

        # 3-3、水文年统计
        statistic_hydro_year = df_day.groupby('HydroYear').agg({
            'Value': ['mean', 'sum', lambda x: (x > limited_value).sum()]
        })
        statistic_hydro_year['Last'] = hydro_year_series_last
        statistic_hydro_year.columns = ['Ave', 'Sum', 'Days', 'Last']

        # 多年平均值
        statistic_ave = statistic_year['Sum'].mean()

        statistic = {
            "Month": statistic_month,
            "Year": statistic_year,
            "HydroYear": statistic_hydro_year,
            "Ave": statistic_ave
        }

        return statistic

    @staticmethod
    def statistic_output(dict_dict, first_col_df, output_file_name):
        """
        将统计结果输出
        Args:
            dict_dict: 嵌套字典
            first_col_df: 首列（时间列），不设置index列
            output_file_name: str 输出文件名
        """
        # Step 1: 构建列名 MultiIndex
        columns = []
        data = []

        for col1, tmp_data in dict_dict.items():
            for col2, arr in tmp_data.items():
                # columns.append((col1, col2))
                # columns.append(col1 + "-" + col2)
                columns.append(col2)
                # print(col1, col2)
                data.append(arr)

        # Step 2: 构造 MultiIndex 和 DataFrame
        other_df = pd.DataFrame(data=np.column_stack(data), columns=columns)
        # 合并 first_col_df 和 other_df
        first_col_df = first_col_df.reset_index(drop=True)  # 丢弃原来的 index，生成新的从 0 开始的整数索引
        other_df = other_df.reset_index(drop=True)  # 丢弃原来的 index，生成新的从 0 开始的整数索引
        df = pd.concat([first_col_df, other_df], axis=1)

        # Step 3: 保留小数位数
        for col in df.columns[1:]:  # 第一列是年-月，跳过
            df[col] = df[col].map(format_value)

        # Step 4: 输出
        df.to_csv(output_file_name, sep=',', index=False, encoding='utf-8')

    @staticmethod
    def transfer_process(date_process, value_process, origin_cal_step, new_cal_step, cal_mode='ave'):
        """
        转换计算步长
        Args:
            date_process: pd.daterange 日期
            value_process: array 值
            origin_cal_step: str 原计算尺度（“日”、“旬”、“月”）
            new_cal_step: str 新计算尺度（“日”、“旬”、“月”）
            cal_mode: str 统计方式，ave-取平均，sum-取加和，first-取首日
        Returns:
            new_value_process: array 值
        """
        # 构建 DataFrame
        df = pd.DataFrame({
            'date': pd.to_datetime(date_process),
            'value': np.array(value_process)
        })

        # 检查是否升序
        if not df['date'].is_monotonic_increasing:
            df = df.sort_values('date').reset_index(drop=True)

        # # 定义映射：中文 → pd 重采样频率
        # freq_map = {
        #     ('日', '旬'): '10D',
        #     ('日', '月'): 'M',
        #     ('旬', '月'): 'M',
        # }

        # 辅助函数：按旬分组（每10天，从每月1、11、21开始）
        def to_decade_group(date_series):
            """返回每条记录所属的“旬”起始日期（1日、11日、21日）"""
            groups = []
            current_decade_start = None
            for dt in date_series:
                if dt.day in [1, 11, 21]:
                    current_decade_start = dt
                groups.append(current_decade_start)
            return groups

        # ============================
        # 同尺度：直接返回
        # ============================
        if origin_cal_step == new_cal_step:
            return np.array(value_process)

        # ============================
        # 日 → 旬
        # ============================
        if origin_cal_step == '日' and new_cal_step == '旬':
            df['decade_group'] = to_decade_group(df['date'])
            grouped = df.groupby('decade_group', sort=True)

        # ============================
        # 日 → 月
        # ============================
        elif origin_cal_step == '日' and new_cal_step == '月':
            if cal_mode == 'first':
                # 使用首日所在月份
                grouped = df.groupby(df['date'].dt.to_period('M'))
            else:
                grouped = df.groupby(df['date'].dt.to_period('M'))

        # ============================
        # 旬 → 月
        # ============================
        elif origin_cal_step == '旬' and new_cal_step == '月':
            # 假设“旬”数据的 date_process 是每旬第一天（1、11、21）
            # 将每旬数据归入对应月份
            df['month_period'] = df['date'].dt.to_period('M')
            grouped = df.groupby('month_period', sort=True)

        # ============================
        # 旬 → 日（升尺度：插值）
        # ============================
        elif origin_cal_step == '旬' and new_cal_step == '日':
            results = []
            for i, dt in enumerate(date_process):
                day = dt.day
                if day in [1, 11, 21]:
                    current_value = value_process[i]
                results.append(current_value)
            return np.array(results)

        # ============================
        # 月 → 日 或 月 → 旬
        # ============================
        elif origin_cal_step == '月':
            # 构建一个映射：每个“月”对应的输出时间点
            target_dates = pd.DatetimeIndex(date_process)
            df_value = pd.DataFrame({'date': target_dates, 'orig_value': value_process})
            df_value['month_period'] = df_value['date'].dt.to_period('M')

            # 获取原始每月值（假设 value_process 中每个值对应其所在月）
            # 我们需要将每月的值广播到该月内所有目标时间点
            month_to_value = {}
            for i, row in df_value.iterrows():
                month_to_value[row['month_period']] = row['orig_value']

            # 映射回每个目标时间点
            result_values = [month_to_value[row['month_period']] for _, row in df_value.iterrows()]

            # 对于 'ave' 和 'sum'，如果是降尺度（月→日/旬），通常保持原值；但这里我们只是广播
            # 注意：'first' 在月→日/旬 时也等同于广播
            return np.array(result_values)

        # ============================
        # 执行聚合操作
        # ============================
        if cal_mode == 'sum':
            result = grouped['value'].sum().values
        elif cal_mode == 'ave':
            result = grouped['value'].mean().values
        elif cal_mode == 'first':
            result = grouped['value'].first().values
        else:
            raise ValueError("cal_mode must be one of ['ave', 'sum', 'first']")

        return result


class CalStatus(Enum):
    NOT_DO = 0  # 未计算
    DOING = 1  # 正在计算
    DONE = 2  # 完成计算


class StructReservoir:
    def __init__(self, reservoir_base_info, reservoir_id):
        """
        读取水库基本信息
        Args:
            reservoir_base_info: dict，水库信息：
                1.水库基本参数：水库名称、死水位、梅汛期限制水位、台汛期限制水位、正常水位、
                             水位-库容曲线、损失水量计算方式、损失水量值、梅汛期开始日期、台汛期开始日期
                             是否有发电任务、是否有供水任务
                2.发电相关信息：计算步长、电站类型、分期蓄水要求、出力调度线、
                3.供水相关信息：
            reservoir_id: int，水库序号，与输入顺序有关，从0开始编号
        """
        # 0 占位信息，不在此处直接读取，调用子函数进行初始化
        # # 调度线相关信息（可共用）
        self.arr_loss = None  # array，时段损失水量
        self.arr_waste = None  # array，时段弃水量
        self.arr_v_end = None  # array，时段末库容

        # 1 参数读取
        # 1-0 水库基本参数读取
        info = reservoir_base_info
        self.name = info['reservoirName']  # str,水库名称
        self.h_dead = info['deadWaterLevel']  # float,死水位
        self.h_max_wet_season = info['wetSeasonLimitWaterLevel']  # float,梅汛期限制水位
        self.h_max_typhoon = info['typhoonSeasonLimitWaterLevel']  # float,台汛期限制水位
        self.h_normal = info['normalWaterLevel']  # float,正常水位

        # - 损失水量计算方法、损失水量比例、损失水量固定值
        loss_cal_way = int(info["lossCalculateType"])  # int 损失水量计算方法 取0：表示千分比损失，1：表示定量损失流量
        if loss_cal_way == 0:
            loss_ratio = float(info["lossValue"]) / 1000  # float 损失水量比例
            loss_value = 0  # 损失水量固定值
        else:
            loss_ratio = 0  # 损失水量比例
            loss_value = float(info["lossValue"])  # float 损失水量固定值
        self.loss_cal_way = loss_cal_way  # int 损失水量计算方法
        self.loss_ratio = loss_ratio  # float 损失水量比例
        self.loss_value = loss_value  # float 损失水量固定值
        # - 梅汛期起止时间
        self.wet_season_start_date = info['wetSeasonStartDate']  # string，梅汛期开始时间
        self.wet_season_end_date = info['wetSeasonEndDate']  # string，梅汛期结束时间
        # - 台汛期起止时间
        self.typhoon_start_date = info['typhoonSeasonStartDate']  # string，台汛期开始时间
        self.typhoon_end_date = info['typhoonSeasonEndDate']  # string，台汛期结束时间
        # -- 检验汛期时间顺序合理：梅汛期开始 -> 梅汛期结束 -> 台汛期开始 -> 台汛期结束
        self.check_date()
        # - 有无发电（水电站发电程序）、供水任务（库群程序）
        self.if_cal_control_line = info['ifCalControlLine']
        self.if_supply_task = info['ifSupplyTask']  # bl，是否有供水任务
        self.if_power_task = info['ifPowerTask']  # bl，是否有发电任务
        # - 水位库容曲线
        self.zv = info['zv']  # pd.DataFrame("waterLevel", "volume")
        zzz = self.zv['waterLevel']
        vvv = self.zv['volume']
        # zzz = []
        # vvv = []
        # for tmp_dict in info['waterLevelVolume']:
        #     # info['waterLevelVolume']示例:
        #     # tmp_dict = {
        #     #     'waterLevel': float,
        #     #     'volume': float,
        #     # }
        #     zzz.append(tmp_dict['waterLevel'])
        #     vvv.append(tmp_dict['volume'])
        # zzz = np.array(zzz)
        # vvv = np.array(vvv)
        # self.zv = pd.DataFrame({'waterLevel': zzz, 'volume': vvv}).sort_values(by='waterLevel', ascending=True)

        # 2 生成水库特征库容
        self.v_dead = np.interp(self.h_dead, zzz, vvv)
        self.v_max_wet_season = np.interp(self.h_max_wet_season, zzz, vvv)
        self.v_max_typhoon = np.interp(self.h_max_typhoon, zzz, vvv)
        self.v_normal = np.interp(self.h_normal, zzz, vvv)

        # 3-1 调度线程序基本参数读取
        if self.if_cal_control_line:
            self.users = None  # dict_dict 用水户信息 详见add_user
            self.arr_date = pd.to_datetime(info['inflow']['date'])
            self.arr_w_in = info['inflow']['value']

        # 3-2 库群程序基本参数读取
        if self.if_supply_task:
            self.id = reservoir_id  # int 水库ID
            self.area = info["area"]  # float 集水面积
            self.ave_runoff = info["aveRunoff"]  # float 平均径流量
            self.v_start = info["vStart"]  # float 起调库容
            self.storage_coefficient = info["storageCoefficient"]  # float 库容系数
            self.arr_v_begin = None  # float 时段初库容
            self.reservoir_users = None  # dict_dict 用水户信息 详见add_need_user
            self.complete_rank = 0  # 已完成计算的用水户个数

            # 是否弃水至其他水库
            self.if_down_2_other_reservoir = info.get("ifDownToOtherRes", False)  # bl 是否弃水至其他水库
            if self.if_down_2_other_reservoir:
                self.down_reservoirs = info["DownReservoirs"]  # list 下游水库名称，示例：["水库1", "水库2"]

            # 是否接受其他水库弃水
            self.if_up_2_this_reservoir = False  # bl 是否接受其他水库弃水
            self.up_reservoirs = None  # dict_dict 上游水库信息 详见add_up_reservoir
            # self.arr_up_reservoir_waste = None  # array 上游弃水过程

            # 是否调水至其他水库
            self.if_supply_2_other_reservoir = info.get("ifTransferToOtherRes", False)  # bl 是否调水至其他水库
            if self.if_supply_2_other_reservoir:
                self.supply_to_other_reservoirs = info["supplyToOtherResList"]  # dict_dict 调水至其他水库 示例：
                # dict_dict = {
                #     "水库1": {
                #         "transferType":
                #         "minVolumeForSupply": {
                #             "date": min_volume_date[i],
                #             "value": min_volume_value[i]
                #         },
                #         "maxVolumeForReceive": {
                #             "date": max_volume_date[i],
                #             "value": max_volume_value[i]
                #         },
                #         "transferMax": max_transfer[i],
                #         "arrSupplyOut": None,
                #         "minVolumeForSupplyDayDF": DataFrame
                #         "maxVolumeForReceiveDayDF": DataFrame
                #     },
                # }
                # self.arr_supply_to_other = None  # array 外调水出库

            # 是否接受其他水库调水入库
            self.if_receive_from_other_reservoir = False  # bl 是否接受其他水库调水入库
            self.receive_from_other = None  # dict_dict 水源水库信息 详见add_receive_from_other
            # self.arr_receive_from_other = None  # array 外调水入库过程

            # 是否接受用水户回归水入库
            self.if_user_return_2_this_reservoir = False  # bl 是否接受用水户回归水入库
            self.return_users = None  # dict_dict 回归水用水户信息 详见add_return_user
            # self.arr_re_water = None  # array 用水户回归水入库过程

            self.arr_date = None
            self.arr_w_in = None

            # 计算结果统计
            self.result_statistic = None

        # 3-3 发电基本参数读取
        if self.if_power_task:
            # self.cal_step = info['cal_step']  # 计算步长：月month、旬ten_days、日day
            self.cal_mode = info['reservoirType']  # 水库类型：年调节Y-Mode、日调节/无调节D-Mode

            # 机组特征
            self.k0 = info['k0']  # 综合出力系数
            self.k1 = info['k1']  # 水头损失系数
            self.k2 = info['k2']  # 出力不均匀系数
            self.qm = info['qm']  # 机组最大设计流量
            self.wpv = info['wpv']  # 装机容量
            self.dh_max = info['dhMax']  # 最大水头损失
            self.dh_min = info['dhMin']  # 最小水头损失

            # 限制水位、库容
            self.h_dead_power = info.get('hDeadPower', self.h_dead)  # 发电死水位（低于该水位无法发电）
            self.h_limited_power = info.get('hLimitedPower', self.h_dead)  # 发电限制水位（低于该水位不主动发电）
            self.v_dead_power = np.interp(self.h_dead_power, zzz, vvv)
            self.v_limited_power = np.interp(self.h_limited_power, zzz, vvv)

            # 尾水位
            self.const_z_down = info.get('constZDown', False)  # 是否固定尾水位
            # self.const_z_down_val = info.get('constZDownVal', None)  # 固定尾水位
            if self.const_z_down:
                self.z_down_day = info['z_down']
            else:
                self.zq = info['zq']  # 流量-水位

            # 限制库容（逐日）
            # # 发电死库容（逐日）
            v_dead_power_month = {
                "Date": ['01-01', '12-31'], "Value": [self.v_dead_power, self.v_dead_power]
            }
            self.v_dead_power_day = info.get(
                'vDeadPowerDay', ComFun.create_lookup_df(v_dead_power_month, False)
            )
            # # 发电限制库容（逐日）
            v_limited_power_month = {
                "Date": ['01-01', '12-31'], "Value": [self.v_limited_power, self.v_limited_power]
            }
            self.v_limited_power_day = info.get(
                'vLimitedPowerDay', ComFun.create_lookup_df(v_limited_power_month, False)
            )

            # # 库内取水限制库容（逐日）
            self.supply_from_reservoir = info.get('ifSupplyFromReservoir', False)
            if self.supply_from_reservoir:
                self.user_name_list_supply_from_reservoir = info['userNameListSupplyFromReservoir']
                # self.v_limited_supply_from_reservoir_day = info['vLimitedFromReservoir']

            # # 坝下取水限制库容（逐日）
            self.supply_from_q_down = info.get('ifSupplyFromDown', False)
            if self.supply_from_q_down:
                self.user_name_list_supply_from_down = info['userNameListSupplyFromDown']
                # self.v_limited_supply_from_down_day = info['vLimitedFromDown']

            # # 取水限制库容（逐日）
            self.v_limited_supply_day = info['vLimitedSupply']

            # 调度线
            if self.cal_mode == '年调节':
                self.know_operate_line = info['knowOperateLine']  # 是否已知调度线
                if self.know_operate_line:
                    self.operate_line_dict = info['operate_line_dict']
                else:
                    self.target_wpp_k = info['targetWppVal']  # 保证出力倍数
                    self.target_wpp_assure_rate = info['targetWppAssureRate']  # 出力保证率
                    self.assurance_power = 0  # 保证出力

            # 峰电发电时段
            if self.cal_mode == '日调节':  # 日调节水库
                self.hour_peak = info['hourPeak']
            # 上游水库信息
            self.up_reservoirs_power = info.get('upReservoirsNameList', None)  # list 上游水库名列表
            self.qm_up = info.get('qm_up', 0)  # 上级电站满发流量

            # 来水、需水系列
            self.arr_date = pd.to_datetime(info['date'])
            self.arr_q_up = info['up']  # 上游水库来水
            self.arr_q_in = info['inflow']
            # self.arr_q_drink_demand = info['drink']
            # self.arr_q_irrigate_demand = info['irrigate']
            self.arr_q_environment_demand = info['environment']
            # self.arr_q_loss = info['loss']
            self.q_user_demand_from_reservoir_df = info.get('qUserDemandFromReservoirDf', None)
            self.q_user_demand_from_down_df = info.get('qUserDemandFromDownDf', None)

            # 供水顺序
            self.supply_order = info.get('supplyOrder', None)

            # 计算状态
            self.power_cal_status = None

            # 计算结果统计
            self.result_statistic = None

        # 4 水库防洪限制库容
        # # dict={"Date", "Value"}
        self.v_flood_month = {
            "Date": [self.wet_season_start_date, self.typhoon_start_date,
                     (pd.to_datetime('2022-' + self.typhoon_end_date) + pd.DateOffset(1)).strftime('%m-%d')],
            "Value": [self.v_max_wet_season, self.v_max_typhoon, self.v_normal]
        }
        # # pd.DataFrame (形如： Month-Day | Normal_Year_Value | Leap_Year_Value)
        self.v_flood_day = ComFun.create_lookup_df(df_line_month=self.v_flood_month, interpolate=False)
        self.v_cntl_operation = None

        # 5 水库来水量
        if self.if_cal_control_line:
            self.arr_date = pd.to_datetime(info['inflow']['date'])
            self.arr_w_in = info['inflow']['value']

        if self.if_supply_task:
            self.arr_date = None
            self.arr_w_in = None

        if self.if_power_task:
            self.arr_date = pd.to_datetime(info['date'])
            self.arr_q_up = info['up']
            self.arr_q_in = info['inflow']
            self.arr_q_environment_demand = info['environment']

            self.q_gen_arr = None  # 发电流量 (m³/s)
            self.q_thrown_arr = None  # 弃水流量 (m³/s)
            self.q_loss_real_arr = None  # 实际水量损失
            self.v_store_arr = None  # 时段末库容序列
            self.z_store_arr = None  # 时段末水位序列
            self.z_up_arr = None  # 上游水位
            self.z_down_arr = None  # 下游尾水位
            self.dh_loss_arr = None  # 水头损失
            self.h_net_arr = None  # 净水头
            self.power_arr = None  # 出力（万kW）

            # 供水量、缺水量、缺水时段数
            # # 库内
            self.q_supply_from_reservoir_df = None
            self.q_lack_from_reservoir_df = None
            self.lack_whether_from_reservoir_df = None
            # # 坝下
            self.q_supply_from_q_down_df = None
            self.q_lack_from_q_down_df = None
            self.lack_whether_from_q_down_df = None

            self.process_result = {}

        # 5 数据初始化
        # self.refresh()

    def refresh(self, num_series=None):
        """数据初始化"""
        if num_series is None:
            num_series = len(self.arr_date)

        if self.if_cal_control_line:
            self.arr_loss = np.zeros(num_series)  # array，时段损失水量
            self.arr_waste = np.zeros(num_series)  # array，时段弃水量
            self.arr_v_end = np.ones(num_series) * self.v_dead  # array，时段末库容

        if self.if_supply_task:
            self.arr_loss = np.zeros(num_series)  # array，时段损失水量
            self.arr_waste = np.zeros(num_series)  # array，时段弃水量
            self.arr_v_end = np.ones(num_series) * self.v_dead  # array，时段末库容

            self.arr_v_begin = np.ones(num_series) * self.v_dead  # array，时段初库容
            self.complete_rank = 0  # int 已完成计算的用水户个数
            if self.if_up_2_this_reservoir:
                for key, up_reservoir in self.up_reservoirs.items():
                    up_reservoir["arrUpReservoir"] = np.zeros(num_series)  # array，时段上游弃水量

            if self.if_supply_2_other_reservoir:
                for key, other_reservoir in self.supply_to_other_reservoirs.items():
                    other_reservoir["arrSupplyOut"] = np.zeros(num_series)  # array，时段调出水量

            if self.if_receive_from_other_reservoir:
                for key, other_reservoir in self.receive_from_other.items():
                    other_reservoir["arrReceive"] = np.zeros(num_series)  # array，时段调入水量

            if self.if_user_return_2_this_reservoir:
                for key, return_user in self.return_users.items():
                    return_user["arrReturn"] = np.zeros(num_series)  # array，回归水量

            # 计算结果统计
            self.result_statistic = {
                "InStatis": None,
                "LossStatis": None,
                "WasteStatis": None,
                "VEndStatis": None
            }

        if self.if_power_task:
            self.arr_q_loss = np.zeros(num_series)  # array，时段损失水量
            self.arr_q_waste = np.zeros(num_series)  # array，时段弃水量
            self.arr_v_end = np.ones(num_series) * self.v_dead  # array，时段末库容

            self.power_cal_status = CalStatus.NOT_DO
            self.arr_q_up = np.zeros(num_series)

            # 计算结果统计
            self.process_result = {}

            # # 调度线
            # if not self.know_operate_line:
            #     self.n_operate_line = len(self.target_power_k)
            #     self.operate_line_dict = {
            #         "01-01": [[], []],
            #         "02-01": [[], []],
            #         "03-01": [[], []],
            #         "04-01": [[], []],
            #         "05-01": [[], []],
            #         "06-01": [[], []],
            #         "07-01": [[], []],
            #         "08-01": [[], []],
            #         "09-01": [[], []],
            #         "10-01": [[], []],
            #         "11-01": [[], []],
            #         "12-01": [[], []],
            #     }

    def refresh_sub_function_for_power_task(self, n_series):
        """发电计算数组初始化"""
        self.q_gen_arr = np.zeros(n_series)  # 发电流量 (m³/s)
        self.q_thrown_arr = np.zeros(n_series)  # 弃水流量 (m³/s)
        self.q_loss_real_arr = np.zeros(n_series)  # 实际水量损失
        self.v_store_arr = np.zeros(n_series)  # 时段末库容序列
        self.z_store_arr = np.zeros(n_series)  # 时段末水位序列
        self.z_up_arr = np.zeros(n_series)  # 上游水位
        self.z_down_arr = np.zeros(n_series)  # 下游尾水位
        self.dh_loss_arr = np.zeros(n_series)  # 水头损失
        self.h_net_arr = np.zeros(n_series)  # 净水头
        self.power_arr = np.zeros(n_series)  # 出力（万kW）

        # 供水量、缺水量、缺水时段数
        # # 库内
        if self.supply_from_reservoir:
            user_name_list = self.user_name_list_supply_from_reservoir
            num_user = len(user_name_list)
            tmp_df = pd.DataFrame(
                np.zeros((n_series, num_user)),
                columns=user_name_list
            )
            self.q_supply_from_reservoir_df = tmp_df.copy()
            self.q_lack_from_reservoir_df = tmp_df.copy()
            self.lack_whether_from_reservoir_df = tmp_df.copy()
        else:
            self.q_supply_from_reservoir_df = pd.DataFrame()
            self.q_lack_from_reservoir_df = pd.DataFrame()
            self.lack_whether_from_reservoir_df = pd.DataFrame()

        # # 坝下
        if self.supply_from_q_down:
            user_name_list = self.user_name_list_supply_from_down
            num_user = len(user_name_list)
            tmp_df = pd.DataFrame(
                np.zeros((n_series, num_user)),
                columns=user_name_list
            )
            self.q_supply_from_q_down_df = tmp_df.copy()
            self.q_lack_from_q_down_df = tmp_df.copy()
            self.lack_whether_from_q_down_df = tmp_df.copy()
        else:
            self.q_supply_from_q_down_df = pd.DataFrame()
            self.q_lack_from_q_down_df = pd.DataFrame()
            self.lack_whether_from_q_down_df = pd.DataFrame()

        # # 生态
        self.environment_supply_arr = np.zeros(n_series)
        self.environment_lack_arr = np.zeros(n_series)
        self.environment_lack_whether_arr = np.zeros(n_series)

    def transfer_cal_step(self, origin_cal_step, new_cal_step):
        """转换计算尺度"""
        if self.if_power_task:
            self.arr_q_up = ComFun.transfer_process(
                self.arr_date, self.arr_q_up, origin_cal_step, new_cal_step, 'ave'
            )
            self.arr_q_in = ComFun.transfer_process(
                self.arr_date, self.arr_q_in, origin_cal_step, new_cal_step, 'ave'
            )

            if self.supply_from_reservoir:
                user_name_list_supply_from_reservoir = self.user_name_list_supply_from_reservoir
                origin_q_user_demand_from_reservoir_df = self.q_user_demand_from_reservoir_df.copy()
                new_q_user_demand_from_reservoir_df = origin_q_user_demand_from_reservoir_df.copy()
                for user_name in user_name_list_supply_from_reservoir:
                    tmp_arr = origin_q_user_demand_from_reservoir_df[user_name]
                    new_q_user_demand_from_reservoir_df[user_name] = ComFun.transfer_process(
                        self.arr_date, tmp_arr, origin_cal_step, new_cal_step, 'ave'
                    )

            if self.supply_from_q_down:
                user_name_list_supply_from_down = self.user_name_list_supply_from_down
                origin_q_user_demand_from_down_df = self.q_user_demand_from_down_df.copy()
                new_q_user_demand_from_down_df = origin_q_user_demand_from_down_df.copy()
                for user_name in user_name_list_supply_from_down:
                    tmp_arr = origin_q_user_demand_from_down_df[user_name]
                    new_q_user_demand_from_down_df[user_name] = ComFun.transfer_process(
                        self.arr_date, tmp_arr, origin_cal_step, new_cal_step, 'ave'
                    )

            self.arr_q_environment_demand = ComFun.transfer_process(
                self.arr_date, self.arr_q_environment_demand, origin_cal_step, new_cal_step, 'ave'
            )

            self.arr_q_loss = ComFun.transfer_process(
                self.arr_date, self.arr_q_loss, origin_cal_step, new_cal_step, 'ave'
            )
            self.arr_date = pd.to_datetime(
                ComFun.transfer_process(
                    self.arr_date, self.arr_date, origin_cal_step, new_cal_step, 'first'
                )
            )

    def check_date(self):
        """日期检查"""
        # 梅汛期起止时间
        wsd = pd.to_datetime('2024-' + self.wet_season_start_date)  # pd.to_datetime，梅汛期开始时间
        wed = pd.to_datetime('2024-' + self.wet_season_end_date)  # pd.to_datetime，梅汛期结束时间
        # 台汛期起止时间
        tsd = pd.to_datetime('2024-' + self.typhoon_start_date)  # pd.to_datetime，台汛期开始时间
        ted = pd.to_datetime('2024-' + self.typhoon_end_date)  # pd.to_datetime，台汛期结束时间

        # 检验输入的梅汛期、台汛期
        if wsd >= wed:
            raise ValueError("梅汛期日期输入有误，开始时间应在结束之前")
        elif wed >= tsd:
            raise ValueError("梅汛期结束时间和台汛期开始时间冲突，梅汛期结束时间应在台汛期开始之前")
        elif tsd >= ted:
            raise ValueError("台汛期日期输入有误，开始时间应在结束之前")

    # 调度线程序
    def add_user(self, users):
        """
        添加用水户信息
        Args:
            users: list_structUser 用水户信息
        Returns: dict_dict 【用户名】:assureRate、v_month、line_month、v_line_month、h_line_month
        """
        user_dict = {}
        for tmp_user in users:
            tmp_user_name = tmp_user.name
            tmp_user_assure_rate = tmp_user.assure_rate
            user_dict[tmp_user_name] = {
                'assureRate': tmp_user_assure_rate,  # 保证率
                'v_month': None,  # 限制库容（逐年逐月排列）
                'line_month': None,  # 调度线（月份）
                'v_line_month': None,  # 调度线（库容）
                'h_line_month': None,  # 调度线（水位）
            }
        self.users = user_dict

    # 库群程序
    def add_need_user(self, need_user, supply_id, reservoir_line):
        """
        添加用水户信息
        Args:
            need_user: structUser 用水户信息
            supply_id: 供水列表顺序
            reservoir_line: 供水限制线，DataFrame (columns=["Date", "Value"])
        Returns: dict_dict
        """
        if self.reservoir_users is None:
            self.reservoir_users = {
                'by_name': {},
                'by_cal_rank': {}
            }

        tmp_user = need_user
        tmp_reservoir_user = {
            "userName": tmp_user.name,
            "userID": tmp_user.id,
            "supplyID": supply_id,
            "calRank": self.complete_rank,
            "reservoirLine": reservoir_line
        }
        self.reservoir_users['by_name'][tmp_user.name] = tmp_reservoir_user
        self.complete_rank += 1  # 已完成计算的用水户个数，此处临时作为供水计算优先次序，值越小，越靠前，默认取供水列表中的顺序

    def add_up_reservoir(self, up_reservoir, waste_ic):
        """
        添加上游水库（弃水至本水库）
        Args:
            up_reservoir: structReservoir 水库信息
            waste_ic: list_dict 弃水量换算比例
        Returns: dict_dict
        """
        if self.up_reservoirs is None:
            self.up_reservoirs = {}

        tmp_reservoir = up_reservoir
        tmp_up_reservoir = {
            # "reservoirName": tmp_reservoir.name,
            "reservoirID": tmp_reservoir.id,
            "wasteInEfficient": waste_ic,
            "arrUpReservoir": None  # array 外调水调出水量
        }
        self.up_reservoirs[tmp_reservoir.name] = tmp_up_reservoir

    def add_receive_from_other(self, reservoir, transfer_ic):
        """
        外调至本水库
        Args:
            reservoir: list_structReservoir, 调出的水库
            transfer_ic: float 实际调水量（扣除漏损）
        Returns: dict_dict
        """
        if self.receive_from_other is None:
            self.receive_from_other = {}

        tmp_reservoir = reservoir
        tmp_receive_from_other = tmp_reservoir.supply_to_other_reservoirs[self.name]
        tmp_receive_from_other["reservoirID"] = tmp_reservoir.id  # 水源水库名
        tmp_receive_from_other["transferIC"] = transfer_ic  # float 调水入库比列=入库量（出库量-扣除漏损）/出库量
        tmp_receive_from_other["arrReceive"] = None  # array 外调水入库过程

        self.receive_from_other[tmp_reservoir.name] = tmp_receive_from_other

    def add_return_user(self, return_user):
        """
        添加信息回归水信息
        Args:
            return_user: structUser 用水户信息
        Returns: list_dict
        """
        if self.return_users is None:
            self.return_users = {}

        tmp_user = return_user
        tmp_return_user = {
            # "userName": tmp_user.name,
            "userID": tmp_user.id,
            "returnEfficient": tmp_user.return_reservoir[self.name]["returnIC"],  # float 回归系数
            "arrReturn": None  # array 回归水过程
        }
        self.return_users[tmp_user.name] = tmp_return_user


class HydroElectricity:
    def __init__(self, reservoirs_dicts, base_info, log_file='log.txt'):
        """
        读取输入信息，包括水库信息表、基础参数等
        Args:
            reservoirs_dicts: 水库（多个）信息
            base_info: 基本计算参数信息
        """
        # 1- 基本参数整理
        self.reservoirs_num = len(reservoirs_dicts)
        self.date_process = next(iter(reservoirs_dicts.values())).arr_date
        self.len_process = len(self.date_process)
        self.reservoirs = reservoirs_dicts

        # 2- 计算基本参数
        dict_para = base_info
        self.cal_step = dict_para["CalStep"]  # 计算步长：月、旬、日
        self.epsilon_h = float(dict_para["EPSYH"])  # 水头精度
        self.epsilon_v = float(dict_para["EPSYV"])   # 库容精度
        self.epsilon_w = float(dict_para["EPSYW"])   # 出力精度
        self.log_file = log_file

        # 3- 结果初始化
        self.process_results_dict = {}

    def calculate(self, max_count=2, max_count_wb=50, max_count_v=50, max_count_hp=50):
        """
        水库群发电计算
        Args:
            max_count: int 最大迭代次数

        Returns:

        """
        # 转化计算步长（日期列）
        self.date_process = pd.to_datetime(
            ComFun.transfer_process(self.date_process, self.date_process,
                                    "日", self.cal_step, 'first')
        )

        # 初始化
        for res_name, tmp_res in self.reservoirs.items():
            tmp_res.refresh()
            tmp_res.power_cal_status = CalStatus.NOT_DO
            # 转化计算步长
            tmp_res.transfer_cal_step("日", self.cal_step)

        # 计算径流调度过程
        for res_name, tmp_res in self.reservoirs.items():
            self.cal_hydroelectricity(tmp_res, max_count, max_count_wb, max_count_v, max_count_hp)

    # 发电调度
    def cal_hydroelectricity(self, reservoir, max_count, max_count_wb, max_count_v, max_count_hp):
        """
        单个水库发电计算
        Args:
            reservoir: StructReservoir 水库信息
            max_count: int 最大迭代次数
            max_count_wb: int 试算调度线时，出力最大试算次数
            max_count_v: int 试算调度线时，库容最大试算次数
            max_count_hp: int 试算调度线时，假定水头最大试算次数

        Returns:

        """
        # 1- 读取计算状态
        res_status = reservoir.power_cal_status
        if res_status == CalStatus.NOT_DO:
            # 未计算的情况，改为正在计算，并完成上游水库计算
            reservoir.power_cal_status = CalStatus.DOING

            up_tmp_res_names = reservoir.up_reservoirs_power  # 上游水库列表
            if not (up_tmp_res_names is None):  # 上游水库不为空
                for up_tmp_res_name in up_tmp_res_names:
                    tmp_res = self.reservoirs[up_tmp_res_name]

                    # 上下游计算步长不一致
                    if reservoir.cal_mode != tmp_res.cal_mode:
                        wrong_info = f"错误：{reservoir.name} 与上游水库 {tmp_res.name}的计算步长不一致！"
                        log_error(self.log_file, wrong_info)
                        raise ValueError(wrong_info)

                    self.cal_hydroelectricity(tmp_res, max_count)
                    q_up_origin_arr = tmp_res.q_power_arr + tmp_res.q_thrown_arr
                    reservoir.q_up_arr += q_up_origin_arr
                    reservoir.qm_up += tmp_res.qm

        elif res_status == CalStatus.DOING:
            # 正在计算状态下，为避免循环，不进入判断
            wrong_info = f"错误：{reservoir.name} 作为自己上游水库，计算陷入循环"
            log_error(self.log_file, wrong_info)
            raise ValueError(wrong_info)

        elif res_status == CalStatus.DONE:
            # 计算完成状态
            return

        # 2- 如果当前是Doing状态，则继续处理后续计算
        cal_mode = reservoir.cal_mode
        if cal_mode == "年调节":  # 年调节
            if reservoir.know_operate_line:
                reservoir.process_result = self.power_operate_year(reservoir, max_count)
            else:
                # 包含 调度线计算、调度线更新后年调节计算
                reservoir.process_result = self.cal_operate_line(reservoir=reservoir,
                                                                 rate_assurance_power=reservoir.rate_assurance_power,
                                                                 max_count_wb=max_count_wb,
                                                                 max_count_v=max_count_v,
                                                                 max_count_hp=max_count_hp)

        elif cal_mode == "日调节":  # 日调节
            # 日调节水库计算步长不为日
            if self.cal_step != "日":
                wrong_info = f"错误：{reservoir.name} 为日调节水库，计算步长不可为 {reservoir.cal_step}！"
                log_error(self.log_file, wrong_info)
                raise ValueError(wrong_info)

            reservoir.process_result = self.power_operate_day(reservoir)

    # 年调节计算
    # def power_operate_year(self, reservoir: StructReservoir, max_count: int, v_start=None):
    #     """
    #     发电年调节计算
    #     Args:
    #         reservoir: StructReservoir 水库
    #         max_count: int 最大迭代次数
    #         v_start: float 初始库容
    #
    #     Returns:
    #
    #     """
    #     # 防止传参错误
    #     if max_count <= 0:
    #         wrong_info = f"传参错误：最大迭代次数为0"
    #         log_error(self.log_file, wrong_info)
    #         raise ValueError(wrong_info)
    #
    #     # 参数
    #     v_normal = reservoir.v_normal
    #     v_dead = reservoir.v_dead
    #
    #     wpv = reservoir.wpv
    #     loss_ratio = reservoir.loss_ratio
    #     loss_value = reservoir.loss_value
    #
    #     # 系列
    #     operate_line_dict = reservoir.operate_line_dict  # 调度线 {"01-01":[[],[]], "02-01":[[],[]]}
    #     z_down_day = reservoir.z_down_day
    #     v_flood_day = reservoir.v_flood_day  # 洪水限制库容（系列）
    #     v_dead_power_day = reservoir.v_dead_power_day  # 发电死库容（系列）
    #     v_limited_power_day = reservoir.v_limited_power_day  # 发电限制库容（系列）
    #     # v_limited_drink_day = reservoir.v_limited_drink_day  # 供水限制库容（系列）
    #     # v_limited_irrigate_day = reservoir.v_limited_irrigate_day  # 灌溉限制库容（系列）
    #     # v_limited_down_user_day_list = reservoir.v_limited_down_user_day_list  # 20250905 下泄水量控制线
    #
    #     q_in_arr = reservoir.arr_q_in + reservoir.arr_q_up  # 来水过程
    #     # q_drink_arr = reservoir.arr_q_drink_demand
    #     # q_irrigate_arr = reservoir.arr_q_irrigate_demand
    #
    #     q_environment_arr = reservoir.arr_q_environment_demand
    #     # num_down_users = len(q_environment_arr[0])  # 20250905 下泄流量分档（湖南镇特殊处理）
    #     # q_loss_arr = reservoir.arr_q_loss  # 损失水量
    #
    #     if reservoir.supply_from_reservoir:
    #         user_name_list_supply_from_reservoir = reservoir.user_name_list_supply_from_reservoir
    #         v_limited_supply_from_reservoir_day = reservoir.v_limited_supply_from_reservoir_day
    #         q_user_demand_from_reservoir_df = reservoir.q_user_demand_from_reservoir_df
    #
    #     if reservoir.supply_from_q_down:
    #         user_name_list_supply_from_down = reservoir.user_name_list_supply_from_down
    #         v_limited_supply_from_down_day = reservoir.v_limited_supply_from_down_day
    #         q_user_demand_from_down_df = reservoir.q_user_demand_from_down_df
    #
    #     # 提前处理日期信息
    #     date_process = self.date_process
    #     n_series = len(date_process)  # 序列长
    #
    #     days_diff = (date_process[1:] - date_process[:-1]).days
    #     days_arr = np.concatenate([days_diff, [days_diff[-1]]])  # 天数
    #
    #     mmdd_array = date_process.strftime('%m-%d')
    #     year_array = date_process.year
    #     is_leap_array = ((year_array % 4 == 0) & (year_array % 100 != 0)) | (year_array % 400 == 0)
    #     year_col_array = np.where(is_leap_array, 'leap_year', 'normal_year')
    #
    #     # --- 初始库容设置 ---
    #     if v_start is None:
    #         v_start = reservoir.v_limited_power + 0.7 * (v_normal - reservoir.v_limited_power)
    #
    #     # --- 供水量、缺水量、缺水时段数缓存 ---
    #     if reservoir.supply_from_reservoir:
    #         num_user_supply_from_reservoir = len(user_name_list_supply_from_reservoir)
    #         tmp_df_from_reservoir = pd.DataFrame(np.zeros((n_series, num_user_supply_from_reservoir)),
    #                                              columns=user_name_list_supply_from_reservoir)
    #
    #     if reservoir.supply_from_q_down:
    #         num_user_supply_from_q_down = len(user_name_list_supply_from_down)
    #         tmp_df_from_q_down = pd.DataFrame(np.zeros((n_series, num_user_supply_from_reservoir)),
    #                                           columns=user_name_list_supply_from_down)
    #
    #     for i_count in range(max_count):
    #         # --- 数组初始化 ---
    #         q_gen_arr = np.zeros(n_series)  # 发电流量 (m³/s)
    #         q_thrown_arr = np.zeros(n_series)  # 弃水流量 (m³/s)
    #         q_loss_real_arr = np.zeros(n_series)  # 实际水量损失
    #         v_store_arr = np.zeros(n_series)  # 时段末库容序列
    #         z_store_arr = np.zeros(n_series)  # 时段末水位序列
    #         z_up_arr = np.zeros(n_series)  # 上游水位
    #         z_down_arr = np.zeros(n_series)  # 下游尾水位
    #         dh_loss_arr = np.zeros(n_series)  # 水头损失
    #         h_net_arr = np.zeros(n_series)  # 净水头
    #         power_arr = np.zeros(n_series)  # 出力（万kW）
    #
    #         # 供水量
    #         # q_drink_supplied_arr = np.zeros(n_series)
    #         # q_irrigate_supplied_arr = np.zeros(n_series)
    #         environment_supply_arr = np.zeros(n_series)
    #         q_supply_from_reservoir_df = tmp_df_from_reservoir.copy()
    #         q_supply_from_down_df = tmp_df_from_q_down.copy()
    #
    #         # 缺水量
    #         # drink_lack_arr = np.zeros(n_series)
    #         # irrigate_lack_arr = np.zeros(n_series)
    #         q_lack_from_reservoir_df = tmp_df_from_reservoir.copy()
    #         q_lack_from_down_df = tmp_df_from_q_down.copy()
    #         environment_lack_arr = np.zeros(n_series)
    #
    #         # 缺水时段判读（0/1）
    #         # drink_lack_whether_arr = np.zeros(n_series)
    #         # irrigate_lack_whether_arr = np.zeros(n_series)
    #         lack_whether_from_reservoir_df = tmp_df_from_reservoir.copy()
    #         lack_whether_from_down_df = tmp_df_from_q_down.copy()
    #         environment_lack_whether_arr = np.zeros(n_series)
    #
    #         # # 20250905 下泄流量分档
    #         # down_user_demand_arr = np.zeros((n_series, num_down_users))
    #         # down_user_supplied_arr = np.zeros((n_series, num_down_users))
    #         # down_user_lack_arr = np.zeros((n_series, num_down_users))
    #
    #         v_begin = v_start  # 当前时段初库容
    #
    #         # --- 逐时段计算 ---
    #         for i in range(n_series):  # 逐时刻
    #             current_year_col = year_col_array[i]
    #             current_mmdd = mmdd_array[i]
    #
    #             # --- 时间步长换算系数 ---
    #             dt = float(days_arr[i] * 8.64)
    #
    #             # --- 恒定尾水位 ---
    #             if reservoir.const_z_down:
    #                 const_z_down_val = z_down_day.loc[current_mmdd][current_year_col]  # 尾水位
    #             else:
    #                 const_z_down_val = -1
    #
    #             # --- 限制库容 ---
    #             v_flood = v_flood_day.loc[current_mmdd][current_year_col]  # 防洪
    #             v_dead_power = v_dead_power_day.loc[current_mmdd][current_year_col]  # 发电死库容
    #             v_limited_power = v_limited_power_day.loc[current_mmdd][current_year_col]  # 发电限制库容
    #             # v_limited_drink = v_limited_drink_day.loc[current_mmdd][current_year_col]  # 供水
    #             # v_limited_irrigate = v_limited_irrigate_day.loc[current_mmdd][current_year_col]  # 灌溉
    #
    #             # # # 20250905
    #             # v_limited_down_user_list = []
    #             # for down_user_i in range(len(v_limited_down_user_day_list)):
    #             #     tmp_v_limited_down_user = v_limited_down_user_day_list[down_user_i].loc[current_mmdd][current_year_col]
    #             #     v_limited_down_user_list.append(tmp_v_limited_down_user)
    #
    #             # --- 获取当前调度线 ---
    #             x_line_list = operate_line_dict[current_mmdd][current_year_col]
    #             x_line_list[0].insert(0, v_flood)
    #             x_line_list[1].insert(0, wpv)
    #             x_line_list[0].append(v_limited_power)
    #             x_line_list[1].append(0)
    #
    #             # --- 入流计算 ---
    #             q_loss_real_arr[i] = v_begin * loss_ratio / dt + loss_value / 8.64
    #             q_available = q_in_arr[i] - q_loss_real_arr[i]  # 入库净流量
    #
    #             # # --- 预留生态流量 ---
    #             # q_eco = q_environment_arr[i].sum()  # 20250905 修改，将必须下泄的水量分为生活工业、灌溉、生态三项
    #             q_eco = q_environment_arr[i]
    #             q_available = q_available - q_eco
    #
    #             # --- 供水模块-库内（饮用 & 灌溉） ---
    #             if reservoir.supply_from_reservoir:
    #                 for i_user_supply_from_reservoir in range(num_user_supply_from_reservoir):
    #                     user_name = user_name_list_supply_from_reservoir[i_user_supply_from_reservoir]
    #                     tmp_v_limited = v_limited_supply_from_reservoir_day[user_name].loc[current_mmdd][current_year_col]
    #                     tmp_q_demand = q_user_demand_from_reservoir_df.iloc[i, i_user_supply_from_reservoir]
    #                     tmp_q = max(0, q_available + (v_start - tmp_v_limited) / dt)  # 最大可供水量
    #                     tmp_q_supply = min(tmp_q, tmp_q_demand)  # 实际供水量
    #                     q_available -= tmp_q_supply
    #                     # 储存
    #                     q_supply_from_reservoir_df.iloc[i, i_user_supply_from_reservoir] = tmp_q_supply
    #                     q_lack_from_reservoir_df.iloc[i, i_user_supply_from_reservoir] = tmp_q_demand - tmp_q_supply
    #                     if tmp_q_demand - tmp_q_supply > 0:
    #                         lack_whether_from_reservoir_df.loc[i, str(user_name)] = 1
    #
    #             # 更新可用流量（已扣除供水）
    #             q_available = q_available - q_supply_from_reservoir_df.iloc[i, :].sum() + q_eco
    #
    #             # --- 发电调度主逻辑 ---
    #             q_gen, q_thrown, v_end, z_up, z_down_val, dh, h_net, power = (
    #                 self.operate_sub(
    #                     const_z_down=const_z_down_val,
    #                     reservoir=reservoir,
    #                     v_initial=v_begin,
    #                     q_in=q_available,
    #                     n=1,
    #                     x_line=x_line_list,
    #                     dt=dt,
    #                     v_flood=v_flood,
    #                     v_dead_power=v_dead_power
    #                 )
    #             )
    #
    #             # --- 供水模块-坝下 ---
    #             q_down = q_gen + q_thrown
    #             if reservoir.supply_from_q_down:
    #                 if q_down < q_eco + q_user_demand_from_down_df.iloc[i, :].sum():
    #                     num_down_users = num_user_supply_from_q_down
    #                     demands = q_user_demand_from_down_df.iloc[i, :].values.copy()  # 需量初始化
    #                     supply_lines = []
    #                     for user_name in user_name_list_supply_from_down:
    #                         supply_lines.append(
    #                             v_limited_supply_from_down_day[user_name].loc[current_mmdd][current_year_col]
    #                         )
    #                     supplied = np.zeros(num_down_users)  # 供量初始化
    #                     lack = demands.copy()  # 缺口初始化
    #                     # supply_lines = v_limited_down_user_list  # 20250905 下泄限制分档
    #
    #                     # --- 阶段1：初步分配（确定哪些用户需要补水）---
    #                     cumsum_demand = np.append(np.cumsum(list(demands)), 0)  # [d1, d1+d2, ...]
    #                     for j in range(num_down_users):
    #                         if q_down < cumsum_demand[j]:
    #                             supplied[j] = q_down - cumsum_demand[j-1]
    #                             lack[j] = demands[j] - supplied[j]
    #                             lack[j + 1:] = demands[j + 1:]
    #                             break
    #                         else:
    #                             supplied[j] = demands[j]
    #                             lack[j] = 0
    #
    #                     # --- 阶段2：按优先级尝试补水（从高到低）---
    #                     qt_tmp = q_down
    #                     v_tmp = v_end
    #                     for j in range(num_down_users):
    #                         if lack[j] == 0:
    #                             continue  # 无需补水
    #
    #                         v_min = supply_lines[j]  # 当前用户的停供线
    #
    #                         if v_tmp <= v_min:
    #                             continue  # 当前库容已低于停供线，无法补水
    #
    #                         # 计算最大可补水流量（不跌破停供线）
    #                         q_max_release = (v_tmp - v_min) / dt + qt_tmp
    #                         q_needed = lack[j]
    #                         q_to_release = min(q_needed, q_max_release)
    #
    #                         if q_to_release > 0:
    #                             qt_tmp += q_to_release
    #                             v_tmp = v_begin + (q_available - qt_tmp) * dt
    #                             supplied[j] += q_to_release
    #                             lack[j] -= q_to_release
    #
    #                         if lack[j] > 0:
    #                             environment_lack_whether_arr[i] = dt
    #
    #                     # --- 阶段3：补水后，更新发电流量、库容 ---
    #                     q_gen = qt_tmp
    #                     if q_gen > reservoir.qm:
    #                         q_gen = reservoir.qm
    #                         q_thrown = qt_tmp - q_gen
    #                     v_end = v_tmp
    #
    #                     # --- 阶段4：发电计算 ---
    #                     # 下泄流量是否均能发电
    #                     tmp_q_gen = max(0, q_available + (v_begin - v_dead) / dt)  # 可发电水量
    #                     if tmp_q_gen < q_gen:  # 不可
    #                         q_gen = tmp_q_gen
    #                         q_thrown = qt_tmp - q_gen
    #
    #                     # 上游库水位
    #                     z_up = np.interp((v_begin + v_end) / 2, reservoir.zv['volume'], reservoir.zv['waterLevel'])
    #
    #                     # 下游尾水位
    #                     if reservoir.const_z_down:
    #                         z_down_val = const_z_down_val
    #                     else:
    #                         z_down_val = np.interp(
    #                             (q_gen + q_thrown), reservoir.zq['q_down'], reservoir.zq['waterLevel']
    #                         )
    #
    #                     # 水头损失
    #                     dh = self.cal_dh(reservoir, (q_gen + q_thrown))
    #
    #                     # 净水头
    #                     h_net = z_up - z_down_val - dh
    #
    #                     # 出力
    #                     power = reservoir.k0 * q_gen * h_net
    #
    #             # --- 生态流量兜底校核 ---
    #             if q_down < q_eco:  # 生态下泄不足
    #                 tmp_q_down = max(0, q_available + (v_begin - v_dead) / dt)  # 可下泄水量
    #                 # tmp_q_gen = max(0, q_available + (v_begin - v_limited_power) / dt)  # 可发电水量
    #                 tmp_q_gen = max(0, q_available + (v_begin - v_dead_power) / dt)  # 可发电水量
    #
    #                 # 是否可满足生态下泄
    #                 if tmp_q_down < q_eco:  # 不可满足
    #                     environment_supply_arr[i] = tmp_q_down
    #                     environment_lack_arr[i] = q_eco - tmp_q_down
    #                     environment_lack_whether_arr[i] = 1
    #                     q_down = tmp_q_down
    #                 else:
    #                     environment_supply_arr[i] = tmp_q_down
    #                     q_down = q_eco
    #
    #                 # 下泄流量是否均能发电
    #                 if tmp_q_gen < q_down:  # 不可
    #                     q_gen = tmp_q_gen
    #                     q_thrown = q_down - q_gen
    #                 else:
    #                     q_gen = q_down
    #
    #                 # 时段末库容
    #                 v_end = v_begin + (q_available - q_down) * dt
    #
    #
    #                 # 上游库水位
    #                 z_up = np.interp((v_begin + v_end) / 2, reservoir.zv['volume'], reservoir.zv['waterLevel'])
    #
    #                 # 下游尾水位
    #                 if reservoir.const_z_down:
    #                     z_down_val = const_z_down_val
    #                 else:
    #                     z_down_val = np.interp((q_gen + q_thrown), reservoir.zq['q_down'], reservoir.zq['waterLevel'])
    #
    #                 # 水头损失
    #                 dh = self.cal_dh(reservoir, (q_gen + q_thrown))
    #
    #                 # 净水头
    #                 h_net = z_up - z_down_val - dh
    #
    #                 # 出力
    #                 power = reservoir.k0 * q_gen * h_net
    #
    #             # --- 存储结果 ---
    #             q_gen_arr[i] = q_gen
    #             q_thrown_arr[i] = q_thrown
    #             v_store_arr[i] = v_end
    #             z_up_arr[i] = z_up
    #             z_down_arr[i] = z_down_val
    #             dh_loss_arr[i] = dh
    #             h_net_arr[i] = h_net
    #             power_arr[i] = power
    #             z_store_arr[i] = np.interp(v_end, reservoir.zv['volume'], reservoir.zv['waterLevel'])
    #             # z_store_arr[i] = reservoir._z_of_v(v_end)
    #
    #             # 20250905 下泄流量分档
    #             # for down_user_i in range(num_down_users):
    #             #     down_user_demand_arr[i, down_user_i] = demands[down_user_i]
    #             #     down_user_supplied_arr[i, down_user_i] = supplied[down_user_i]
    #             #     down_user_lack_arr[i, down_user_i] = lack[down_user_i]
    #
    #             # --- 为下一时段准备 ---
    #             v_begin = v_end
    #
    #         # 判断是否需要再算一遍，满足计算时段内起始库容和结束库容一致
    #         if abs(v_start - v_end) >= self.epsilon_v:
    #             print(f'第{i_count}轮：{v_start} - {v_end} = {v_start - v_end} ')
    #             v_start = v_end
    #         else:  # 始末库容均一致，无需开启二次计算
    #             print(f'{v_store_arr[0]} {v_store_arr[-1]}')
    #             print(f'第{i_count}轮：{v_start} - {v_end} = {v_start - v_end} ')
    #             print(f"迭代次数：{i_count}")
    #             break
    #
    #     process_table = {}
    #     process_table['date'] = date_process
    #     process_table['Qin'] = q_in_arr
    #     process_table['QPower'] = q_gen_arr
    #     process_table['DQQ'] = q_thrown_arr
    #     process_table['V'] = v_store_arr
    #     process_table['H'] = h_net_arr
    #     process_table['Power'] = power_arr
    #
    #     for user_name in user_name_list_supply_from_reservoir:
    #         process_table[user_name+'_Need'] = q_user_demand_from_reservoir_df[user_name]
    #     for user_name in user_name_list_supply_from_down:
    #         process_table[user_name+'_Need'] = q_user_demand_from_down_df[user_name]
    #     process_table['QEnv'] = q_environment_arr
    #
    #     for user_name in user_name_list_supply_from_reservoir:
    #         process_table[user_name+'_Supply'] = q_supply_from_reservoir_df[user_name]
    #     for user_name in user_name_list_supply_from_down:
    #         process_table[user_name+'_Supply'] = q_supply_from_down_df[user_name]
    #     process_table['QEnv_Supply'] = environment_supply_arr
    #
    #     for user_name in user_name_list_supply_from_reservoir:
    #         process_table[user_name+'_Lack'] = q_lack_from_reservoir_df[user_name]
    #     for user_name in user_name_list_supply_from_down:
    #         process_table[user_name+'_Lack'] = q_lack_from_down_df[user_name]
    #     process_table['QEnv_Lack'] = environment_lack_arr
    #
    #     for user_name in user_name_list_supply_from_reservoir:
    #         process_table[user_name+'_Need'] = lack_whether_from_reservoir_df[user_name]
    #     for user_name in user_name_list_supply_from_down:
    #         process_table[user_name+'_Need'] = lack_whether_from_down_df[user_name]
    #     process_table['EnvironmentLackDay'] = environment_lack_whether_arr
    #
    #     process_table['Qloss'] = q_loss_real_arr
    #     process_table['Z1'] = z_up_arr
    #     process_table['Z2'] = z_down_arr
    #     process_table['DH'] = dh_loss_arr
    #     process_table['Days'] = days_arr
    #     process_table['Z_End'] = z_store_arr
    #
    #     return process_table

    # 修改后，迭代代替递归
    def operate_sub(self, const_z_down: float, reservoir: StructReservoir, v_initial: float, q_in: float,
                    n: int, x_line: list, dt: float, v_flood: float, v_dead_power: float):
        """
        按调度线迭代计算发电，避免递归，提升效率与稳定性
        """
        n_operate_line = len(x_line[0]) - 1  # 调度线数量（不含防洪）
        qm = reservoir.qm
        k0 = reservoir.k0
        eps_w = self.epsilon_w
        max_iter = 50  # 收敛最大迭代次数，防止死循环

        v_list = x_line[0]  # [v_flood, v1, v2, ...]
        p_list = x_line[1]  # [wpv, p1, p2, ...]

        current_rank = n  # 当前调度线层级

        while current_rank <= n_operate_line:
            v_target = v_list[current_rank]
            p_target = p_list[current_rank]
            p_upper = p_list[current_rank - 1] if current_rank > 0 else float('inf')  # 上一级出力目标

            # 初始发电流量：尝试降至当前调度线
            q_gen = min(max(0.0, q_in + (v_initial - v_target) / dt), qm)

            # 计算实际出力
            q_gen, q_thrown, v_end, z_up, z_down, dh, effective_head, w = self.cal_power(
                const_z_down, reservoir, v_initial, q_in, q_gen, dt, v_flood, v_dead_power
            )

            # 情况①：满足上一级出力目标（WPV/P_{n-1}）
            if w >= p_upper:
                # 需要按上一级目标反推 q_gen 并迭代调整
                target_power = p_upper
                iter_count = 0
                while abs(w - target_power) >= eps_w and iter_count < max_iter:
                    # 根据目标出力求所需流量：w = k0 * q_gen * (dh - dh_loss)
                    if effective_head <= 0:
                        q_gen = 0.0
                    else:
                        q_gen = target_power / (k0 * effective_head)
                        q_gen = max(0.0, min(q_gen, qm))

                    q_gen, q_thrown, v_end, z_up, z_down, dh, effective_head, w = self.cal_power(
                        const_z_down, reservoir, v_initial, q_in, q_gen, dt, v_flood, v_dead_power
                    )
                    iter_count += 1

                # 返回最终结果
                return q_gen, q_thrown, v_end, z_up, z_down, dh, effective_head, w

            # 情况②：满足当前级目标，但不满足上一级
            elif w >= p_target:
                return q_gen, q_thrown, v_end, z_up, z_down, dh, effective_head, w

            # 情况③：不满足当前级目标，尝试下一级调度线
            else:
                # 若还有下一级，则继续循环（current_rank + 1）
                if current_rank < n_operate_line:
                    current_rank += 1
                    continue
                else:
                    # 已是最后一级，仍不满足，则返回当前计算结果（可能低于Pn）
                    return q_gen, q_thrown, v_end, z_up, z_down, dh, effective_head, w

        # 理论上不会走到这里
        raise RuntimeError("调度线逻辑错误：未匹配任何调度等级")

    # 水头损失计算模块
    @staticmethod
    def cal_dh(reservoir: StructReservoir, q: float):
        """
        计算水头损失
        Args:
            reservoir: StructReservoir 水库
            q: float 下泄流量

        Returns:
            dh: float 水头损失
        """
        k1 = reservoir.k1
        k2 = reservoir.k2
        qm = reservoir.qm
        dh_max = reservoir.dh_max
        dh_min = reservoir.dh_min

        dh = min(
            dh_max,
            max(
                dh_min,
                k1 * (k2 * q) ** 2,
                k1 * qm ** 2
            )
        )

        return dh

    # 出力计算模块
    def cal_power(self, const_z_down: float, reservoir: StructReservoir, v_initial: float, q_in: float, q_gen: float,
                  dt: float, v_flood: float, v_limited_power: float):
        """
        出力计算
        Args:
            const_z_down: float 恒定尾水位
            reservoir: StructReservoir 水库
            v_initial: float 时段初库容
            q_in: float 扣除损失和供水量后的入库流量（可能为负值）
            q_gen: float 发电流量
            dt: float 流量->水量转化系数
            v_flood: float 防洪限制库容
            v_limited_power: float 发电限制库容

        Returns:
            q_gen: float 发电流量
            q_thrown: float 弃水流量
            v_end: float 时段末库容
            z_up: float 水头
            z_down: float 出力
            dh: float 水头损失
            w: float 出力

        """
        # 发电流量修正（低于发电限制水位不发电）
        q_gen_max = max(0, q_in + (v_initial - v_limited_power) / dt)  # 最大发电下泄流量，即发电后不低于发电限制水位
        q_gen = min(q_gen, q_gen_max)

        # 弃水流量、末库容
        q_thrown = 0
        v_end = v_initial + (q_in - q_gen) * dt
        if v_end > v_flood:
            q_thrown = (v_end - v_flood) / dt

        v_end = v_initial + (q_in - q_gen - q_thrown) * dt

        z_up, z_down, dh, h_net, w = self.cal_power_sub_function(
            reservoir, v_initial, v_end, const_z_down, q_gen, q_thrown
        )

        return q_gen, q_thrown, v_end, z_up, z_down, dh, h_net, w

    def cal_power_sub_function(self, reservoir: StructReservoir, v_begin: float, v_end: float, const_z_down_val: float,
                               q_gen: float, q_thrown: float):
        # 上游库水位
        z_up = np.interp((v_begin + v_end) / 2, reservoir.zv['volume'], reservoir.zv['waterLevel'])

        # 下游尾水位
        if reservoir.const_z_down:
            z_down_val = const_z_down_val
        else:
            z_down_val = np.interp((q_gen + q_thrown), reservoir.zq['q_down'], reservoir.zq['waterLevel'])

        # 水头损失
        dh = self.cal_dh(reservoir, (q_gen + q_thrown))

        # 净水头
        h_net = z_up - z_down_val - dh

        # 出力
        power = reservoir.k0 * q_gen * h_net

        return z_up, z_down_val, dh, h_net, power

    # def statistic(self):
    #     for res_name, res in self.reservoirs.items():
    #         process_table = res.process_result
    #         process_df = pd.DataFrame(process_table)
    #         # process_df.to_csv("process.csv", sep=',', index=None)
    #
    #         num_year = process_table['date'].year[-1] - process_table['date'].year[0] + 1
    #         ave_w_in = sum(process_table['Qin'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_w_power = sum(process_table['QPower'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_w_thrown = sum(process_table['DQQ'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_w_drink = sum(process_table['QDrink_Supply'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_w_irrigate = sum(process_table['QIrrigate_Supply'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_w_loss = sum(process_table['Qloss'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_power = sum(process_table['Power'] * process_table['Days']) / num_year * 24 / (10 ** 8)
    #         ave_transferout = sum(process_table['QIrrigate_Supply'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_lack = sum(process_table['QIrrigate_Lack'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_lack_day = sum(process_table['IrrigateLackDay'] * process_table['Days'])
    #         ave_z = np.average(process_table['Z_Month_End'])
    #         assurance_power = np.sort(process_table['Power'])[int(0.1 * len(process_table['Power']))]
    #
    #         print(f"年平均来水量：{ave_w_in:.2f}亿m3")
    #         print(f"年平均发电水量：{ave_w_power:.2f}亿m3")
    #         print(f"年平均弃水量：{ave_w_thrown:.2f}亿m3")
    #         print(f"年平均下泄水量：{(ave_w_power + ave_w_thrown):.2f}亿m3")
    #         print(f"年平均库内取水量1：{ave_w_drink:.2f}亿m3")
    #         print(f"年平均库内取水量2：{ave_w_irrigate:.2f}亿m3")
    #         print(f"年平均损失水量：{ave_w_loss:.2f}亿m3")
    #         print(f"年平均水位：{ave_z:.2f}m")
    #         print(f"保证出力：{assurance_power:.0f}kW")
    #         print(f"年平均发电量：{ave_power:.2f}亿kw·h")
    #         # print(f"调水量：{ave_transferout}")
    #         # print(f"缺水量：{ave_lack}")
    #         # print(f"缺水天数：{ave_lack_day}")
    #
    #         column_mapping = {
    #             "date": "日期",
    #             "Qin": "来水流量（m3/s）",
    #             "QPower": "发电流量（m3/s）",
    #             "DQQ": "弃水流量（m3/s）",
    #             "V": "时段末库容（万m3）",
    #             "H": "水头（m）",
    #             "Power": "发电功率（kW）",
    #             "QDrink_Need": "需库内取水流量1（m3/s）",
    #             "QDrink_Supply": "库内取水供水量1（m3/s）",
    #             "QIrrigate_Need": "需库内取水流量2（m3/s）",
    #             "QIrrigate_Supply": "库内取水供水量2（m3/s）",
    #             "Qloss": "实际损失水量（m3/s）",
    #             "Z1": "上游水位（m）",
    #             "Z2": "下游水位（m）",
    #             "DH": "水头损失（m）",
    #             "Days": "本时段总天数（天）",
    #             "Z_Month_End": "时段末水位（m）",
    #             "QDrink_Lack": "库内取水缺水量1（m3/s）",
    #             "QIrrigate_Lack": "库内取水缺水量2（m3/s）",
    #             "DrinkLackDay": "库内取水缺水天数1（天）",
    #             "IrrigateLackDay": "库内取水缺水天数2（天）",
    #             "EnvironmentLackDay": "下泄缺水天数（天）",
    #
    #             "down_user_demand_1": "用水户1需下泄流量（m3/s）",
    #             "down_user_supply_1": "用水户1下泄流量（m3/s）",
    #             "down_user_lack_1": "用水户1缺水流量（m3/s）",
    #
    #             "down_user_demand_2": "用水户2需下泄流量（m3/s）",
    #             "down_user_supply_2": "用水户2下泄流量（m3/s）",
    #             "down_user_lack_2": "用水户2缺水流量（m3/s）",
    #
    #             "down_user_demand_3": "用水户3需下泄流量（m3/s）",
    #             "down_user_supply_3": "用水户3下泄流量（m3/s）",
    #             "down_user_lack_3": "用水户3缺水流量（m3/s）",
    #         }
    #
    #         process_df = process_df.rename(columns=column_mapping)
    #         process_df.to_csv("process.csv", sep=',', index=None, encoding='utf-8')

    # def statistic(self,
    #               res_day_table_file_name="output_逐日过程.txt",
    #               res_mon_table_file_name="output_逐月过程.txt",
    #               res_year_table_file_name="output_逐年过程.txt",
    #               res_hydroyear_table_file_name="output_水文年过程.txt",):
    #     result_day = {}
    #     result_mon = {}
    #     result_year = {}
    #     result_hydroyear = {}
    #     for res_name, res in self.reservoirs.items():
    #         process_table = res.process_result
    #         process_df = pd.DataFrame(process_table)
    #
    #         date_process = process_df['date']
    #         tmp_mon = {}
    #         tmp_year = {}
    #         tmp_hydro_year = {}
    #         for str_col_name in process_df.columns[1:]:  # 首列为date
    #             arr_value = process_df[str_col_name]
    #             # # 日系列转换为月、年
    #             tmp_day_input = pd.DataFrame({
    #                 'Date': date_process,
    #                 'Value': arr_value
    #             })
    #             arr_statistic = ComFun.statistic(tmp_day_input, 0, 4, 3)
    #             tmp_mon[str_col_name] = arr_statistic['Month']['Ave']
    #             tmp_year[str_col_name] = arr_statistic['Year']['Ave']
    #             tmp_hydro_year[str_col_name] = arr_statistic['HydroYear']['Ave']
    #
    #         # index 列
    #         date_process_df = date_process.to_frame(name='年/月/日')
    #         mon_process_df = arr_statistic['Month']['Date'].dt.strftime('%Y-%m').to_frame(name='年/月')
    #         year_process_df = arr_statistic['Year']['Date'].dt.strftime('%Y').to_frame(name='年')
    #         hydro_year_process_df = arr_statistic['HydroYear'].index.to_frame(name='水文年')
    #
    #         result_day[res_name] = process_df.iloc[:, 1:]
    #         result_mon[res_name] = tmp_mon
    #         result_year[res_name] = tmp_year
    #         result_hydroyear[res_name] = tmp_hydro_year
    #
    #         num_year = process_table['date'].year[-1] - process_table['date'].year[0] + 1
    #         ave_w_in = sum(process_table['Qin'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_w_power = sum(process_table['QPower'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_w_thrown = sum(process_table['DQQ'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_w_loss = sum(process_table['Qloss'] * process_table['Days']) / num_year * 8.64 / (10 ** 4)
    #         ave_power = sum(process_table['Power'] * process_table['Days']) / num_year * 24 / (10 ** 8)
    #         ave_z = np.average(process_table['Z_End'])
    #         assurance_power = np.sort(process_table['Power'])[int(0.1 * len(process_table['Power']))]
    #
    #         print(f"年平均来水量：{ave_w_in:.2f}亿m3")
    #         print(f"年平均发电水量：{ave_w_power:.2f}亿m3")
    #         print(f"年平均弃水量：{ave_w_thrown:.2f}亿m3")
    #         print(f"年平均下泄水量：{(ave_w_power + ave_w_thrown):.2f}亿m3")
    #         print(f"年平均损失水量：{ave_w_loss:.2f}亿m3")
    #         print(f"年平均水位：{ave_z:.2f}m")
    #         print(f"保证出力：{assurance_power:.0f}kW")
    #         print(f"年平均发电量：{ave_power:.2f}亿kw·h")
    #
    #         # column_mapping = {
    #         #     "date": "日期",
    #         #     "Qin": "来水流量（m3/s）",
    #         #     "QPower": "发电流量（m3/s）",
    #         #     "DQQ": "弃水流量（m3/s）",
    #         #     "V": "时段末库容（万m3）",
    #         #     "H": "水头（m）",
    #         #     "Power": "发电功率（kW）",
    #         #     "QDrink_Need": "需库内取水流量1（m3/s）",
    #         #     "QDrink_Supply": "库内取水供水量1（m3/s）",
    #         #     "QIrrigate_Need": "需库内取水流量2（m3/s）",
    #         #     "QIrrigate_Supply": "库内取水供水量2（m3/s）",
    #         #     "Qloss": "实际损失水量（m3/s）",
    #         #     "Z1": "上游水位（m）",
    #         #     "Z2": "下游水位（m）",
    #         #     "DH": "水头损失（m）",
    #         #     "Days": "本时段总天数（天）",
    #         #     "Z_Month_End": "时段末水位（m）",
    #         #     "QDrink_Lack": "库内取水缺水量1（m3/s）",
    #         #     "QIrrigate_Lack": "库内取水缺水量2（m3/s）",
    #         #     "DrinkLackDay": "库内取水缺水天数1（天）",
    #         #     "IrrigateLackDay": "库内取水缺水天数2（天）",
    #         #     "EnvironmentLackDay": "下泄缺水天数（天）",
    #         #
    #         #     "down_user_demand_1": "用水户1需下泄流量（m3/s）",
    #         #     "down_user_supply_1": "用水户1下泄流量（m3/s）",
    #         #     "down_user_lack_1": "用水户1缺水流量（m3/s）",
    #         #
    #         #     "down_user_demand_2": "用水户2需下泄流量（m3/s）",
    #         #     "down_user_supply_2": "用水户2下泄流量（m3/s）",
    #         #     "down_user_lack_2": "用水户2缺水流量（m3/s）",
    #         #
    #         #     "down_user_demand_3": "用水户3需下泄流量（m3/s）",
    #         #     "down_user_supply_3": "用水户3下泄流量（m3/s）",
    #         #     "down_user_lack_3": "用水户3缺水流量（m3/s）",
    #         # }
    #         #
    #         # process_df = process_df.rename(columns=column_mapping)
    #         # process_df.to_csv("process.csv", sep=',', index=None, encoding='utf-8')
    #         # process_df.to_csv("output_逐日过程.txt", sep='\t', index=None, encoding='utf-8')
    #
    #     ComFun.statistic_output(dict_dict=result_day, first_col_df=date_process_df,
    #                             output_file_name=res_day_table_file_name)
    #     ComFun.statistic_output(dict_dict=result_mon, first_col_df=mon_process_df,
    #                             output_file_name=res_mon_table_file_name)
    #     ComFun.statistic_output(dict_dict=result_year, first_col_df=year_process_df,
    #                             output_file_name=res_year_table_file_name)
    #     ComFun.statistic_output(dict_dict=result_hydroyear, first_col_df=hydro_year_process_df,
    #                             output_file_name=res_hydroyear_table_file_name)


    # 20251007 湖南镇-黄坛口水库联合调度
    # 供水预处理（依据供水顺序生成对应的需水表及限制库容表）
    @staticmethod
    def get_demand_current(i_series, supply_order_name, v_limited_supply,
                           user_name_list_from_reservoir, demands_from_reservoir,
                           user_name_list_from_q_down, demands_from_q_down,
                           mmdd, year_col):
        if supply_order_name is None or supply_order_name == []:
            return None, None, None

        num_user = len(supply_order_name)
        num_user_from_reservoir = len(user_name_list_from_reservoir)
        num_user_from_q_down = len(user_name_list_from_q_down)
        # user_demand_dict = {}
        demands = np.zeros(num_user)  # 需水
        v_limiteds = np.zeros(num_user)  # 供水限制库容
        if_from_q_down = np.ones(num_user) * -1  # 是否从坝下取（默认从库内取）
        i_user = 0
        for user_name in supply_order_name:
            try:
                id_index = user_name_list_from_reservoir.index(user_name)
                tmp_demands = demands_from_reservoir.iloc[id_index]
                tmp_if_from_q_down = 0
            except ValueError:
                id_index = user_name_list_from_q_down.index(user_name)
                tmp_demands = demands_from_q_down.iloc[id_index]
                tmp_if_from_q_down = 1

            tmp_v_limited_supply = v_limited_supply[user_name].loc[mmdd][year_col]

            demands[i_user] = tmp_demands
            v_limiteds[i_user] = tmp_v_limited_supply
            if_from_q_down[i_user] = tmp_if_from_q_down
            i_user += 1

            # user_demand_dict[str(user_name)] = [tmp_demands, tmp_v_limited_supply, tmp_if_from_q_down]

        return demands, v_limiteds, if_from_q_down

    # 计算供水和发电
    def cal_supply_and_eletricity(self, i_series, reservoir, mmdd, year_col, dt, loss_ratio, loss_value,
                                  q_in, q_eco, supply_order_name,
                                  if_q_up_eco_as_in,  # 控制上库生态流量是否参与供水计算
                                  q_up_eco,  # 上库生态流量不参与供水计算，直接进入发电机组
                                  user_name_list_from_reservoir, user_name_list_from_q_down,
                                  q_user_demand_from_reservoir_df, q_user_demand_from_q_down_df,
                                  # v_limited_supply_from_reservoir_day, v_limited_supply_from_q_down_day,
                                  v_limited_supply_day,
                                  q_supply_from_reservoir_df, q_supply_from_q_down_df,
                                  q_lack_from_reservoir_df, q_lack_from_q_down_df,
                                  lack_whether_from_reservoir_df, lack_whether_from_q_down_df,
                                  if_const_z_down, const_z_down_val,
                                  v_begin, x_line_list,
                                  v_flood, v_limited_power, v_dead_power, v_dead):
        """
        计算供水和发电量
        Parameters:
            i_series : int 时序序号
            reservoir : str 水库名称
            mmdd : str 月-日格式日期
            year_col : bool 是否为闰年
            dt : float 时段转换系数
            loss_ratio : float 时段水库损失比例
            loss_value : float 时段水库损失水量
            q_in : float 入库流量
            q_eco : float 生态需水流量
            supply_order_name : list 供水顺序名单
            user_name_list_from_reservoir : list 库内取水用户名单
            user_name_list_from_q_down : list 坝下取水用户名单
            q_user_demand_from_reservoir_df : pd.DataFrame 库内取水需求数据框
            q_user_demand_from_q_down_df : pd.DataFrame 坝下取水需求数据框
            # v_limited_supply_from_reservoir_day : float 库内取水日限制库容
            # v_limited_supply_from_q_down_day : float 坝下取水日限制库容
            v_limited_supply_day: float 供水限制库容
            q_supply_from_reservoir_df : pd.DataFrame 库内取水供水流量数据框
            q_supply_from_q_down_df : pd.DataFrame 坝下取水供水流量数据框
            q_lack_from_reservoir_df : pd.DataFrame 库内取水缺水流量数据框
            q_lack_from_q_down_df : pd.DataFrame 坝下取水缺水流量数据框
            lack_whether_from_reservoir_df : pd.DataFrame 库内取水缺水时段数据框
            lack_whether_from_q_down_df : pd.DataFrame 坝下取水缺水时段数据框
            if_const_z_down : bool 尾水位是否恒定
            const_z_down_val : float 尾水位恒定值
            v_begin : float 时段初库容
            x_line_list : list 调度线列表
            v_flood : float 防洪限制库容
            v_limited_power : float 发电限制库容
            v_dead_power : float 发电死库容
            v_dead : float 水库死库容

        Returns:
            包含计算结果的多返回值
        """

        # --- 入流计算 ---
        if if_q_up_eco_as_in:
            q_up_eco = 0
        q_loss_real = v_begin * loss_ratio / dt + loss_value / 8.64
        q_available = q_in - q_loss_real - q_up_eco  # 入库净流量（扣除损失流量、扣除上游生态）

        # --- 预留生态流量 ---
        q_available = q_available - q_eco

        # 供水预处理
        q_demands_from_reservoir = None
        q_demands_from_q_down = None
        if reservoir.supply_from_reservoir:
            q_demands_from_reservoir = q_user_demand_from_reservoir_df.loc[i_series].copy()
        if reservoir.supply_from_q_down:
            q_demands_from_q_down = q_user_demand_from_q_down_df.loc[i_series].copy()
        demands_current, v_limited_supply_current, if_from_q_down_current = self.get_demand_current(
            i_series=i_series,
            supply_order_name=supply_order_name,
            mmdd=mmdd,
            year_col=year_col,
            v_limited_supply=v_limited_supply_day,
            user_name_list_from_reservoir=user_name_list_from_reservoir,
            demands_from_reservoir=q_demands_from_reservoir,
            # v_limited_from_reservoir=v_limited_supply_from_reservoir_day,
            user_name_list_from_q_down=user_name_list_from_q_down,
            demands_from_q_down=q_demands_from_q_down,
            # v_limited_from_q_down=v_limited_supply_from_q_down_day
        )

        # 供水模块
        q_add_current = q_available  # 入库流量
        q_supply_from_reservoir = 0
        q_supply_from_q_down = 0
        for i_user in range(len(supply_order_name)):
            # # 计算
            tmp_q_demand = demands_current[i_user]
            tmp_v_limited = v_limited_supply_current[i_user]
            if_from_q_down = if_from_q_down_current[i_user]

            tmp_q = max(0, q_add_current + (v_begin - tmp_v_limited) / dt)  # 最大可供水量
            tmp_q_supply = min(tmp_q, tmp_q_demand)  # 实际供水量
            q_add_current -= tmp_q_supply
            # # 储存
            user_name = supply_order_name[i_user]
            if if_from_q_down != -1:
                if if_from_q_down:
                    q_supply_from_q_down += tmp_q_supply
                    q_supply_from_q_down_df.loc[i_series, str(user_name)] = tmp_q_supply
                    q_lack_from_q_down_df.loc[i_series, str(user_name)] = tmp_q_demand - tmp_q_supply
                    if tmp_q_demand - tmp_q_supply > 0:
                        lack_whether_from_q_down_df.loc[i_series, str(user_name)] = 1
                else:
                    q_supply_from_reservoir += tmp_q_supply
                    q_supply_from_reservoir_df.loc[i_series, str(user_name)] = tmp_q_supply
                    q_lack_from_reservoir_df.loc[i_series, str(user_name)] = tmp_q_demand - tmp_q_supply
                    if tmp_q_demand - tmp_q_supply > 0:
                        lack_whether_from_reservoir_df.loc[i_series, str(user_name)] = 1

        # 更新可用流量（已扣除供水）
        q_available = q_available - q_supply_from_reservoir + q_eco

        # --- 发电调度主逻辑 ---
        q_gen, q_thrown, v_end, z_up, z_down_val, dh, h_net, power = (
            self.operate_sub(
                const_z_down=const_z_down_val,
                reservoir=reservoir,
                v_initial=v_begin,
                q_in=q_available,
                n=1,
                x_line=x_line_list,
                dt=dt,
                v_flood=v_flood,
                v_dead_power=v_limited_power
            )
        )
        if_cal_power_again = False  # 出力计算已完成，默认不需要重新计算出力

        # 坝下供水部分可以用于发电
        q_down = q_gen + q_thrown
        if q_down < q_supply_from_q_down:  # 发电计算的下泄水量不满足坝下供水，需加大下泄
            q_down = q_supply_from_q_down  # 更新下泄水量（供水计算部分已得出q_supply_from_q_down为不发电情况下的可坝下供水量）

            # 下泄水量是否均能发电
            tmp_q_gen = min(max(0, q_available + (v_begin - v_dead_power) / dt), reservoir.qm)  # 可发电水量
            if tmp_q_gen < q_down:  # 可发电水量小于下泄水量，不可全发电
                q_gen = tmp_q_gen
            else:
                q_gen = q_supply_from_q_down

            q_thrown = q_supply_from_q_down - q_gen

            if_cal_power_again = True  # 需要重新计算出力

        # 生态流量兜底校核
        environment_supply = q_eco
        environment_lack = 0
        environment_lack_whether = 0
        if q_down < q_supply_from_q_down + q_eco:  # 生态下泄不足（生态流量在坝下供水量之外）
            tmp_q_down = max(0, q_available + (v_begin - v_dead) / dt)  # 可下泄水量
            tmp_q_gen = min(max(0, q_available + (v_begin - v_dead_power) / dt), reservoir.qm)  # 可发电水量

            # 下泄至死水位，是否可满足生态下泄
            if tmp_q_down < q_supply_from_q_down + q_eco:  # 不可满足
                environment_supply = tmp_q_down - q_supply_from_q_down
                environment_lack = q_eco - environment_supply
                environment_lack_whether = 1
                q_down = tmp_q_down
            else:
                q_down = q_supply_from_q_down + q_eco

            # 下泄流量是否均能发电
            if tmp_q_gen < q_down:  # 不可
                q_gen = tmp_q_gen
            else:
                q_gen = q_down

            q_thrown = q_down - q_gen

            if_cal_power_again = True  # 需要重新计算出力

        # 上库生态流量发电
        if q_up_eco > 0:
            q_down = q_up_eco + q_down
            q_gen = min(q_gen + q_up_eco, reservoir.qm)
            q_thrown = q_down - q_gen

            if_cal_power_again = True  # 需要重新计算出力

        # 是否需要重新计算出力
        if if_cal_power_again:  # 是
            # 时段末库容
            v_end = v_begin + (q_available - q_down) * dt

            # 出力计算
            z_up, z_down_val, dh, h_net, power = self.cal_power_sub_function(
                reservoir, v_begin, v_end, const_z_down_val, q_gen, q_thrown
            )

        return (q_loss_real,
                q_supply_from_reservoir_df, q_lack_from_reservoir_df, lack_whether_from_reservoir_df,
                q_supply_from_q_down_df, q_lack_from_q_down_df, lack_whether_from_q_down_df,
                environment_supply, environment_lack, environment_lack_whether,
                q_gen, q_thrown, v_end, z_up, z_down_val, dh, h_net, power
                )

    def power_operate_year_up_down(self, if_up_q_eco_as_in,
                                   up_res_name: str, down_res_name: str,
                                   up_v_special: list, down_v_special: list,
                                   need_add_user: list, user_special: list,
                                   user_stop_supply: list,
                                   max_count=2):
        """
        上、下游联合调度
        Args:
            up_res_name: 上游水库
            down_res_name: 下游水库
            up_v_special: list 湖南镇特征库容
            down_v_special: list 黄坛口特征库容
            user_special: list[list] 需重点保障用水户
            user_stop_supply: list 上库库容较低时停止供水的用水户
            max_count: int 最大迭代次数

        Returns:

        """
        # 防止传参错误
        up_reservoir = self.reservoirs.get(up_res_name, None)
        down_reservoir = self.reservoirs.get(down_res_name, None)
        if up_reservoir is None:
            wrong_info = f"传参错误：水库信息中不存在{up_res_name}"
            log_error(self.log_file, wrong_info)
            raise ValueError(wrong_info)
        if down_reservoir is None:
            wrong_info = f"传参错误：水库信息中不存在{down_res_name}"
            log_error(self.log_file, wrong_info)
            raise ValueError(wrong_info)
        if max_count <= 0:
            wrong_info = f"传参错误：最大迭代次数为0"
            log_error(self.log_file, wrong_info)
            raise ValueError(wrong_info)

        # 读取参数
        def read_params(reservoir):
            v_normal = reservoir.v_normal  # 正常库容
            v_dead = reservoir.v_dead  # 死库容

            if_const_z_down = reservoir.const_z_down  # 尾水位是否恒定

            wpv = reservoir.wpv  # 装机容量

            loss_ratio = reservoir.loss_ratio  # 损失水量比例
            loss_value = reservoir.loss_value  # 损失水量值
            supply_order = reservoir.supply_order  # 供水顺序

            return v_normal, v_dead, if_const_z_down, wpv, loss_ratio, loss_value, supply_order

        # # 上库
        (up_v_normal, up_v_dead, up_if_const_z_down,
         up_wpv, up_loss_ratio, up_loss_value, up_supply_order) = read_params(up_reservoir)
        # # 下库
        (down_v_normal, down_v_dead, down_if_const_z_down,
         down_wpv, down_loss_ratio, down_loss_value, down_supply_order) = read_params(down_reservoir)

        # 读取系列
        def read_arr(reservoir):
            operate_line_dict = reservoir.operate_line_dict  # 调度线 {"01-01":[[],[]], "02-01":[[],[]]}

            if reservoir.const_z_down:
                z_down_day = reservoir.z_down_day  # 尾水位恒定（系列）
            else:
                z_down_day = None

            v_flood_day = reservoir.v_flood_day  # 洪水限制库容（系列）
            v_limited_power_day = reservoir.v_limited_power_day  # 发电限制库容（系列）
            v_dead_power_day = reservoir.v_dead_power_day  # 发电死库容（系列）
            v_limited_supply_day = reservoir.v_limited_supply_day  # 供水限制库容（系列）

            q_in_arr = reservoir.arr_q_in + reservoir.arr_q_up  # 来水过程
            q_environment_arr = reservoir.arr_q_environment_demand  # 库下取水

            user_name_list_supply_from_reservoir = []
            num_user_supply_from_reservoir = 0
            # v_limited_supply_from_reservoir_day = None
            q_user_demand_from_reservoir_df = pd.DataFrame()
            if reservoir.supply_from_reservoir:
                user_name_list_supply_from_reservoir = reservoir.user_name_list_supply_from_reservoir
                num_user_supply_from_reservoir = len(user_name_list_supply_from_reservoir)
                # v_limited_supply_from_reservoir_day = reservoir.v_limited_supply_from_reservoir_day
                q_user_demand_from_reservoir_df = reservoir.q_user_demand_from_reservoir_df

            user_name_list_supply_from_down = []
            num_user_supply_from_q_down = 0
            # v_limited_supply_from_down_day = None
            q_user_demand_from_down_df = pd.DataFrame()
            if reservoir.supply_from_q_down:
                user_name_list_supply_from_down = reservoir.user_name_list_supply_from_down
                num_user_supply_from_q_down = len(user_name_list_supply_from_down)
                # v_limited_supply_from_down_day = reservoir.v_limited_supply_from_down_day
                q_user_demand_from_down_df = reservoir.q_user_demand_from_down_df

            return (operate_line_dict, z_down_day,
                    v_flood_day, v_limited_power_day, v_dead_power_day, v_limited_supply_day,
                    q_in_arr, q_environment_arr,
                    num_user_supply_from_reservoir,
                    user_name_list_supply_from_reservoir,
                    # v_limited_supply_from_reservoir_day,
                    q_user_demand_from_reservoir_df,
                    num_user_supply_from_q_down,
                    user_name_list_supply_from_down,
                    # v_limited_supply_from_down_day,
                    q_user_demand_from_down_df)

        # # 上库
        (up_operate_line_dict, up_z_down_day,
         up_v_flood_day, up_v_limited_power_day, up_v_dead_power_day, up_v_limited_supply_day,
         up_q_in_arr, up_q_environment_arr,
         up_num_user_supply_from_reservoir, up_user_name_list_supply_from_reservoir,
         # up_v_limited_supply_from_reservoir_day,
         up_q_user_demand_from_reservoir_df,
         up_num_user_supply_from_q_down, up_user_name_list_supply_from_q_down,
         # up_v_limited_supply_from_down_day,
         up_q_user_demand_from_down_df
         ) = read_arr(up_reservoir)
        # # 下库
        (down_operate_line_dict, down_z_down_day,
         down_v_flood_day, down_v_limited_power_day, down_v_dead_power_day, down_v_limited_supply_day,
         down_q_in_arr, down_q_environment_arr,
         down_num_user_supply_from_reservoir, down_user_name_list_supply_from_reservoir,
         # down_v_limited_supply_from_reservoir_day,
         down_q_user_demand_from_reservoir_df,
         down_num_user_supply_from_q_down, down_user_name_list_supply_from_q_down,
         # down_v_limited_supply_from_down_day,
         down_q_user_demand_from_down_df
         ) = read_arr(down_reservoir)

        # 提前处理日期信息
        date_process = self.date_process
        n_series = len(date_process)  # 序列长

        days_diff = (date_process[1:] - date_process[:-1]).days
        days_arr = np.concatenate([days_diff, [days_diff[-1]]])  # 天数

        mmdd_array = date_process.strftime('%m-%d')
        year_array = date_process.year
        is_leap_array = ((year_array % 4 == 0) & (year_array % 100 != 0)) | (year_array % 400 == 0)
        year_col_array = np.where(is_leap_array, 'leap_year', 'normal_year')

        # 初始库容设置
        up_v_start = up_reservoir.v_dead_power + 0.7 * (up_v_normal - up_reservoir.v_dead_power)
        down_v_start = down_reservoir.v_dead_power + 0.7 * (down_v_normal - down_reservoir.v_dead_power)

        # 读取系列2
        def read_arr2(reservoir):
            # --- 数组初始化 ---
            reservoir.refresh_sub_function_for_power_task(n_series)

            # 基础数组
            q_gen_arr = reservoir.q_gen_arr
            q_thrown_arr = reservoir.q_thrown_arr
            q_loss_real_arr = reservoir.q_loss_real_arr

            v_store_arr = reservoir.v_store_arr
            z_store_arr = reservoir.z_store_arr
            z_up_arr = reservoir.z_up_arr
            z_down_arr = reservoir.z_down_arr

            dh_loss_arr = reservoir.dh_loss_arr

            h_net_arr = reservoir.h_net_arr

            power_arr = reservoir.power_arr

            # 供水量、缺水量、缺水时段数
            # # 库内
            q_supply_from_reservoir_df = reservoir.q_supply_from_reservoir_df
            q_lack_from_reservoir_df = reservoir.q_lack_from_reservoir_df
            lack_whether_from_reservoir_df = reservoir.lack_whether_from_reservoir_df

            # # 坝下
            q_supply_from_q_down_df = reservoir.q_supply_from_q_down_df
            q_lack_from_q_down_df = reservoir.q_lack_from_q_down_df
            lack_whether_from_q_down_df = reservoir.lack_whether_from_q_down_df

            # # 生态
            environment_supply_arr = np.zeros(n_series)
            environment_lack_arr = np.zeros(n_series)
            environment_lack_whether_arr = np.zeros(n_series)

            # 补水后
            q_gen_arr_after_add = q_gen_arr.copy()
            q_thrown_arr_after_add = q_thrown_arr.copy()
            q_loss_real_arr_after_add = q_loss_real_arr.copy()

            v_store_arr_after_add = v_store_arr.copy()
            z_store_arr_after_add = z_store_arr.copy()
            z_up_arr_after_add = z_up_arr.copy()
            z_down_arr_after_add = z_down_arr.copy()

            dh_loss_arr_after_add = dh_loss_arr.copy()

            h_net_arr_after_add = h_net_arr.copy()

            power_arr_after_add = power_arr.copy()

            if q_supply_from_reservoir_df is not None:
                q_supply_from_reservoir_df_after_add = q_supply_from_reservoir_df.copy()
                q_lack_from_reservoir_df_after_add = q_lack_from_reservoir_df.copy()
                lack_whether_from_reservoir_df_after_add = lack_whether_from_reservoir_df.copy()
            else:
                q_supply_from_reservoir_df_after_add = pd.DataFrame()
                q_lack_from_reservoir_df_after_add = pd.DataFrame()
                lack_whether_from_reservoir_df_after_add = pd.DataFrame()

            if q_supply_from_q_down_df is not None:
                q_supply_from_q_down_df_after_add = q_supply_from_q_down_df.copy()
                q_lack_from_q_down_df_after_add = q_lack_from_q_down_df.copy()
                lack_whether_from_q_down_df_after_add = lack_whether_from_q_down_df.copy()
            else:
                q_supply_from_q_down_df_after_add = pd.DataFrame()
                q_lack_from_q_down_df_after_add = pd.DataFrame()
                lack_whether_from_q_down_df_after_add = pd.DataFrame()

            return (q_gen_arr, q_thrown_arr, q_loss_real_arr,
                    v_store_arr, z_store_arr, z_up_arr, z_down_arr,
                    dh_loss_arr, h_net_arr, power_arr,
                    q_supply_from_reservoir_df, q_lack_from_reservoir_df, lack_whether_from_reservoir_df,
                    q_supply_from_q_down_df, q_lack_from_q_down_df, lack_whether_from_q_down_df,
                    environment_supply_arr, environment_lack_arr, environment_lack_whether_arr,
                    q_gen_arr_after_add, q_thrown_arr_after_add, q_loss_real_arr_after_add,
                    v_store_arr_after_add, z_store_arr_after_add, z_up_arr_after_add, z_down_arr_after_add,
                    dh_loss_arr_after_add, h_net_arr_after_add, power_arr_after_add,
                    q_supply_from_reservoir_df_after_add, q_lack_from_reservoir_df_after_add,
                    lack_whether_from_reservoir_df_after_add,
                    q_supply_from_q_down_df_after_add, q_lack_from_q_down_df_after_add,
                    lack_whether_from_q_down_df_after_add)

        # 读取参数2：限制库容（防洪（储水上限）、主动发电下限、机组发电下限、库内供下限、坝下供下限）、恒定尾水位、发电调度线
        def read_params2(if_const_z_down, z_down_day, v_flood_day, v_dead_power_day, v_limited_power_day,
                         operate_line_dict, wpv, mmdd, year_col):
            # --- 恒定尾水位 ---
            if if_const_z_down:
                const_z_down_val = z_down_day.loc[current_mmdd][current_year_col]  # 尾水位
            else:
                const_z_down_val = -1

            # --- 限制库容 ---
            v_flood = v_flood_day.loc[mmdd][year_col]  # 防洪
            v_dead_power = v_dead_power_day.loc[mmdd][year_col]  # 发电死库容
            v_limited_power = v_limited_power_day.loc[mmdd][year_col]  # 发电限制库容

            # --- 获取当前调度线 ---
            x_line_list = operate_line_dict[mmdd][year_col]
            x_line_list[0].insert(0, v_flood)
            x_line_list[1].insert(0, wpv)
            x_line_list[0].append(v_limited_power)
            x_line_list[1].append(0)

            return (const_z_down_val, v_flood, v_dead_power, v_limited_power, x_line_list)

        # 补水后计算成果初始化：令补水后成果 等于 补水前成果
        def update_after_add(i_series, q_gen, q_thrown, v_store, z_up, z_down, dh_loss, h_net, power,
                             q_supply_from_reservoir_df, q_lack_from_reservoir_df, lack_whether_from_reservoir_df,
                             q_supply_from_q_down_df, q_lack_from_q_down_df, lack_whether_from_q_down_df,
                             q_supply_from_reservoir_df_after_add, q_lack_from_reservoir_df_after_add,
                             lack_whether_from_reservoir_df_after_add,
                             q_supply_from_q_down_df_after_add, q_lack_from_q_down_df_after_add,
                             lack_whether_from_q_down_df_after_add
                             ):
            q_gen_after_add = q_gen
            q_thrown_after_add = q_thrown

            v_store_after_add = v_store

            z_up_after_add = z_up
            z_down_after_add = z_down

            dh_loss_after_add = dh_loss

            h_net_after_add = h_net

            power_after_add = power

            # # 供水、缺水、缺水时段数
            # if q_supply_from_reservoir_df is not None:
            try:
                q_supply_from_reservoir_df_after_add.loc[i_series] = q_supply_from_reservoir_df.loc[i_series].copy()
                q_lack_from_reservoir_df_after_add.loc[i_series] = q_lack_from_reservoir_df.loc[i_series].copy()
                lack_whether_from_reservoir_df_after_add.loc[i_series] = lack_whether_from_reservoir_df.loc[i_series].copy()
            except KeyError:
                pass

            # if q_supply_from_q_down_df is not None:
            try:
                q_supply_from_q_down_df_after_add.loc[i_series] = q_supply_from_q_down_df.loc[i_series].copy()
                q_lack_from_q_down_df_after_add.loc[i_series] = q_lack_from_q_down_df.loc[i_series].copy()
                lack_whether_from_q_down_df_after_add.loc[i_series] = lack_whether_from_q_down_df.loc[i_series].copy()
            except KeyError:
                pass

            return (q_gen_after_add, q_thrown_after_add, v_store_after_add,
                    z_up_after_add, z_down_after_add, dh_loss_after_add, h_net_after_add, power_after_add,
                    q_supply_from_reservoir_df_after_add, q_lack_from_reservoir_df_after_add,
                    lack_whether_from_reservoir_df_after_add,
                    q_supply_from_q_down_df_after_add, q_lack_from_q_down_df_after_add,
                    lack_whether_from_q_down_df_after_add)

        for i_count in range(max_count):
            # --- 数组初始化 ---
            # # 上库
            (up_q_gen_arr, up_q_thrown_arr, up_q_loss_real_arr,
             up_v_store_arr, up_z_store_arr, up_z_up_arr, up_z_down_arr,
             up_dh_loss_arr, up_h_net_arr, up_power_arr,
             up_q_supply_from_reservoir_df, up_q_lack_from_reservoir_df, up_lack_whether_from_reservoir_df,
             up_q_supply_from_q_down_df, up_q_lack_from_q_down_df, up_lack_whether_from_q_down_df,
             up_environment_supply_arr, up_environment_lack_arr, up_environment_lack_whether_arr,
             up_q_gen_arr_after_add, up_q_thrown_arr_after_add, up_q_loss_real_arr_after_add,
             up_v_store_arr_after_add, up_z_store_arr_after_add, up_z_up_arr_after_add,
             up_z_down_arr_after_add, up_dh_loss_arr_after_add, up_h_net_arr_after_add,
             up_power_arr_after_add,
             up_q_supply_from_reservoir_df_after_add, up_q_lack_from_reservoir_df_after_add,
             up_lack_whether_from_reservoir_df_after_add,
             up_q_supply_from_q_down_df_after_add, up_q_lack_from_q_down_df_after_add,
             up_lack_whether_from_q_down_df_after_add
             ) = read_arr2(up_reservoir)
            # # 下库
            (down_q_gen_arr, down_q_thrown_arr, down_q_loss_real_arr,
             down_v_store_arr, down_z_store_arr, down_z_up_arr, down_z_down_arr,
             down_dh_loss_arr, down_h_net_arr, down_power_arr,
             down_q_supply_from_reservoir_df, down_q_lack_from_reservoir_df, down_lack_whether_from_reservoir_df,
             down_q_supply_from_q_down_df, down_q_lack_from_q_down_df, down_lack_whether_from_q_down_df,
             down_environment_supply_arr, down_environment_lack_arr, down_environment_lack_whether_arr,
             down_q_gen_arr_after_add, down_q_thrown_arr_after_add, down_q_loss_real_arr_after_add,
             down_v_store_arr_after_add, down_z_store_arr_after_add, down_z_up_arr_after_add,
             down_z_down_arr_after_add, down_dh_loss_arr_after_add, down_h_net_arr_after_add,
             down_power_arr_after_add,
             down_q_supply_from_reservoir_df_after_add, down_q_lack_from_reservoir_df_after_add,
             down_lack_whether_from_reservoir_df_after_add,
             down_q_supply_from_q_down_df_after_add, down_q_lack_from_q_down_df_after_add,
             down_lack_whether_from_q_down_df_after_add
             ) = read_arr2(down_reservoir)
            # # 补水量
            real_add_q_arr = np.zeros(n_series)
            real_add_q2_arr = np.zeros(n_series)
            real_add_q3_arr = np.zeros(n_series)

            # 当前时段初库容
            up_v_begin = up_v_start
            down_v_begin = down_v_start

            # --- 逐时段计算 ---
            for i in range(n_series):  # 逐时刻
                current_year_col = year_col_array[i]
                current_mmdd = mmdd_array[i]

                # --- 时间步长换算系数 ---
                dt = float(days_arr[i] * 8.64)

                # --- 恒定尾水位 ---
                # --- 限制库容 ---
                # # 上库
                (up_const_z_down_val, up_v_flood, up_v_dead_power,
                 up_v_limited_power, up_x_line_list) = read_params2(
                    if_const_z_down=up_if_const_z_down,
                    z_down_day=up_z_down_day,
                    v_flood_day=up_v_flood_day,
                    v_dead_power_day=up_v_dead_power_day,
                    v_limited_power_day=up_v_limited_power_day,
                    operate_line_dict=up_operate_line_dict,
                    wpv=up_wpv,
                    mmdd=current_mmdd,
                    year_col=current_year_col
                )
                # # 下库
                (down_const_z_down_val, down_v_flood, down_v_dead_power,
                 down_v_limited_power, down_x_line_list) = read_params2(
                    if_const_z_down=down_if_const_z_down,
                    z_down_day=down_z_down_day,
                    v_flood_day=down_v_flood_day,
                    v_dead_power_day=down_v_dead_power_day,
                    v_limited_power_day=down_v_limited_power_day,
                    operate_line_dict=down_operate_line_dict,
                    wpv=down_wpv,
                    mmdd=current_mmdd,
                    year_col=current_year_col
                )

                # --- 计算供水和发电 ---
                # # 上库
                # # # 入库
                up_q_in = up_q_in_arr[i]
                up_q_eco = up_q_environment_arr[i]
                # # # 计算
                (up_q_loss_real_arr[i],
                 up_q_supply_from_reservoir_df, up_q_lack_from_reservoir_df, up_lack_whether_from_reservoir_df,
                 up_q_supply_from_q_down_df, up_q_lack_from_q_down_df, up_lack_whether_from_q_down_df,
                 up_environment_supply_arr[i], up_environment_lack_arr[i], up_environment_lack_whether_arr[i],
                 up_q_gen, up_q_thrown, up_v_end, up_z_up, up_z_down_val, up_dh, up_h_net, up_power
                 ) = self.cal_supply_and_eletricity(
                    i_series=i,
                    reservoir=up_reservoir,
                    mmdd=current_mmdd,
                    year_col=current_year_col,
                    dt=dt,
                    loss_ratio=up_loss_ratio,
                    loss_value=up_loss_value,
                    q_in=up_q_in,
                    q_eco=up_q_eco,
                    if_q_up_eco_as_in=if_up_q_eco_as_in,  # 控制上库生态流量是否参与供水计算
                    q_up_eco=0,
                    supply_order_name=up_supply_order,
                    user_name_list_from_reservoir=up_user_name_list_supply_from_reservoir,
                    user_name_list_from_q_down=up_user_name_list_supply_from_q_down,
                    q_user_demand_from_reservoir_df=up_q_user_demand_from_reservoir_df,
                    q_user_demand_from_q_down_df=up_q_user_demand_from_down_df,
                    v_limited_supply_day=up_v_limited_supply_day,
                    # v_limited_supply_from_reservoir_day=up_v_limited_supply_from_reservoir_day,
                    # v_limited_supply_from_q_down_day=up_v_limited_supply_from_down_day,
                    q_supply_from_reservoir_df=up_q_supply_from_reservoir_df,
                    q_supply_from_q_down_df=up_q_supply_from_q_down_df,
                    q_lack_from_reservoir_df=up_q_lack_from_reservoir_df,
                    q_lack_from_q_down_df=up_q_lack_from_q_down_df,
                    lack_whether_from_reservoir_df=up_lack_whether_from_reservoir_df,
                    lack_whether_from_q_down_df=up_lack_whether_from_q_down_df,
                    if_const_z_down=up_if_const_z_down,
                    const_z_down_val=up_const_z_down_val,
                    v_begin=up_v_begin,
                    x_line_list=up_x_line_list,
                    v_flood=up_v_flood,
                    v_limited_power=up_v_limited_power,
                    v_dead_power=up_v_dead_power,
                    v_dead=up_v_dead
                )

                # # 下库
                # # # 入库
                down_q_in = down_q_in_arr[i] + up_q_gen + up_q_thrown
                down_q_eco = down_q_environment_arr[i]
                # # # 计算
                (down_q_loss_real_arr[i],
                 down_q_supply_from_reservoir_df, down_q_lack_from_reservoir_df, down_lack_whether_from_reservoir_df,
                 down_q_supply_from_q_down_df, down_q_lack_from_q_down_df, down_lack_whether_from_q_down_df,
                 down_environment_supply_arr[i], down_environment_lack_arr[i], down_environment_lack_whether_arr[i],
                 down_q_gen, down_q_thrown, down_v_end, down_z_up, down_z_down_val, down_dh, down_h_net, down_power
                 ) = self.cal_supply_and_eletricity(
                    i_series=i,
                    reservoir=down_reservoir,
                    mmdd=current_mmdd,
                    year_col=current_year_col,
                    dt=dt,
                    loss_ratio=down_loss_ratio,
                    loss_value=down_loss_value,
                    q_in=down_q_in,
                    q_eco=down_q_eco,
                    if_q_up_eco_as_in=if_up_q_eco_as_in,  # 控制上库生态流量是否参与供水计算
                    q_up_eco=up_environment_supply_arr[i],
                    supply_order_name=down_supply_order,
                    user_name_list_from_reservoir=down_user_name_list_supply_from_reservoir,
                    user_name_list_from_q_down=down_user_name_list_supply_from_q_down,
                    q_user_demand_from_reservoir_df=down_q_user_demand_from_reservoir_df,
                    q_user_demand_from_q_down_df=down_q_user_demand_from_down_df,
                    v_limited_supply_day=down_v_limited_supply_day,
                    # v_limited_supply_from_reservoir_day=down_v_limited_supply_from_reservoir_day,
                    # v_limited_supply_from_q_down_day=down_v_limited_supply_from_down_day,
                    q_supply_from_reservoir_df=down_q_supply_from_reservoir_df,
                    q_supply_from_q_down_df=down_q_supply_from_q_down_df,
                    q_lack_from_reservoir_df=down_q_lack_from_reservoir_df,
                    q_lack_from_q_down_df=down_q_lack_from_q_down_df,
                    lack_whether_from_reservoir_df=down_lack_whether_from_reservoir_df,
                    lack_whether_from_q_down_df=down_lack_whether_from_q_down_df,
                    if_const_z_down=down_if_const_z_down,
                    const_z_down_val=down_const_z_down_val,
                    v_begin=down_v_begin,
                    x_line_list=down_x_line_list,
                    v_flood=down_v_flood,
                    v_limited_power=down_v_limited_power,
                    v_dead_power=down_v_dead_power,
                    v_dead=down_v_dead
                )

                # 上库给下库补水
                # # 补水相关数据初始化
                # real_add_q = 0  # 补水量初始化
                real_add_q1 = 0  # 补黄坛口
                real_add_q2 = 0  # 补缺口
                real_add_q3 = 0  # 补衢州生活工业缺口
                need_cal_power_again = False  # 是否需要重新计算发电，默认为否
                # # # 上库
                (up_q_gen_after_add, up_q_thrown_after_add, up_v_end_after_add,
                 up_z_up_after_add, up_z_down_val_after_add, up_dh_after_add, up_h_net_after_add, up_power_after_add,
                 up_q_supply_from_reservoir_df_after_add, up_q_lack_from_reservoir_df_after_add,
                 up_lack_whether_from_reservoir_df_after_add,
                 up_q_supply_from_q_down_df_after_add, up_q_lack_from_q_down_df_after_add,
                 up_lack_whether_from_q_down_df_after_add) = update_after_add(
                    i, up_q_gen, up_q_thrown,
                    up_v_end, up_z_up, up_z_down_val,
                    up_dh, up_h_net, up_power,
                    up_q_supply_from_reservoir_df, up_q_lack_from_reservoir_df, up_lack_whether_from_reservoir_df,
                    up_q_supply_from_q_down_df, up_q_lack_from_q_down_df, up_lack_whether_from_q_down_df,
                    up_q_supply_from_reservoir_df_after_add, up_q_lack_from_reservoir_df_after_add,
                    up_lack_whether_from_reservoir_df_after_add,
                    up_q_supply_from_q_down_df_after_add, up_q_lack_from_q_down_df_after_add,
                    up_lack_whether_from_q_down_df_after_add
                )
                # # # 下库
                (down_q_gen_after_add, down_q_thrown_after_add, down_v_end_after_add,
                 down_z_up_after_add, down_z_down_val_after_add, down_dh_after_add, down_h_net_after_add, down_power_after_add,
                 down_q_supply_from_reservoir_df_after_add, down_q_lack_from_reservoir_df_after_add,
                 down_lack_whether_from_reservoir_df_after_add,
                 down_q_supply_from_q_down_df_after_add, down_q_lack_from_q_down_df_after_add,
                 down_lack_whether_from_q_down_df_after_add) = update_after_add(
                    i, down_q_gen, down_q_thrown,
                    down_v_end, down_z_up, down_z_down_val,
                    down_dh, down_h_net, down_power,
                    down_q_supply_from_reservoir_df, down_q_lack_from_reservoir_df, down_lack_whether_from_reservoir_df,
                    down_q_supply_from_q_down_df, down_q_lack_from_q_down_df, down_lack_whether_from_q_down_df,
                    down_q_supply_from_reservoir_df_after_add, down_q_lack_from_reservoir_df_after_add,
                    down_lack_whether_from_reservoir_df_after_add,
                    down_q_supply_from_q_down_df_after_add, down_q_lack_from_q_down_df_after_add,
                    down_lack_whether_from_q_down_df_after_add
                )

                # # 补水相关计算
                if up_v_end > up_v_special[0]:  # 大于198m时，按发电调度，不进行额外处理
                    pass
                elif up_v_end >= up_v_special[1]:  # 196~198m时，向下库补水
                    max_add_q = max(0, (up_v_end - up_v_special[1]) / dt)  # 最大可补水量

                    # 需补水量1：补水至下库满足111.73
                    need_add_q1 = max(0, (down_v_special[0] - down_v_end) / dt)

                    # # 需补水量2：需补缺口
                    # tmp_add_q1 = 0
                    # tmp_add_q2 = 0
                    # if down_num_user_supply_from_reservoir > 0:
                    #     tmp_add_q1 = down_q_lack_from_reservoir_df.iloc[i].sum()
                    # if down_num_user_supply_from_q_down > 0:
                    #     tmp_add_q2 = down_q_lack_from_q_down_df.iloc[i].sum()
                    # need_add_q2 = (tmp_add_q1 + tmp_add_q2)
                    #
                    # if need_add_q2 > 0:
                    #     print(current_mmdd, need_add_q2, )
                    #     input()
                    #
                    # need_add_q = need_add_q1 + need_add_q2

                    # 实际补水量
                    # real_add_q = min(need_add_q, max_add_q)

                    # # 更新供水、缺口
                    # if real_add_q > need_add_q2:
                    #     real_add_q2 = need_add_q2
                    #     if down_num_user_supply_from_reservoir > 0:
                    #         down_q_supply_from_reservoir_df_after_add.iloc[i] = (
                    #             down_q_user_demand_from_reservoir_df.iloc[i].copy()
                    #         )
                    #         down_q_lack_from_reservoir_df_after_add.iloc[i] = (
                    #             np.zeros(down_num_user_supply_from_reservoir)
                    #         )
                    #         down_lack_whether_from_reservoir_df_after_add.iloc[i] = (
                    #             np.zeros(down_num_user_supply_from_reservoir)
                    #         )
                    #     if down_num_user_supply_from_q_down > 0:
                    #         down_q_supply_from_q_down_df_after_add.iloc[i] = (
                    #             down_q_user_demand_from_down_df.iloc[i].copy()
                    #         )
                    #         down_q_lack_from_q_down_df_after_add.iloc[i] = (
                    #             np.zeros(down_num_user_supply_from_q_down)
                    #         )
                    #         down_lack_whether_from_q_down_df_after_add.iloc[i] = (
                    #             np.zeros(down_num_user_supply_from_q_down)
                    #         )
                    #
                    # else:
                    #     tmp_add_q = real_add_q
                    #     for tmp_user_name in need_add_user:
                    #         try:
                    #             tmp_lack = down_q_lack_from_reservoir_df.loc[i, str(tmp_user_name)]  # 需补
                    #             tmp_add_supply = min(tmp_lack, tmp_add_q)  # 可补
                    #             # 更新供水
                    #             down_q_supply_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] += tmp_add_supply
                    #             # 更新缺口
                    #             down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] -= tmp_add_supply
                    #             # 更新缺水时段判断
                    #             if down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] <= 0:
                    #                 down_lack_whether_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] = 0
                    #
                    #         except KeyError:
                    #             tmp_lack = down_q_lack_from_q_down_df.loc[i, str(tmp_user_name)]  # 需补
                    #             tmp_add_supply = min(tmp_lack, tmp_add_q)  # 可补
                    #             # 更新供水
                    #             down_q_supply_from_q_down_df_after_add.loc[i, str(tmp_user_name)] += tmp_add_supply
                    #             # 更新缺口
                    #             down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] -= tmp_add_supply
                    #             # 更新缺水时段判断
                    #             if down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] <= 0:
                    #                 down_lack_whether_from_q_down_df_after_add.loc[i, str(tmp_user_name)] = 0
                    #
                    #         tmp_add_q -= tmp_add_supply  # 剩余
                    #         real_add_q2 += tmp_add_supply
                    #
                    #         if tmp_add_q <= 0:
                    #             break

                    # real_add_q1 = real_add_q - real_add_q2

                    # 需补水量2：补缺口 20251021修改
                    real_add_q2 = 0
                    tmp_add_q = max_add_q  # 剩余
                    for tmp_user_name in need_add_user:
                        try:
                            tmp_lack = down_q_lack_from_reservoir_df.loc[i, str(tmp_user_name)]  # 需补
                            tmp_add_supply = min(tmp_lack, tmp_add_q)  # 可补
                            # 更新供水
                            down_q_supply_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] += tmp_add_supply
                            # 更新缺口
                            down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] -= tmp_add_supply
                            # 更新缺水时段判断
                            if down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] <= 0:
                                down_lack_whether_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] = 0

                        except KeyError:
                            tmp_lack = down_q_lack_from_q_down_df.loc[i, str(tmp_user_name)]  # 需补
                            tmp_add_supply = min(tmp_lack, tmp_add_q)  # 可补
                            # 更新供水
                            down_q_supply_from_q_down_df_after_add.loc[i, str(tmp_user_name)] += tmp_add_supply
                            # 更新缺口
                            down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] -= tmp_add_supply
                            # 更新缺水时段判断
                            if down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] <= 0:
                                down_lack_whether_from_q_down_df_after_add.loc[i, str(tmp_user_name)] = 0

                        tmp_add_q -= tmp_add_supply  # 剩余
                        real_add_q2 += tmp_add_supply

                        if tmp_add_q <= 0:
                            break

                    real_add_q1 = min(need_add_q1, tmp_add_q)
                    real_add_q = real_add_q1 + real_add_q2

                    # 更新末库容
                    down_v_end_after_add += max(0, real_add_q1) * dt
                    up_v_end_after_add -= real_add_q * dt

                    # 进行了补水，需更新发电计算
                    if real_add_q > 0:
                        need_cal_power_again = True

                if up_v_end_after_add <= up_v_special[1]:  # 196m以下至死库容，补足衢州生活缺口，最多额外补7.52
                    tmp_down_v_end = down_v_end_after_add
                    tmp_up_v_end = up_v_end_after_add

                    for tmp_user_info in user_special:
                        tmp_user_name = tmp_user_info[0]
                        tmp_user_need = float(tmp_user_info[1])

                        max_add_q = max(0, (tmp_up_v_end - up_v_dead) / dt)  # 最大可补水量

                        # # 当前供水量
                        try:
                            origin_supply = down_q_supply_from_reservoir_df_after_add.loc[i, str(tmp_user_name)]
                            origin_lack = down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)]
                        except KeyError:
                            origin_supply = down_q_supply_from_q_down_df_after_add.loc[i, str(tmp_user_name)]
                            origin_lack = down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)]

                        # # 需补量
                        # need_add_q3 = max(0, tmp_user_need - origin_supply)
                        need_add_q3 = min(tmp_user_need, origin_lack)

                        # # 实际补水量
                        real_add_q3 = min(need_add_q3, max_add_q)

                        # # 更新供水、缺口信息
                        try:
                            down_q_supply_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] += real_add_q3
                            # down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] = (
                            #         need_add_q3 - real_add_q3
                            # )
                            down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] -= real_add_q3
                            # 更新缺水时段判断
                            if down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] <= 0:
                                down_lack_whether_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] = 0
                        except KeyError:
                            down_q_supply_from_q_down_df_after_add.loc[i, str(tmp_user_name)] += real_add_q3
                            # down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] = (
                            #         need_add_q3 - real_add_q3
                            # )
                            down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] -= real_add_q3
                            # 更新缺水时段判断
                            if down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] <= 0:
                                down_lack_whether_from_q_down_df_after_add.loc[i, str(tmp_user_name)] = 0

                        # # 更新末库容
                        tmp_up_v_end -= real_add_q3 * dt

                        # 进行了补水需更新发电计算
                        if real_add_q3 > 0:
                            need_cal_power_again = True

                    # 20251029调整 上库水位较低时，下库减少特定用水户的供水
                    for tmp_user_name in user_stop_supply:
                        if tmp_user_name not in down_supply_order:
                            continue
                        # # 当前供水量
                        try:
                            origin_supply = down_q_supply_from_reservoir_df_after_add.loc[i, str(tmp_user_name)]
                            origin_lack = down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)]
                        except KeyError:
                            origin_supply = down_q_supply_from_q_down_df_after_add.loc[i, str(tmp_user_name)]
                            origin_lack = down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)]

                        if origin_supply != origin_supply:
                            print("NaN")
                            input()

                        # # 更新供水、缺口信息
                        if origin_supply > 0:
                            try:
                                # # 注意！！！由于此处别直接采用等于，因为，等于代表赋值，即使不存在也会被新增列，采用"-="或"+="比较好
                                down_q_supply_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] -= origin_supply
                                down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] += origin_supply
                                # 更新缺水时段判断
                                if down_q_lack_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] > 0:
                                    down_lack_whether_from_reservoir_df_after_add.loc[i, str(tmp_user_name)] = 1

                            except KeyError:
                                # # 注意！！！由于此处别直接采用等于，因为，等于代表赋值，即使不存在也会被新增列，采用"-="或"+="比较好
                                down_q_supply_from_q_down_df_after_add.loc[i, str(tmp_user_name)] -= origin_supply
                                down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] += origin_supply
                                # 更新缺水时段判断
                                if down_q_lack_from_q_down_df_after_add.loc[i, str(tmp_user_name)] > 0:
                                    down_lack_whether_from_q_down_df_after_add.loc[i, str(tmp_user_name)] = 1

                            # # 更新末库容
                            tmp_down_v_end += origin_supply * dt

                            # 需重新计算发电
                            need_cal_power_again = True

                    down_v_end_after_add = tmp_down_v_end
                    up_v_end_after_add = tmp_up_v_end

                # # 补水后发电调整
                # if real_add_q1 + real_add_q2 + real_add_q3 > 0:
                # 20251029 调整
                if need_cal_power_again:
                    # # # 上库
                    tmp_add_q = real_add_q1 + real_add_q2 + real_add_q3

                    tmp_qm = up_reservoir.qm
                    tmp_q_gen = up_q_gen
                    tmp_q_thrown = up_q_thrown

                    tmp_v_end = up_v_end
                    tmp_v_dead = up_v_dead_power

                    tmp_add_q_gen = min(tmp_add_q, tmp_qm - tmp_q_gen)  # 低于机组发电流量部分
                    tmp_add_max_q_gen = max(0, (tmp_v_end - tmp_v_dead) / dt)  # 可发电部分水量
                    add_q_gen = min(tmp_add_q_gen, tmp_add_max_q_gen)  # 补水部分可发电

                    up_q_gen_after_add = max(0, add_q_gen + tmp_q_gen)
                    up_q_thrown_after_add = tmp_add_q + tmp_q_gen + tmp_q_thrown - up_q_gen_after_add

                    (up_z_up_after_add, up_z_down_val_after_add, up_dh_after_add, up_h_net_after_add,
                     up_power_after_add) = self.cal_power_sub_function(
                        up_reservoir, up_v_begin, up_v_end_after_add, up_const_z_down_val,
                        up_q_gen_after_add, up_q_thrown_after_add
                    )

                    # # # 下库
                    tmp_add_q = 0
                    for user_name in down_user_name_list_supply_from_q_down:
                        tmp_add_q += (down_q_supply_from_q_down_df_after_add.loc[i, str(user_name)] -
                                      down_q_supply_from_q_down_df.loc[i, str(user_name)])

                    tmp_qm = down_reservoir.qm
                    tmp_q_gen = down_q_gen
                    tmp_q_thrown = down_q_thrown

                    tmp_v_end = down_v_end
                    tmp_v_dead = down_v_dead_power

                    tmp_add_q_gen = min(tmp_add_q, tmp_qm - tmp_q_gen)  # 低于机组发电流量部分
                    tmp_add_max_q_gen = max(0, (tmp_v_end - tmp_v_dead) / dt)  # 可发电部分水量
                    add_q_gen = min(tmp_add_q_gen, tmp_add_max_q_gen)  # 补水部分可发电

                    down_q_gen_after_add = max(0, add_q_gen + tmp_q_gen)
                    down_q_thrown_after_add = tmp_add_q + tmp_q_gen + tmp_q_thrown - down_q_gen_after_add

                    (down_z_up_after_add, down_z_down_val_after_add, down_dh_after_add, down_h_net_after_add,
                     down_power_after_add) = self.cal_power_sub_function(
                        down_reservoir, down_v_begin, down_v_end_after_add, down_const_z_down_val,
                        down_q_gen_after_add, down_q_thrown_after_add
                    )

                # --- 存储结果 ---
                # # 上库
                up_q_gen_arr[i] = up_q_gen
                up_q_thrown_arr[i] = up_q_thrown
                up_v_store_arr[i] = up_v_end
                up_z_up_arr[i] = up_z_up
                up_z_down_arr[i] = up_z_down_val
                up_dh_loss_arr[i] = up_dh
                up_h_net_arr[i] = up_h_net
                up_power_arr[i] = up_power
                up_z_store_arr[i] = np.interp(up_v_end, up_reservoir.zv['volume'], up_reservoir.zv['waterLevel'])

                up_q_gen_arr_after_add[i] = up_q_gen_after_add
                up_q_thrown_arr_after_add[i] = up_q_thrown_after_add
                up_v_store_arr_after_add[i] = up_v_end_after_add
                up_z_up_arr_after_add[i] = up_z_up_after_add
                up_z_down_arr_after_add[i] = up_z_down_val_after_add
                up_dh_loss_arr_after_add[i] = up_dh_after_add
                up_h_net_arr_after_add[i] = up_h_net_after_add
                up_power_arr_after_add[i] = up_power_after_add
                up_z_store_arr_after_add[i] = np.interp(up_v_end_after_add,
                                                        up_reservoir.zv['volume'], up_reservoir.zv['waterLevel'])
                # # 下库
                down_q_gen_arr[i] = down_q_gen
                down_q_thrown_arr[i] = down_q_thrown
                down_v_store_arr[i] = down_v_end
                down_z_up_arr[i] = down_z_up
                down_z_down_arr[i] = down_z_down_val
                down_dh_loss_arr[i] = down_dh
                down_h_net_arr[i] = down_h_net
                down_power_arr[i] = down_power
                down_z_store_arr[i] = np.interp(down_v_end, down_reservoir.zv['volume'], down_reservoir.zv['waterLevel'])

                down_q_gen_arr_after_add[i] = down_q_gen_after_add
                down_q_thrown_arr_after_add[i] = down_q_thrown_after_add
                down_v_store_arr_after_add[i] = down_v_end_after_add
                down_z_up_arr_after_add[i] = down_z_up_after_add
                down_z_down_arr_after_add[i] = down_z_down_val_after_add
                down_dh_loss_arr_after_add[i] = down_dh_after_add
                down_h_net_arr_after_add[i] = down_h_net_after_add
                down_power_arr_after_add[i] = down_power_after_add
                down_z_store_arr_after_add[i] = np.interp(down_v_end_after_add,
                                                          down_reservoir.zv['volume'], down_reservoir.zv['waterLevel'])

                # # 补水
                real_add_q_arr[i] = real_add_q1
                real_add_q2_arr[i] = real_add_q2
                real_add_q3_arr[i] = real_add_q3

                # --- 为下一时段准备 ---
                up_v_begin = up_v_end_after_add
                down_v_begin = down_v_end_after_add

            # 判断是否需要再算一遍，满足计算时段内起始库容和结束库容一致
            if abs(up_v_start - up_v_end) >= self.epsilon_v:
                print(f'第{i_count}轮：{up_v_start} - {up_v_end} = {up_v_start - up_v_end} ')
                up_v_start = up_v_end
                down_v_start = down_v_end
            else:  # 始末库容均一致，无需开启二次计算
                print(f'第{i_count}轮：{up_v_start} - {up_v_end} = {up_v_start - up_v_end} ')
                print(f"迭代次数：{i_count}")

        # 储存
        def create_process_table(date, supply_order,
                                 q_up_eco,
                                 q_in_arr, q_gen_arr, q_thrown_arr, v_store_arr, h_net_arr, power_arr,
                                 q_environment_arr,
                                 environment_supply_arr,
                                 environment_lack_arr,
                                 environment_lack_whether_arr,
                                 q_loss_real_arr,
                                 z_up_arr, z_down_arr, dh_loss_arr, days_arr, z_store_arr,
                                 real_add_q_arr, real_add_q3_arr,
                                 q_user_demand_from_reservoir_df, q_user_demand_from_down_df,
                                 q_supply_from_reservoir_df, q_supply_from_q_down_df,
                                 q_lack_from_reservoir_df, q_lack_from_q_down_df,
                                 lack_whether_from_reservoir_df, lack_whether_from_q_down_df,

                                 q_gen_arr_after_add, q_thrown_arr_after_add, v_store_arr_after_add,
                                 h_net_arr_after_add, power_arr_after_add,
                                 z_up_arr_after_add, z_down_arr_after_add, dh_loss_arr_after_add,
                                 z_store_arr_after_add,
                                 q_supply_from_reservoir_df_after_add, q_supply_from_q_down_df_after_add,
                                 q_lack_from_reservoir_df_after_add, q_lack_from_q_down_df_after_add,
                                 lack_whether_from_reservoir_df_after_add, lack_whether_from_q_down_df_after_add,
                                 user_special):

            process_table = {}

            # 基本数据
            process_table['日期'] = date
            process_table['来水流量（包含上库生态流量）'] = q_in_arr
            process_table['上库生态流量下泄'] = q_up_eco
            process_table['发电流量'] = q_gen_arr
            process_table['弃水流量'] = q_thrown_arr
            process_table['时段末库容'] = v_store_arr
            process_table['水头'] = h_net_arr
            process_table['出力（kW）'] = power_arr

            # 需水流量
            for user_name in supply_order:
                try:
                    process_table[user_name + '_需水流量'] = q_user_demand_from_reservoir_df[user_name]
                except KeyError:
                    process_table[user_name + '_需水流量'] = q_user_demand_from_down_df[user_name]
                # except TypeError:
                #     process_table[user_name + '_需水流量'] = q_user_demand_from_down_df[user_name]
            process_table['生态下泄要求'] = q_environment_arr

            # 实际供水流量
            for user_name in supply_order:
                try:
                    process_table[user_name + '_实际供水流量'] = q_supply_from_reservoir_df[user_name]
                except KeyError:
                    process_table[user_name + '_实际供水流量'] = q_supply_from_q_down_df[user_name]
                # except TypeError:
                #     process_table[user_name + '_实际供水流量'] = q_supply_from_q_down_df[user_name]
            process_table['生态实际下泄'] = environment_supply_arr

            # 缺水流量
            for user_name in supply_order:
                try:
                    process_table[user_name + '_缺水流量'] = q_lack_from_reservoir_df[user_name]
                except KeyError:
                    process_table[user_name + '_缺水流量'] = q_lack_from_q_down_df[user_name]
                # except TypeError:
                #     process_table[user_name + '_缺水流量'] = q_lack_from_q_down_df[user_name]
            process_table['生态缺口'] = environment_lack_arr

            # 缺水时段
            for user_name in supply_order:
                try:
                    process_table[user_name + '_缺水时段'] = lack_whether_from_reservoir_df[user_name]
                except KeyError:
                    process_table[user_name + '_缺水时段'] = lack_whether_from_q_down_df[user_name]
                # except TypeError:
                #     process_table[user_name + '_缺水时段'] = lack_whether_from_q_down_df[user_name]
            process_table['生态缺水天数'] = environment_lack_whether_arr

            # 其他数据
            process_table['蒸发、渗漏损失流量'] = q_loss_real_arr
            process_table['Z1'] = z_up_arr
            process_table['Z2'] = z_down_arr
            process_table['DH'] = dh_loss_arr
            process_table['时段天数'] = days_arr
            process_table['时段末水位'] = z_store_arr

            process_table['向黄坛口补水'] = real_add_q_arr
            process_table['补黄坛口供水缺口'] = real_add_q2_arr
            if user_special != []:
                process_table['补' + str(user_special[-1][0])] = real_add_q3_arr

            process_table['补水后-发电流量'] = q_gen_arr_after_add
            process_table['补水后-弃水流量'] = q_thrown_arr_after_add
            process_table['补水后-时段末库容'] = v_store_arr_after_add
            process_table['补水后-水头'] = h_net_arr_after_add
            process_table['补水后-出力（kW）'] = power_arr_after_add

            # 实际供水流量
            for user_name in supply_order:
                try:
                    process_table['补水后-' + user_name + '_实际供水流量'] = q_supply_from_reservoir_df_after_add[user_name]
                except KeyError:
                    process_table['补水后-' + user_name + '_实际供水流量'] = q_supply_from_q_down_df_after_add[user_name]
                except TypeError:
                    process_table['补水后-' + user_name + '_实际供水流量'] = q_supply_from_q_down_df_after_add[user_name]

            # 缺水流量
            for user_name in supply_order:
                try:
                    process_table['补水后-' + user_name + '_缺水流量'] = q_lack_from_reservoir_df_after_add[user_name]
                except KeyError:
                    process_table['补水后-' + user_name + '_缺水流量'] = q_lack_from_q_down_df_after_add[user_name]
                except TypeError:
                    process_table['补水后-' + user_name + '_缺水流量'] = q_lack_from_q_down_df_after_add[user_name]

            # 缺水时段
            for user_name in supply_order:
                try:
                    process_table['补水后-' + user_name + '_缺水时段'] = lack_whether_from_reservoir_df_after_add[user_name]
                except KeyError:
                    process_table['补水后-' + user_name + '_缺水时段'] = lack_whether_from_q_down_df_after_add[user_name]
                except TypeError:
                    process_table['补水后-' + user_name + '_缺水时段'] = lack_whether_from_q_down_df_after_add[user_name]

            # 其他数据
            process_table['补水后-Z1'] = z_up_arr_after_add
            process_table['补水后-Z2'] = z_down_arr_after_add
            process_table['补水后-DH'] = dh_loss_arr_after_add
            process_table['补水后-时段末水位'] = z_store_arr_after_add

            return process_table

        # # 上库
        up_process_table = create_process_table(
            date=date_process,
            supply_order=up_supply_order,
            q_up_eco=0,
            q_in_arr=up_q_in_arr,
            q_gen_arr=up_q_gen_arr,
            q_thrown_arr=up_q_thrown_arr,
            v_store_arr=up_v_store_arr,
            h_net_arr=up_h_net_arr,
            power_arr=up_power_arr,
            q_environment_arr=up_q_environment_arr,
            environment_supply_arr=up_environment_supply_arr,
            environment_lack_arr=up_environment_lack_arr,
            environment_lack_whether_arr=up_environment_lack_whether_arr,
            q_loss_real_arr=up_q_loss_real_arr,
            z_up_arr=up_z_up_arr,
            z_down_arr=up_z_down_arr,
            dh_loss_arr=up_dh_loss_arr,
            days_arr=days_arr,
            z_store_arr=up_z_store_arr,
            real_add_q_arr=real_add_q_arr,
            real_add_q3_arr=real_add_q3_arr,
            q_user_demand_from_reservoir_df=up_q_user_demand_from_reservoir_df,
            q_user_demand_from_down_df=up_q_user_demand_from_down_df,
            q_supply_from_reservoir_df=up_q_supply_from_reservoir_df,
            q_supply_from_q_down_df=up_q_supply_from_q_down_df,
            q_lack_from_reservoir_df=up_q_lack_from_reservoir_df,
            q_lack_from_q_down_df=up_q_lack_from_q_down_df,
            lack_whether_from_reservoir_df=up_lack_whether_from_reservoir_df,
            lack_whether_from_q_down_df=up_lack_whether_from_q_down_df,
            user_special=user_special,
            q_gen_arr_after_add=up_q_gen_arr_after_add,
            q_thrown_arr_after_add=up_q_thrown_arr_after_add,
            v_store_arr_after_add=up_v_store_arr_after_add,
            h_net_arr_after_add=up_h_net_arr_after_add,
            power_arr_after_add=up_power_arr_after_add,
            z_up_arr_after_add=up_z_up_arr_after_add,
            z_down_arr_after_add=up_z_down_arr_after_add,
            dh_loss_arr_after_add=up_dh_loss_arr_after_add,
            z_store_arr_after_add=up_z_store_arr_after_add,
            q_supply_from_reservoir_df_after_add=up_q_supply_from_reservoir_df_after_add,
            q_supply_from_q_down_df_after_add=up_q_supply_from_q_down_df_after_add,
            q_lack_from_reservoir_df_after_add=up_q_lack_from_reservoir_df_after_add,
            q_lack_from_q_down_df_after_add=up_q_lack_from_q_down_df_after_add,
            lack_whether_from_reservoir_df_after_add=up_lack_whether_from_reservoir_df_after_add,
            lack_whether_from_q_down_df_after_add=up_lack_whether_from_q_down_df_after_add
        )

        # # 下库
        down_process_table = create_process_table(
            date=date_process,
            supply_order=down_supply_order,
            q_up_eco=up_environment_supply_arr,
            q_in_arr=down_q_in_arr + up_q_gen_arr_after_add + up_q_thrown_arr_after_add,
            q_gen_arr=down_q_gen_arr,
            q_thrown_arr=down_q_thrown_arr,
            v_store_arr=down_v_store_arr,
            h_net_arr=down_h_net_arr,
            power_arr=down_power_arr,
            q_environment_arr=down_q_environment_arr,
            environment_supply_arr=down_environment_supply_arr,
            environment_lack_arr=down_environment_lack_arr,
            environment_lack_whether_arr=down_environment_lack_whether_arr,
            q_loss_real_arr=down_q_loss_real_arr,
            z_up_arr=down_z_up_arr,
            z_down_arr=down_z_down_arr,
            dh_loss_arr=down_dh_loss_arr,
            days_arr=days_arr,
            z_store_arr=down_z_store_arr,
            real_add_q_arr=real_add_q_arr,
            real_add_q3_arr=real_add_q3_arr,
            q_user_demand_from_reservoir_df=down_q_user_demand_from_reservoir_df,
            q_user_demand_from_down_df=down_q_user_demand_from_down_df,
            q_supply_from_reservoir_df=down_q_supply_from_reservoir_df,
            q_supply_from_q_down_df=down_q_supply_from_q_down_df,
            q_lack_from_reservoir_df=down_q_lack_from_reservoir_df,
            q_lack_from_q_down_df=down_q_lack_from_q_down_df,
            lack_whether_from_reservoir_df=down_lack_whether_from_reservoir_df,
            lack_whether_from_q_down_df=down_lack_whether_from_q_down_df,
            user_special=user_special,
            q_gen_arr_after_add=down_q_gen_arr_after_add,
            q_thrown_arr_after_add=down_q_thrown_arr_after_add,
            v_store_arr_after_add=down_v_store_arr_after_add,
            h_net_arr_after_add=down_h_net_arr_after_add,
            power_arr_after_add=down_power_arr_after_add,
            z_up_arr_after_add=down_z_up_arr_after_add,
            z_down_arr_after_add=down_z_down_arr_after_add,
            dh_loss_arr_after_add=down_dh_loss_arr_after_add,
            z_store_arr_after_add=down_z_store_arr_after_add,
            q_supply_from_reservoir_df_after_add=down_q_supply_from_reservoir_df_after_add,
            q_supply_from_q_down_df_after_add=down_q_supply_from_q_down_df_after_add,
            q_lack_from_reservoir_df_after_add=down_q_lack_from_reservoir_df_after_add,
            q_lack_from_q_down_df_after_add=down_q_lack_from_q_down_df_after_add,
            lack_whether_from_reservoir_df_after_add=down_lack_whether_from_reservoir_df_after_add,
            lack_whether_from_q_down_df_after_add=down_lack_whether_from_q_down_df_after_add
        )
        down_process_table['补水前-时段末水位-'+up_res_name] = up_process_table['时段末水位']
        down_process_table['补水后-时段末水位-'+up_res_name] = up_process_table['补水后-时段末水位']

        return up_process_table, down_process_table

    def statistic_for_up_down(self, process_table, tm_str, res_name, output_col_name_list,
                              res_day_table_file_name="output_逐日过程.csv",
                              res_mon_table_file_name="output_逐月过程.csv",
                              res_year_table_file_name="output_逐年过程.csv",
                              res_hydroyear_table_file_name="output_水文年过程.csv",
                              tmp_res_day_table_file_name="output_汇总.csv"):
        result_day = {}
        result_mon = {}
        result_year = {}
        result_hydroyear = {}

        process_df = pd.DataFrame(process_table)

        date_process = process_df['日期']
        tmp_mon = {}
        tmp_year = {}
        tmp_hydro_year = {}
        for str_col_name in process_df.columns[1:]:  # 首列为date
            arr_value = process_df[str_col_name]
            # # 日系列转换为月、年
            tmp_day_input = pd.DataFrame({
                'Date': date_process,
                'Value': arr_value
            })
            arr_statistic = ComFun.statistic(tmp_day_input, 0, 4, 3)
            tmp_mon[str_col_name] = arr_statistic['Month']['Ave']
            tmp_year[str_col_name] = arr_statistic['Year']['Ave']
            tmp_hydro_year[str_col_name] = arr_statistic['HydroYear']['Ave']

        # index 列
        date_process_df = date_process.to_frame(name='年/月/日')
        mon_process_df = arr_statistic['Month']['Date'].dt.strftime('%Y-%m').to_frame(name='年/月')
        year_process_df = arr_statistic['Year']['Date'].dt.strftime('%Y').to_frame(name='年')
        hydro_year_process_df = arr_statistic['HydroYear'].index.to_frame(name='水文年')

        result_day[res_name] = process_df.iloc[:, 1:]
        result_mon[res_name] = tmp_mon
        result_year[res_name] = tmp_year
        result_hydroyear[res_name] = tmp_hydro_year

        tmp_result_day = {}
        tmp_dict = {}
        for col_name in output_col_name_list:
            try:
                tmp_dict[col_name] = process_df[col_name].values
            except KeyError:
                continue
        tmp_df = pd.DataFrame(tmp_dict)
        tmp_result_day[res_name] = tmp_df

        num_year = process_table['日期'].year[-1] - process_table['日期'].year[0] + 1
        ave_w_in = sum(process_table['来水流量（包含上库生态流量）'] * process_table['时段天数']) / num_year * 8.64 / (10 ** 4)
        ave_w_power = sum(process_table['发电流量'] * process_table['时段天数']) / num_year * 8.64 / (10 ** 4)
        ave_w_thrown = sum(process_table['弃水流量'] * process_table['时段天数']) / num_year * 8.64 / (10 ** 4)
        ave_w_loss = sum(process_table['蒸发、渗漏损失流量'] * process_table['时段天数']) / num_year * 8.64 / (10 ** 4)
        ave_power = sum(process_table['出力（kW）'] * process_table['时段天数']) / num_year * 24 / (10 ** 8)
        ave_z = np.average(process_table['时段末水位'])
        assurance_power = np.sort(process_table['出力（kW）'])[int(0.1 * len(process_table['出力（kW）']))]

        print(f"水库: {res_name}")
        print(f"年平均来水量：{ave_w_in:.2f}亿m3")
        print(f"年平均发电水量：{ave_w_power:.2f}亿m3")
        print(f"年平均弃水量：{ave_w_thrown:.2f}亿m3")
        print(f"年平均下泄水量：{(ave_w_power + ave_w_thrown):.2f}亿m3")
        print(f"年平均损失水量：{ave_w_loss:.2f}亿m3")
        print(f"年平均水位：{ave_z:.2f}m")
        print(f"保证出力：{assurance_power:.0f}kW")
        print(f"年平均发电量：{ave_power:.2f}亿kw·h")

        for user_name in self.reservoirs[res_name].supply_order:
            tmp_sum_lack_year = (result_hydroyear[res_name]['补水后-'+user_name+'_缺水时段'] > 0).sum()
            max_lack = result_hydroyear[res_name]['补水后-'+user_name+'_缺水流量'].max() * 365 * 8.64 / 10000
            print(f"{user_name}有{tmp_sum_lack_year}年缺水，保证率为{100-tmp_sum_lack_year/num_year*100}%")
            print(f"年最大缺水量为{max_lack: .2f}亿m3")

        # 创建水库子目录
        import os
        res_output_dir = res_name
        os.makedirs(res_output_dir, exist_ok=True)
        
        # 输出到子目录，使用 output_ 前缀
        ComFun.statistic_output(dict_dict=result_day, first_col_df=date_process_df,
                                output_file_name=f"{res_output_dir}/{res_day_table_file_name}")
        ComFun.statistic_output(dict_dict=result_mon, first_col_df=mon_process_df,
                                output_file_name=f"{res_output_dir}/{res_mon_table_file_name}")
        ComFun.statistic_output(dict_dict=result_year, first_col_df=year_process_df,
                                output_file_name=f"{res_output_dir}/{res_year_table_file_name}")
        ComFun.statistic_output(dict_dict=result_hydroyear, first_col_df=hydro_year_process_df,
                                output_file_name=f"{res_output_dir}/{res_hydroyear_table_file_name}")
        ComFun.statistic_output(dict_dict=tmp_result_day, first_col_df=date_process_df,
                                output_file_name=f"{res_output_dir}/{tmp_res_day_table_file_name}")


# def check_date_is_continues(date_process):
#     """
#     检验时间数组是否连续
#     :param date_process: 日尺度时间序列
#     :return: string，指出不连续位置
#     """
#     # if not isinstance(date_process, np.ndarray):
#     #     raise ValueError("Input must be a numpy array")
#
#     if len(date_process) < 2:
#         return ""
#
#     # 计算相邻日期的时间差
#     diff = np.diff(date_process).astype('timedelta64[D]').astype(int)
#
#     for i, d in enumerate(diff):
#         if d != 1:
#             bad_date = date_process[i]
#             y, m, d = bad_date.astype(object).year, bad_date.astype(object).month, bad_date.astype(object).day
#             return f"Data is not continuous, issue at {y}-{m}-{d}"
#     return ""


def parse_nested_list(s):
    """将字符串解析为列表"""
    if not isinstance(s, str) or s.strip() == '/' or s.strip() == '':
        return []  # 或者 return None，根据你的需求决定

    try:
        input_str = s.strip()

        # 如果是类似 [a,b,c] 的列表字符串
        if input_str.startswith('[') and input_str.endswith(']'):
            inner_str = input_str[1:-1]  # 去掉两边的 []
            elements = [x.strip() for x in inner_str.split(',') if x.strip()]
            return [e.strip('"').strip("'") for e in elements]  # 去掉可能的引号
        else:
            inner_str = input_str
            elements = [x.strip() for x in inner_str.split(',') if x.strip()]
            return [e.strip('"').strip("'") for e in elements]

    except (SyntaxError, ValueError):
        # 如果解析失败（比如格式错误），也可以选择返回空列表或抛出异常
        print(f"警告：无法解析字符串 -> {s}")
        return []


# def read_reservoir_info(list_data_dict=None, json_file="input.json", log_file="log.txt"):
#     """
#     从 JSON 文件中读取数据并初始化水库
#     :param list_data_dict: list，包含各个水库的info(dict)
#     :param json_file: 输入文件路径
#     :param log_file: log文件路径
#     :return: list_struct_reservoir
#     """
#     # 从 JSON 文件中读取数据
#     # if list_data_dict is None:
#     #     with open(json_file, "r", encoding="utf-8") as f:
#     #         list_data_dict = json.load(f)['reservoir']
#
#     # for tmp_reservoir_info in list_data_dict:
#     #     # 对数据进行简单检查，保证为连续的日尺度数据
#     #     date_process = pd.to_datetime(tmp_reservoir_info['inflow']["date_process"])
#     #     wrong_info = check_date_is_continues(date_process)
#     #     if wrong_info != '':
#     #         log_error(log_file, wrong_info)
#     #         raise ValueError(wrong_info)
#
#     reservoirs_by_id = {}
#     reservoirs_by_name = {}
#     for reservoir_id in range(len(list_data_dict)):
#         # 初始化水库
#         tmp_reservoir_info = list_data_dict[reservoir_id].copy()
#         tmp_reservoir_info["ifCalControlLine"] = False
#         tmp_reservoir_info["ifPowerTask"] = False
#         tmp_reservoir_info["ifSupplyTask"] = True
#         reservoir = StructReservoir(tmp_reservoir_info, reservoir_id)
#
#         reservoirs_by_id[reservoir.id] = reservoir
#         reservoirs_by_name[reservoir.name] = reservoir
#
#     return reservoirs_by_id, reservoirs_by_name


def transfer_operate_line_style(operate_line_df, read_mode, zv_dict=None, log_file='log.txt'):
    """"""
    if read_mode == 'sw' and zv_dict is None:
        wrong_info = f"转化调度线水位时，水位库容关系未提供"
        log_error(log_file, wrong_info)
        raise ValueError(wrong_info)

    tmp_operate_line_df = operate_line_df.copy()

    def is_mmdd_format(date_str):
        """检查字符串是否是 mm-dd 格式"""
        import re
        # 匹配 mm-dd 格式，其中 mm 是 01-12，dd 是 01-31
        pattern = r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
        return bool(re.match(pattern, date_str))
    # 原值
    date_series = tmp_operate_line_df.iloc[:, 0]

    def convert_chinese_date(date_str):
        """
        将 '1月1日' 格式的字符串转换为 '01-01' 格式
        """
        if pd.isna(date_str):
            return None
        # 使用正则提取数字
        match = re.match(r"(\d+)月(\d+)日", str(date_str))
        if match:
            month = match.group(1).zfill(2)  # 补零
            day = match.group(2).zfill(2)  # 补零
            return f"{month}-{day}"
        else:
            return None  # 无法解析

    # 判断是否是中文日期格式（示例）
    def is_mmdd_format(s):
        """简单判断是否已经是 MM-DD 格式"""
        return bool(re.match(r"^\d{1,2}-\d{1,2}$", str(s)))

    # === 处理逻辑 ===
    if is_mmdd_format(date_series.iloc[0]):
        # 如果已经是 MM-DD 格式
        tmp_date = date_series.values
    else:
        # 手动转换中文 "X月Y日" → "MM-DD"
        tmp_date = date_series.apply(convert_chinese_date).values
        print("转换后的 MM-DD 格式：", tmp_date)

    # 初始化结果数据结构
    tmp_operate_line = {
        'Month-Day': None,
        'normal_year': {},
        'leap_year': {}
    }

    # ----- 读取df -----
    n = 1
    # 处理每一对列（库容列和出力列）
    for icol in range(1, len(tmp_operate_line_df.columns), 2):
        if icol + 1 >= len(tmp_operate_line_df.columns):
            print(f"警告：最后一列 {icol} 没有配对的出力列，跳过。")
            break

        # 处理库容列
        if read_mode == 'sw':  # 读取调度线水位，转换为库容
            tmp_value_z = tmp_operate_line_df.iloc[:, icol].values
            tmp_value_v = np.array([np.interp(z, zv_dict["waterLevel"], zv_dict["volume"]) for z in tmp_value_z])
        else:  # 读取调度线库容
            tmp_value_v = tmp_operate_line_df.iloc[:, icol].values

        tmp_volume_df = ComFun.create_lookup_df(
            df_line_month={"Date": tmp_date, "Value": tmp_value_v.astype(float)},
            interpolate=True  # 库容通常需要插值
        )

        # 处理出力列-出力单位为MW
        tmp_value_p = tmp_operate_line_df.iloc[:, icol + 1].values

        tmp_power_df = ComFun.create_lookup_df(
            df_line_month={"Date": tmp_date, "Value": tmp_value_p.astype(float)},
            interpolate=False  # 出力可能不需要插值，根据业务定，默认不插值
        )

        # 存储结果
        key_v, key_p = f'v{n}', f'p{n}'
        for year_type in ['normal_year', 'leap_year']:
            tmp_operate_line[year_type][key_v] = tmp_volume_df[year_type].values
            tmp_operate_line[year_type][key_p] = tmp_power_df[year_type].values

        # 第一次时记录 Month-Day 所有调度线一致，只需要记录一次
        if n == 1:
            tmp_operate_line['Month-Day'] = tmp_volume_df.index.values

        n += 1
    # ----- 读取完毕 -----

    # ----- 储存为日 -----
    operate_line = {}

    # 获取所有 MM-DD
    month_days = tmp_operate_line['Month-Day']

    # 存储
    for irow, mmdd in enumerate(month_days):
        # 初始化该日期的条目
        operate_line[mmdd] = {
            'normal_year': [[], []],  # [v_list, p_list]
            'leap_year': [[], []]
        }

        # 遍历每条调度线
        for j in range(1, n):
            v_key, p_key = f'v{j}', f'p{j}'

            for year_type in ['normal_year', 'leap_year']:
                operate_line[mmdd][year_type][0].append(tmp_operate_line[year_type][v_key][irow])
                operate_line[mmdd][year_type][1].append(tmp_operate_line[year_type][p_key][irow])
    # ----- 储存完成 -----

    # print(operate_line[mmdd]['leap_year'])
    return operate_line


def read_info_txt(
        reservoirs=None,
        res_name="tmp_res",
        folder=".",
        gs_sheet_reservoir="input_水库信息.txt",
        gs_sheet_zv="input_水位-库容.txt",
        gs_sheet_zq="input_水位-流量.txt",
        gs_sheet_z_down="input_下游水位_下游尾水位恒定.csv",
        gs_sheet_limited_power="input_限制线.csv",
        gs_sheet_operate_line="input_发电调度线.csv",
        gs_sheet_target_operate_line="input_假定出力目标.txt",
        gs_sheet_runflow_data="input_来水及生态系列.csv",
        gs_sheet_kn_demand_data="input_库内需水系列.csv",
        gs_sheet_bx_demand_data="input_坝下需水系列.csv",
        log_file="log.txt",
        read_mode='kr'):
    """
    读取数据
    Args:
        reservoirs: 存储水库信息的字典集
        res_name: 新增水库名
        folder: 文件夹
        gs_sheet_reservoir: 水库信息
        gs_sheet_zv: 水库水位-库容曲线
        gs_sheet_zq: 水库下游_水位-流量曲线
        gs_sheet_z_down: 水库下游_下游尾水位恒定
        gs_sheet_limited_power: 发电限制库容
        gs_sheet_operate_line: 调度线信息
        gs_sheet_target_operate_line: 针对未知调度线，根据假定的出力目标进行调度线试算
        gs_sheet_runflow_data: 流量信息——来水、生态下泄需求
        gs_sheet_kn_demand_data: 库内需水
        gs_sheet_bx_demand_data: 坝下需水
        log_file: 记录文件
        read_mode: 读取方式，kr库容、sw水位
    Returns:
        reservoirs_dict: dict 水库信息

    """
    gs_sheet_reservoir = folder + "/" + gs_sheet_reservoir
    gs_sheet_zv = folder + "/" + gs_sheet_zv
    gs_sheet_zq = folder + "/" + gs_sheet_zq
    gs_sheet_z_down = folder + "/" + gs_sheet_z_down
    gs_sheet_limited_power = folder + "/" + gs_sheet_limited_power
    gs_sheet_operate_line = folder + "/" + gs_sheet_operate_line
    gs_sheet_target_operate_line = folder + "/" + gs_sheet_target_operate_line
    gs_sheet_runflow_data = folder + "/" + gs_sheet_runflow_data
    gs_sheet_kn_demand_data = folder + "/" + gs_sheet_kn_demand_data
    gs_sheet_bx_demand_data = folder + "/" + gs_sheet_bx_demand_data

    # 基本参数输入
    paras = pd.read_csv(gs_sheet_reservoir, sep="\t", encoding='utf-8', header=None, index_col=0)
    reservoir_info = {
        "reservoirName": paras.loc["水库名称"].values[0],
        "deadWaterLevel": float(paras.loc["水库死水位"].values[0]),
        "normalWaterLevel": float(paras.loc["水库正常水位"].values[0]),
        "wetSeasonLimitWaterLevel": float(paras.loc["水库汛限水位（梅汛）"].values[0]),
        "typhoonSeasonLimitWaterLevel": float(paras.loc["水库汛限水位（台汛）"].values[0]),
        "lossCalculateType": paras.loc["水库水量损失单位（0表示%，1表示万m3/d）"].values[0],
        "lossValue": paras.loc["水库水量损失"].values[0],
        "wetSeasonStartDate": paras.loc["梅汛期开始日期"].values[0],
        "wetSeasonEndDate": paras.loc["梅汛期结束日期"].values[0],
        "typhoonSeasonStartDate": paras.loc["台汛期开始日期"].values[0],
        "typhoonSeasonEndDate": paras.loc["台汛期结束日期"].values[0],
        "ifCalControlLine": False,
        "ifSupplyTask": False,
        "ifPowerTask": True,
        # "cal_step": paras.loc["计算步长"].values[0],
        "reservoirType": paras.loc["水库类型"].values[0],
        "k0": float(paras.loc["k0"].values[0]),
        "k1": float(paras.loc["k1"].values[0]),
        "k2": float(paras.loc["k2"].values[0]),
        "qm": float(paras.loc["机组设计流量"].values[0]),
        "wpv": float(paras.loc["装机容量"].values[0]),
        "dhMax": float(paras.loc["最大水头损失"].values[0]),
        "dhMin": float(paras.loc["最小水头损失"].values[0]),
        # "h_limited_power": paras.loc["发电死水位"].values[0],
        # "hDrink": float(paras.loc["供水死水位"].values[0]),
        # "hIrrigate": float(paras.loc["灌溉死水位"].values[0]),
        "constZDown": bool(float(paras.loc["下游尾水位是否恒定"].values[0])),
        "knowOperateLine": True,  # bool(float(paras.loc["调度线是否已知"].values[0])),
        "ifSecondReservoir": bool(float(paras.loc["是否为二级梯级电站"].values[0])),
        "qm_up": float(paras.loc["上级电站满发流量"].values[0]),
        "ifSupplyFromReservoir": bool(float(paras.loc["是否有库内取水"].values[0])),
        "userNameListSupplyFromReservoir": parse_nested_list(paras.loc["库内取水用水户"].values[0]),
        "ifSupplyFromDown": bool(float(paras.loc["是否有坝下取水"].values[0])),
        "userNameListSupplyFromDown": parse_nested_list(paras.loc["坝下取水用水户"].values[0]),
        "supplyOrder": parse_nested_list(paras.loc["供水顺序"].values[0])
    }
    print(f"{reservoir_info['reservoirName']}")
    print(f"库内用水户: {reservoir_info['userNameListSupplyFromReservoir']}")
    print(f"坝下用水户: {reservoir_info['userNameListSupplyFromDown']}")
    print(f"供水顺序: {reservoir_info['supplyOrder']}")

    # 水位库容曲线
    zv_df = pd.read_csv(gs_sheet_zv, encoding='utf-8', sep="\t")
    zv_df.sort_values(by='水位(m)', ascending=True, inplace=True)
    zzz = zv_df["水位(m)"].values
    vvv = zv_df["库容(万m3)"].values
    zv_dict = {
        "waterLevel": zzz,
        "volume": vvv
    }
    reservoir_info['zv'] = zv_dict

    # 水位流量曲线
    if reservoir_info['constZDown']:
        z_down_df = pd.read_csv(gs_sheet_z_down, encoding='utf-8', sep=",")
        tmp_date = z_down_df.iloc[:, 0].values
        tmp_val = z_down_df.iloc[:, 1].values
        z_down_dict = ComFun.create_lookup_df(
            df_line_month={
                "Date": tmp_date,
                "Value": np.array(tmp_val, dtype=float)
            },
            interpolate=True
        )
        reservoir_info['z_down'] = z_down_dict
    else:
        zq_df = pd.read_csv(gs_sheet_zq, encoding='utf-8', sep="\t")
        zq_df.sort_values(by='水位（m）', ascending=True, inplace=True)
        zzz = zq_df["水位（m）"].values
        qqq = zq_df["流量(m3/s)"].values
        zq_dict = {
            "waterLevel": zzz,
            "q_down": qqq
        }
    reservoir_info['zq'] = zq_dict

    # 来水及需水系列输入
    data = pd.read_csv(gs_sheet_runflow_data, encoding='utf-8', sep=",")
    # # 日期列
    date_arr = data.iloc[:, 0].values
    num_series_date = len(date_arr)
    # wrong_info = check_date_is_continues(pd.to_datetime(date_arr))
    # if wrong_info != '':
    #     log_error(log_file, wrong_info)
    #     raise ValueError(wrong_info)
    reservoir_info['date'] = date_arr

    # # 水库来水列
    if reservoir_info['ifSecondReservoir']:  # 是否为二级梯级水库
        reservoir_info['up'] = data.iloc[:, 1].values
        reservoir_info['inflow'] = data.iloc[:, 2].values
    else:
        reservoir_info['up'] = np.zeros(num_series_date)
        reservoir_info['inflow'] = data.iloc[:, 1].values
    # # 生态需水列
    reservoir_info['environment'] = data.iloc[:, -1].values

    # 需水数据读取
    # # 临时函数
    def read_demand_data(csv, name_list):
        demand_data = pd.read_csv(csv, encoding='utf-8', sep=",")
        # # 日期列，检验是否与来水系列对应
        demand_date_arr = demand_data.iloc[:, 0].values
        if demand_date_arr.all() != date_arr.all():
            tmp_wrong_info = f"输入数据日期不统一"
            log_error(log_file, tmp_wrong_info)
            raise ValueError(tmp_wrong_info)

        # # 储存需水过程
        demand_dict = {}
        for i in range(len(name_list)):
            tmp_user_name = name_list[i]
            if i + 1 > len(demand_data.columns):
                demand_dict[tmp_user_name] = np.zeros(num_series_date)
            else:
                demand_dict[tmp_user_name] = demand_data.iloc[:, i + 1].values

        return pd.DataFrame(demand_dict)

    # # 库内取水系列输入
    if reservoir_info['ifSupplyFromReservoir']:  # 是否有库内取
        # # 用水户名
        user_name_list = reservoir_info.get('userNameListSupplyFromReservoir', None)
        if user_name_list is None:
            wrong_info = f"基本信息中缺少“库内取水用水户”"
            log_error(log_file, wrong_info)
            raise ValueError(wrong_info)
        # # 储存
        reservoir_info['qUserDemandFromReservoirDf'] = read_demand_data(gs_sheet_kn_demand_data, user_name_list)
        # print(reservoir_info['qUserDemandFromReservoirDf'])

    # # 坝下取水系列输入
    if reservoir_info['ifSupplyFromDown']:  # 是否有坝下取
        # # 用水户名
        user_name_list = reservoir_info.get('userNameListSupplyFromDown', None)
        if user_name_list is None:
            wrong_info = f"基本信息中缺少“坝下取水用水户”"
            log_error(log_file, wrong_info)
            raise ValueError(wrong_info)
        # # 储存
        reservoir_info['qUserDemandFromDownDf'] = read_demand_data(gs_sheet_bx_demand_data, user_name_list)
        # print(reservoir_info['qUserDemandFromDownDf'])

    # # 损失流量
    # reservoir_info['loss'] = np.zeros(num_series_date)

    # 限制线
    tmp_limited_df = pd.read_csv(gs_sheet_limited_power, encoding='utf-8', sep=",")
    # # 日期列
    icol_limited_df = 0

    # 原数据
    date_series = tmp_limited_df.iloc[:, icol_limited_df]

    def convert_chinese_date(date_str):
        """
        将 '1月1日' 格式的字符串转换为 '01-01' 格式
        """
        if pd.isna(date_str):
            return None
        # 使用正则提取数字
        match = re.match(r"(\d+)月(\d+)日", str(date_str))
        if match:
            month = match.group(1).zfill(2)  # 补零
            day = match.group(2).zfill(2)  # 补零
            return f"{month}-{day}"
        else:
            return None  # 无法解析

    # 判断是否是中文日期格式（示例）
    def is_mmdd_format(s):
        """简单判断是否已经是 MM-DD 格式"""
        return bool(re.match(r"^\d{1,2}-\d{1,2}$", str(s)))

    # === 处理逻辑 ===
    if is_mmdd_format(date_series.iloc[0]):
        # 如果已经是 MM-DD 格式
        tmp_date = date_series.values
    else:
        # 手动转换中文 "X月Y日" → "MM-DD"
        tmp_date = date_series.apply(convert_chinese_date).values
        print("转换后的 MM-DD 格式：", tmp_date)

    num_limited_date = len(tmp_date)

    # # 发电死水位列
    icol_limited_df += 1
    if read_mode == 'sw':
        tmp_value_z = tmp_limited_df.iloc[:, icol_limited_df].values
        tmp_value_v = np.array([np.interp(z, zv_dict["waterLevel"], zv_dict["volume"]) for z in tmp_value_z])
    elif read_mode == 'kr':
        tmp_value_v = tmp_limited_df.iloc[:, icol_limited_df].values
    reservoir_info['vDeadPowerDay'] = ComFun.create_lookup_df(
        df_line_month={
            "Date": tmp_date,
            "Value": np.array(tmp_value_v, dtype=float)
        },
        interpolate=True
    )

    # # 发电限制水位列
    icol_limited_df += 1
    if read_mode == 'sw':
        tmp_value_z = tmp_limited_df.iloc[:, icol_limited_df].values
        tmp_value_v = np.array([np.interp(z, zv_dict["waterLevel"], zv_dict["volume"]) for z in tmp_value_z])
    elif read_mode == 'kr':
        tmp_value_v = tmp_limited_df.iloc[:, icol_limited_df].values
    reservoir_info['vLimitedPowerDay'] = ComFun.create_lookup_df(
        df_line_month={
            "Date": tmp_date,
            "Value": np.array(tmp_value_v, dtype=float)
        },
        interpolate=True
    )

    # # 临时函数
    def create_limited_volume_dict(user_names, limited_df, start_col_index, zv_relation, date_count, h_dead, date_range):
        """创建限制水位体积字典的临时函数"""
        result_dict = {}
        current_col_index = start_col_index
        for i in range(len(user_names)):
            current_col_index += 1
            user_name = user_names[i]
            if current_col_index < len(limited_df.columns):
                if read_mode == 'sw':
                    tmp_value_z = limited_df.iloc[:, current_col_index].values
                    tmp_value_v = np.array(
                        [np.interp(z, zv_relation["waterLevel"], zv_relation["volume"]) for z in tmp_value_z]
                    )
                elif read_mode == 'kr':
                    tmp_value_v = limited_df.iloc[:, current_col_index].values
            else:
                tmp_value_v = np.ones(date_count) * np.interp(h_dead, zv_relation["waterLevel"], zv_relation["volume"])
            result_dict[user_name] = ComFun.create_lookup_df(
                df_line_month={
                    "Date": date_range,
                    "Value": np.array(tmp_value_v, dtype=float)
                },
                interpolate=True  # 库容通常需要插值
            )
        return result_dict, current_col_index

    # # # 库内取水限制水位处理
    # if reservoir_info['ifSupplyFromReservoir']:  # 是否有库内取
    #     # # 用水户名
    #     user_name_list = reservoir_info.get('userNameListSupplyFromReservoir', None)
    #     # # 生成限制库容
    #     tmp_dict, icol_limited_df = create_limited_volume_dict(
    #         user_name_list, tmp_limited_df, icol_limited_df, zv_dict,
    #         num_limited_date, reservoir_info['deadWaterLevel'], tmp_date
    #         )
    #     print(icol_limited_df)
    #     # # 存储
    #     reservoir_info['vLimitedFromReservoir'] = tmp_dict
    #     print(tmp_dict)
    #
    # # # 坝下取水限制水位处理
    # if reservoir_info['ifSupplyFromDown']:  # 是否有坝下取
    #     # # 用水户名
    #     user_name_list = reservoir_info.get('userNameListSupplyFromDown', None)
    #     # # 生成限制库容
    #     tmp_dict, icol_limited_df = create_limited_volume_dict(
    #         user_name_list, tmp_limited_df, icol_limited_df, zv_dict,
    #         num_limited_date, reservoir_info['deadWaterLevel'], tmp_date
    #     )
    #     # # 存储
    #     reservoir_info['vLimitedFromDown'] = tmp_dict
    #     print(tmp_dict)

    # # 供水顺序
    user_name_list = reservoir_info['supplyOrder']
    tmp_dict, icol_limited_df = create_limited_volume_dict(
        user_name_list, tmp_limited_df, icol_limited_df, zv_dict,
        num_limited_date, reservoir_info['deadWaterLevel'], tmp_date
    )
    reservoir_info['vLimitedSupply'] = tmp_dict

    # 发电调度线
    if reservoir_info['reservoirType'] == '年调节':
        # 已知调度线
        if reservoir_info['knowOperateLine']:
            # ----- 读取调度线 -----
            tmp_operate_line_df = pd.read_csv(gs_sheet_operate_line, encoding='utf-8', sep=",")
            operate_line = transfer_operate_line_style(tmp_operate_line_df, read_mode, zv_dict, log_file)
            reservoir_info['operate_line_dict'] = operate_line

        # 未知调度线
        else:
            # ----- 读取目标试算线 -----
            tmp_target_line_df = pd.read_csv(gs_sheet_target_operate_line, encoding='utf-8', sep='\t')
            tmp_wpp_val = tmp_target_line_df.iloc[:, 0].values
            tmp_wpp_assure_rate = tmp_target_line_df.iloc[:, 1].values
            reservoir_info['targetWppVal'] = tmp_wpp_val
            reservoir_info['targetWppAssureRate'] = tmp_wpp_assure_rate

    # ------------------ 数组初始化 ---------------------
    reservoir = StructReservoir(reservoir_info, 0)
    reservoir.refresh()

    # 存入字典
    if reservoirs is None or reservoirs == {}:
        reservoirs = {}
    reservoirs[res_name] = reservoir

    return reservoirs


def read_paras(input_path="计算参数.csv"):
    """
    读取计算参数
    Args:
        input_path: str 参数文件名

    Returns:
        params_dict: dict 计算参数
    """

    # 获取小写后缀名
    ext = input_path.split('.')[-1]
    cvs_path = input_path.replace(ext, '') + "csv"
    xlsx_path = input_path.replace(ext, '') + "xlsx"

    try:
        paras = pd.read_excel(xlsx_path, header=None, index_col=0)
        print('xlsx')
    except:
        paras = pd.read_csv(cvs_path, sep=',', header=None, index_col=0)
        print('csv')

    paras_dict = {
        "up_res": paras.loc["上库"].values[0],
        "down_res": paras.loc["下库"].values[0],
        "up_v_special": pd.Series(paras.loc["上库特征库容"].values).dropna().astype(float).tolist(),
        "down_v_special": pd.Series(paras.loc["下库特征库容"].values).dropna().astype(float).tolist(),
        "need_add_user": pd.Series(paras.loc["需补水的用水户（利用上库特征库容之间进行补水）"].values).dropna().tolist(),
        "if_q_up_eco_as_in": bool(int(paras.loc["湖南镇生态水是否入黄坛口水量平衡"].values[0])),
        "stop_supply": pd.Series(paras.loc["当上库库容较低时（低于上库特征库容），下库停止供水的用水户"].values).dropna().tolist(),
    }
    another_add_user = pd.Series(paras.loc["额外再补用水户（利用上库特征库容以下进行补水）"].values).dropna()
    another_add_val = pd.Series(paras.loc["额外再补流量"].values).dropna()

    another_add = []
    for i_user in range(len(another_add_user)):
        tmp_add_user = another_add_user[i_user]

        try:
            tmp_add_val = another_add_val[i_user]
        except (IndexError, ValueError):
            tmp_add_val = -1

        another_add.append([tmp_add_user, tmp_add_val])
    paras_dict['another_add'] = another_add

    return paras_dict


def test_transfer_process():
    dataset = pd.read_csv("input.csv", encoding='utf-8', sep=',')

    date_process = pd.to_datetime(dataset.iloc[:, 0].values)
    val_process = dataset.iloc[:, 1].values
    print(date_process[:5])
    print(val_process[:5])

    new_date_process = ComFun.transfer_process(date_process, date_process, "日", "旬", 'first')
    transfer_process = ComFun.transfer_process(date_process, val_process, "日", "旬", 'sum')
    print(new_date_process[:5])
    print(transfer_process[:5])

    new_df = pd.DataFrame(
        {
            'date_process': new_date_process,
            'val_process': transfer_process
        }
    )
    new_df.to_csv('test.csv', sep=',')
    input()


if __name__ == "__main__":
    sks = {}
    sks = read_info_txt(sks, "湖南镇水库", "湖南镇水库相关参数")
    sks = read_info_txt(sks, "黄坛口水库", "黄坛口水库相关参数")

    base_info = {
        "CalStep": "旬",
        "EPSYH": 0.01,
        "EPSYV": 1,
        "EPSYW": 1
    }

    paras_dict = read_paras()
    print(paras_dict)

    output_list = pd.read_csv('输出列名.csv', sep='\t', header=None, encoding='utf-8').values[:, 0].tolist()
    print(output_list)

    st = time.time()
    test = HydroElectricity(sks, base_info)
    # test.calculate(max_count=2)
    up_table, down_table = test.power_operate_year_up_down(
        if_up_q_eco_as_in=paras_dict['if_q_up_eco_as_in'],  # 湖南镇生态水是否入黄坛口水量平衡（1为是，0为否）
        up_res_name=paras_dict['up_res'],  # '湖南镇水库'
        down_res_name=paras_dict['down_res'],  # '黄坛口水库',
        up_v_special=paras_dict['up_v_special'],  # [59994, 55919],
        down_v_special=paras_dict['down_v_special'],  # [7040],
        need_add_user=paras_dict['need_add_user'],  # ['衢州生活工业', '西干渠灌溉', '金华', '龙游']
        user_special=paras_dict['another_add'],  # [['衢州生活工业', 7.52]]
        user_stop_supply=paras_dict['stop_supply'],  # ['西干渠灌溉', '东中干渠灌溉', '黄坛口生态', '金华', '龙游']
    )
    en = time.time()
    print(f"计算耗时：{en - st}s")

    # test.statistic()
    tm_str = datetime.now().strftime('%Y_%m%d_%H%M')
    tm_str = ''

    test.statistic_for_up_down(up_table, tm_str, f'湖南镇水库', output_list)
    test.statistic_for_up_down(down_table, tm_str, f'黄坛口水库', output_list)

    en = time.time()
    print(f"总耗时：{en-st}s")

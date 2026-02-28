# 概湖降雨过程计算项目

## 项目简介

本项目用于计算概湖降雨过程，综合考虑分区降雨系数、取水户用水量等因素，生成最终的概湖净降雨过程数据。

## 文件结构

```
zdys_comby 2/
├── comb0609.py              # 主处理程序
├── README.md                # 项目说明文档
├── data/                    # 数据目录
│   ├── 01csv/              # 分区CSV数据
│   ├── 02area/             # 面积数据
│   ├── 03ggxs/             # 降雨系数数据  
│   ├── 04deduct/           # 扣减计算数据
│   ├── logs/               # 日志文件
│   ├── final.csv           # 最终结果
│   └── merge_all.csv       # 合并数据
├── input_*.txt             # 输入数据文件
└── output_*.txt            # 输出结果文件
```

## 输入文件说明

| 文件名 | 中文含义 | 数据类型 | 描述 |
|--------|---------|----------|------|
| input_FQNNGXL.txt | 分区年内降雨量 | TIME TABLE | 各分区的日降雨量数据，按时间序列排列 |
| input_GHJYL.txt | 概湖降雨量 | TIME TABLE | 各概湖的降雨量时间序列数据 |
| static_PYLYSCS.txt | 排涝系统参数 | 分区配置 | 包含分区名称、概湖对应关系、面积等参数 |
| input_YSH_GH.txt | 用水户-概湖对应关系 | 关系映射 | 用水户与概湖之间的对应关系表 |
| input_YSH.txt | 用水户用水量 | TIME TABLE | 各用水户的取水量时间序列数据 |

## 输出文件说明

| 文件名 | 中文含义 | 描述 |
|--------|---------|------|
| data/02area/gaihu.csv | 概湖面积数据 | 各概湖的面积信息汇总 |
| data/02area/fenqu.csv | 分区面积数据 | 各分区的面积信息汇总 |
| data/03ggxs/G***_ggxs.csv | 概湖降雨系数 | 各概湖的小时降雨系数数据 |
| data/04deduct/G***_deduct.csv | 扣减计算结果 | 各概湖的降雨扣减计算数据 |
| data/merge_all.csv | 合并降雨数据 | 所有概湖的降雨数据合并结果 |
| data/final.csv | 最终净降雨结果 | 考虑所有因素后的概湖净降雨过程 |
| output_GHJYL.txt | 概湖净降雨过程 | 最终输出的概湖净降雨过程数据 |

## 处理流程

### 1. 分区处理 (partition_process)
- 解析 `static_PYLYSCS.txt` 文件
- 提取各分区的概湖信息和面积数据
- 生成分区对应的CSV文件到 `data/01csv/` 目录

### 2. 面积处理 (area_process)
- 从分区CSV文件中提取面积信息
- 生成概湖面积汇总表 (`gaihu.csv`)
- 生成分区面积汇总表 (`fenqu.csv`)

### 3. 降雨系数处理 (ggxs_process)
- 读取分区年内降雨量数据 (`input_FQNNGXL.txt`)
- 将日降雨量转换为小时降雨量
- 根据分区面积计算各概湖的降雨系数
- 生成各概湖的降雨系数文件 (`G***_ggxs.csv`)

### 4. 取水处理 (intake_process)
- 处理用水户与概湖的对应关系
- 计算各概湖的取水量影响
- 生成取水数据文件 (`G***_intake.csv`)

### 5. 扣减处理 (deduct_process)
- 综合降雨系数和取水量数据
- 计算总需水量 (降雨 + 取水)
- 生成扣减计算结果 (`G***_deduct.csv`)

### 6. 合并和最终处理 (merge_final_process)
- 合并所有概湖的降雨数据
- 与原始概湖降雨量进行对比扣减
- 生成最终的概湖净降雨过程

## 运行方法

### 基本运行
```bash
python comb0609.py
```

### 指定工作目录
```bash
python comb0609.py /path/to/project/directory
```

### 运行特定步骤
```bash
# 只运行分区处理
python comb0609.py --steps partition

# 运行多个步骤
python comb0609.py --steps partition area ggxs

# 可选步骤：partition, area, ggxs, intake, deduct, merge_final, all
```

## 数据格式说明

### TIME TABLE 格式
时间序列数据，第一列为日期，后续列为各测点/分区的数值：
```
日期        G001    G002    G003
2023/1/1    10.5    8.2     12.1
2023/1/2    5.3     6.7     8.9
```

### 分区配置文件格式
包含分区信息的配置文件，格式如下：
```
分区01-名称:NSPYQ（南沙）
包含概湖个数:3
包含概湖的名称:G001,G002,G003
包含概湖对应的面积(m2):1000.0,2000.0,1500.0
```

## 注意事项

1. **数据单位**：
   - 面积单位：平方米 (m²) 和平方公里 (km²)
   - 降雨量单位：毫米 (mm)
   - 时间精度：小时级

2. **文件编码**：所有输入文件需使用 UTF-8 编码

3. **日志记录**：程序运行日志保存在 `data/logs/` 目录下

4. **错误处理**：如遇到数据文件缺失或格式错误，程序会记录警告并尝试继续处理

## 依赖环境

- Python 3.6+
- pandas
- pathlib (Python 3.4+ 内置)
- datetime (Python 内置)
- logging (Python 内置)

## 安装依赖

```bash
pip install pandas
```

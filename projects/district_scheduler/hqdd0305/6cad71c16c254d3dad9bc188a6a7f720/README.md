# 浙东河区调度模型（hqdd）

水资源逐日水平衡计算系统。覆盖 19 个河区、6 个分水枢纽，基于来水/需水数据计算供需平衡、排水调度和枢纽引水需求。

## 运行

```bash
# 使用当前目录作为数据目录
python main.py

# 指定工作目录
python main.py /path/to/data/directory
```

依赖：`pandas`, `scipy`, `numpy`

## 输入文件

### 静态配置（static_）

| 文件 | 内容 |
|------|------|
| `static_HQ_ZQ.txt` | 河区库容曲线（死/低/中/高/超蓄 水位与库容对应关系） |
| `static_HQ_SK.txt` | 河区-水库归属映射 |
| `static_SW_PS.txt` | 排水水位配置 |
| `static_FSSN_RULES.txt` | 分水枢纽层级规则（枢纽包含哪些子区域/子枢纽） |

### 时序输入（input_）

| 文件 | 含义 | 数据类别 |
|------|------|---------|
| `input_GPS_GGXS.txt` | 农业需水（灌溉供水） | 需水 |
| `input_XS_FN.txt` | 非农需水 | 需水 |
| `input_XS_ST.txt` | 其他生态需水 | 需水 |
| `input_FQJL.txt` | 河网供水（翻倾降落） | 来水 |
| `input_LS_QT.txt` | 其他外供 | 来水 |
| `input_SK.txt` | 各水库来水 | 来水 |
| `input_GPS_PYCS.txt` | 平原产水 | 来水 |
| `input_SW_CS.txt` | 初始水位 | 其他 |
| `input_SW_MB.txt` | 目标水位 | 其他 |

所有文件均为 UTF-8 编码、制表符分隔，首行表头，首列为日期。

## 输出文件

### 河区输出（output_hq_）

每个河区生成一个详细结果文件，包含逐日来水、需水、水平衡计算全过程。

| 文件 | 河区 |
|------|------|
| `output_hq_FHPYQ` | 丰惠平原区 |
| `output_hq_YYPYSHQ` | 余姚平原上河区 |
| `output_hq_YYPYXHQ` | 余姚平原下河区 |
| `output_hq_YYPYYJSYQ` | 余姚平原姚江上游区 |
| `output_hq_YYPYYJXYQ` | 余姚平原姚江下游区 |
| `output_hq_YYPYMZZHQ` | 余姚平原马渚中河区 |
| `output_hq_NSPYQ` | 南沙平原区 |
| `output_hq_YJYXDGYYSQ` | 姚江沿线大工业用水区 |
| `output_hq_CXPYDHQ` | 慈溪平原东河区 |
| `output_hq_CXPYZHQ` | 慈溪平原中河区 |
| `output_hq_CXPYXHQ` | 慈溪平原西河区 |
| `output_hq_JBZHPYQ` | 江北镇海平原区 |
| `output_hq_HSPYQ` | 海曙平原区 |
| `output_hq_SYPYQ` | 绍虞平原区 |
| `output_hq_ZSDLYSQ` | 舟山大陆用水区 |
| `output_hq_YBPYSHQ` | 虞北平原上河区 |
| `output_hq_YBPYZHQ` | 虞北平原中河区 |
| `output_hq_SSPYQ` | 蜀山平原区 |
| `output_hq_YZTSQ` | 鄞州调水区 |

### 汇总输出

| 文件 | 内容 |
|------|------|
| `output_hq_all.txt` | 16 河区逐日汇总 |
| `output_hq_all_cumulative.txt` | 16 河区逐日累计汇总 |
| `output_hq_all_total.txt` | 16 河区期间合计 |

### 枢纽输出（output_sn_）

| 文件 | 枢纽 |
|------|------|
| `output_sn_XSSN` | 萧山枢纽 |
| `output_sn_SXZ` | 三兴闸 |
| `output_sn_SYSN` | 上虞枢纽 |
| `output_sn_PQZ` | 浦前闸 |
| `output_sn_MOUSZ` | 牟山闸 |
| `output_sn_STZQTZ` | 四塘闸/七塘闸 |

## 核心计算流程

```
Config.initialize()                          # 加载库容曲线、水位配置
  → Config.load_fssn_rules()                 # 加载枢纽层级规则
  → Config.load_level_data()                 # 加载初始/目标/排水水位
    → ReservoirInflowGenerator.generate()    # 汇总各区水库来水
      → DistrictDataProcessor                # 组装分区来水/需水数据
        → WaterBalanceCalculator             # 逐日水平衡迭代
          → FSSnDataGenerator                # 递归汇总枢纽引水需求
            → DataOutputProcessor            # 合并中间数据、生成汇总报表
```

### 类职责

| 类 | 职责 |
|---|---|
| `Config` | 路径管理、静态配置加载（库容曲线列、水位、枢纽规则） |
| `DataLoader` | 读取 TSV 文件、构建水位↔容积插值函数 |
| `ReservoirInflowGenerator` | 按 `static_HQ_SK.txt` 映射汇总各区水库来水 |
| `DistrictDataProcessor` | 分区来水/需水数据组装，动态平衡区特殊处理 |
| `WaterBalanceCalculator` | 核心逐日水平衡计算（净流量→容积→排水→缺水） |
| `FSSnDataGenerator` | 递归展开枢纽层级，汇总叶子节点缺水量 |
| `DataOutputProcessor` | 合并中间数据、重命名输出、生成汇总报表 |

## 需水/来水数据映射

### 需水构成

```
总需水量
├── 需水量
│   ├── 农业需水      ← input_GPS_GGXS.txt
│   └── 非农需水      ← input_XS_FN.txt
└── 生态需水
    ├── 其他生态需水  ← input_XS_ST.txt
    └── 水位生态需水  （计算值，当前简化为 0）
```

### 来水构成

```
合计来水
├── 平原产水  ← input_GPS_PYCS.txt
├── 其他外供  ← input_LS_QT.txt（动态平衡区为计算值）
├── 河网供水  ← input_FQJL.txt
└── 水库供水  ← input_SK.txt（经 static_HQ_SK.txt 映射汇总）
```

### 水平衡核心公式

- **净流量** = 合计来水 - 总需水量
- **日末容积** = 日中容积 + 缺水(浙东需供)
- **河区排水** = max(0, 日末容积 - 排水容积)

### 动态平衡区

南沙、海曙、绍虞、蜀山 4 个河区启用动态平衡模式：自动调整"其他外供"使净流量为零。

### 枢纽层级

```
萧山枢纽
├── 三兴闸
│   ├── 虞北平原上河区
│   ├── 虞北平原中河区
│   ├── 浦前闸
│   │   ├── 余姚平原上河区
│   │   └── 四塘闸/七塘闸
│   │       ├── 慈溪平原西河区
│   │       ├── 慈溪平原中河区
│   │       └── 慈溪平原东河区
│   └── 牟山闸
│       ├── 余姚平原下河区
│       └── 余姚平原马渚中河区
└── 上虞枢纽
    ├── 丰惠平原区
    ├── 余姚平原姚江上游区
    ├── 余姚平原姚江下游区
    └── 江北镇海平原区
```

## 中间数据目录

计算过程中在 `data/` 下生成分阶段中间文件：

| 目录 | 阶段 |
|------|------|
| `data/01_inflow/` | 各区来水数据 |
| `data/02_demand/` | 各区需水数据 |
| `data/03_calculated/` | 水平衡计算结果 |
| `data/04_final/` | 合并后的最终分区结果 |
| `data/05_discrict/` | 分区汇总（含 xlsx） |

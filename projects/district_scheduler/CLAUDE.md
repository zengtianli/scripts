# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

浙东河区调度模型（hqdd）— 水资源逐日水平衡计算系统。覆盖 19 个河区、6 个分水枢纽，基于来水/需水数据计算供需平衡、排水调度和枢纽引水需求。

## 运行

```bash
# 使用当前目录
python main.py

# 指定工作目录
python main.py /path/to/data/directory
```

依赖：`pandas`, `scipy`, `numpy`（标准数据科学栈，无 requirements.txt）

无测试套件、无 lint 配置、无构建步骤。

## 架构

单文件架构 `main.py`，包含 7 个类，按数据流水线顺序执行：

```
Config.initialize() → Config.load_fssn_rules() → Config.load_level_data()
  → ReservoirInflowGenerator.generate()
    → DistrictDataProcessor.generate_categorized_data()
      → WaterBalanceCalculator.calculate()  [逐日逐区迭代]
        → FSSnDataGenerator.generate_supplement_data()
          → DataOutputProcessor.merge_and_output_final_data()
            → copy_and_rename_files() → generate_16_hq_summary() → correct_total_summary()
```

入口：`WaterResourcesManager.run()` 串联整个流程。

### 核心类职责

| 类 | 职责 |
|---|---|
| `Config` | 路径管理、静态配置加载（库容曲线列、水位、枢纽规则） |
| `DataLoader` | 读取 TSV 文件、构建水位↔容积插值函数（`scipy.interpolate.interp1d`） |
| `ReservoirInflowGenerator` | 按 `static_HQ_SK.txt` 映射汇总各区水库来水 |
| `DistrictDataProcessor` | 分区来水/需水数据组装，动态平衡区特殊处理 |
| `WaterBalanceCalculator` | 核心逐日水平衡计算（净流量→容积→排水→缺水） |
| `FSSnDataGenerator` | 递归展开枢纽层级，汇总叶子节点缺水量 |
| `DataOutputProcessor` | 合并中间数据、重命名输出、生成汇总报表 |

### 关键业务逻辑

- 水平衡公式：`净流量 = 合计来水 - 总需水量`，`日末容积 = 日中容积 + 缺水(浙东需供)`，`河区排水 = max(0, 日末容积 - 排水容积)`
- 动态平衡区（南沙、海曙、绍虞、蜀山）：自动调整"其他外供"使净流量为零
- 枢纽层级递归：萧山枢纽 → 三兴闸/上虞枢纽 → 浦前闸/牟山闸 → 四塘闸/七塘闸 → 具体河区
- 当前使用 16 河区汇总（`generate_16_hq_summary`），19 河区汇总已注释

## 数据约定

- 所有文件 UTF-8 编码、制表符分隔（`\t`）
- 文件命名：`static_*.txt`（静态配置）、`input_*.txt`（时序输入）、`output_hq_*.txt`（河区输出）、`output_sn_*.txt`（枢纽输出）
- 中间数据按处理阶段存放在 `data/01_inflow/` ~ `data/05_discrict/`（注意 discrict 是原有拼写）
- 河区中文名 → 拼音缩写映射定义在 `DISTRICT_NAME_MAPPING` 和 `SLUICE_NAME_MAPPING`

## 修改注意事项

- 修改水平衡计算逻辑时，注意日初容积依赖前一天排末容积的链式关系
- `SUMMARY_COLUMNS` 列表决定汇总报表包含哪些字段，新增计算字段需同步更新
- 汇总时容积类字段需要重新计算（不能简单求和），参见 `generate_16_hq_summary` 中的修复逻辑
- `correct_total_summary` 对 total 文件做二次修正（日初容积取首日、排末容积取末日）

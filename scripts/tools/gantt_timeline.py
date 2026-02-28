#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.patches as mpatches
import os

# 获取脚本所在目录，确保图片输出到 output/ 子目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_chinese_fonts():
    """
    设置中文字体支持

    Returns:
        FontProperties对象，用于设置中文字体
    """
    plt.rcParams.update({
        'font.sans-serif': ['Arial Unicode MS', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
        'axes.unicode_minus': False, 
        'font.family': 'sans-serif'
    })
    mpl.rc('font', **{
        'sans-serif': ['Arial Unicode MS', 'Microsoft YaHei', 'SimHei'],
        'serif': ['Arial Unicode MS', 'SimSun'],
        'monospace': ['Arial Unicode MS']
    })
    try:
        return FontProperties(fname='/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
    except:
        return FontProperties()

# 设置中文字体
chinese_font = setup_chinese_fonts()

# 新的任务数据 - 供水配置研究项目
tasks_data = [
    # 四大阶段的主要工作任务
    {'任务': '第一阶段：项目启动与基础调研', '开始': '2025-11-01', '结束': '2025-11-14', '阶段': '项目启动与基础调研', '类型': '工作任务'},
    {'任务': '第二阶段：需求预测与平衡分析', '开始': '2025-11-15', '结束': '2025-12-26', '阶段': '需求预测与平衡分析', '类型': '工作任务'},
    {'任务': '第三阶段：方案编制与优化', '开始': '2025-12-27', '结束': '2026-02-13', '阶段': '方案编制与优化', '类型': '工作任务'},
    {'任务': '第四阶段：报告完善与评审', '开始': '2026-02-14', '结束': '2026-03-28', '阶段': '报告完善与评审', '类型': '工作任务'},

    # 详细工作任务 - 第一阶段（2周）
    {'任务': '基础资料收集与整理', '开始': '2025-11-01', '结束': '2025-11-07', '阶段': '项目启动与基础调研', '类型': '子任务'},
    {'任务': '现场踏勘调研', '开始': '2025-11-03', '结束': '2025-11-10', '阶段': '项目启动与基础调研', '类型': '子任务'},
    {'任务': '现状分析与评估', '开始': '2025-11-08', '结束': '2025-11-14', '阶段': '项目启动与基础调研', '类型': '子任务'},

    # 详细工作任务 - 第二阶段（6周）
    {'任务': '人口与经济预测', '开始': '2025-11-15', '结束': '2025-11-28', '阶段': '需求预测与平衡分析', '类型': '子任务'},
    {'任务': '分质需水量预测', '开始': '2025-11-20', '结束': '2025-11-29', '阶段': '需求预测与平衡分析', '类型': '子任务'},
    {'任务': '供水能力分析', '开始': '2025-11-30', '结束': '2025-12-10', '阶段': '需求预测与平衡分析', '类型': '子任务'},
    {'任务': '供需平衡分析', '开始': '2025-12-11', '结束': '2025-12-16', '阶段': '需求预测与平衡分析', '类型': '子任务'},
    {'任务': '预测成果汇总', '开始': '2025-12-17', '结束': '2025-12-26', '阶段': '需求预测与平衡分析', '类型': '子任务'},

    # 详细工作任务 - 第三阶段（7周，含春节）
    {'任务': '供水片区划分', '开始': '2025-12-27', '结束': '2026-01-03', '阶段': '方案编制与优化', '类型': '子任务'},
    {'任务': '分质供水体系构建', '开始': '2026-01-04', '结束': '2026-01-20', '阶段': '方案编制与优化', '类型': '子任务'},
    {'任务': '春节假期', '开始': '2026-01-26', '结束': '2026-02-02', '阶段': '方案编制与优化', '类型': '假期'},
    {'任务': '分片区配置优化', '开始': '2026-01-21', '结束': '2026-02-08', '阶段': '方案编制与优化', '类型': '子任务'},
    {'任务': '技术经济分析', '开始': '2026-02-09', '结束': '2026-02-13', '阶段': '方案编制与优化', '类型': '子任务'},

    # 详细工作任务 - 第四阶段（6周）
    {'任务': '报告初稿编制', '开始': '2026-02-14', '结束': '2026-02-25', '阶段': '报告完善与评审', '类型': '子任务'},
    {'任务': '图件与表格编制', '开始': '2026-02-14', '结束': '2026-02-28', '阶段': '报告完善与评审', '类型': '子任务'},
    {'任务': '三级校审', '开始': '2026-02-26', '结束': '2026-03-10', '阶段': '报告完善与评审', '类型': '子任务'},
    {'任务': '送审稿报告提交', '开始': '2026-03-11', '结束': '2026-03-15', '阶段': '报告完善与评审', '类型': '子任务'},
    {'任务': '专家评审与修改', '开始': '2026-03-16', '结束': '2026-03-25', '阶段': '报告完善与评审', '类型': '子任务'},
    {'任务': '最终成果整理提交', '开始': '2026-03-26', '结束': '2026-03-28', '阶段': '报告完善与评审', '类型': '子任务'},

    # 关键里程碑（9个）
    {'任务': 'M1：工作方案确定', '开始': '2025-11-04', '结束': '2025-11-04', '阶段': '项目启动与基础调研', '类型': '里程碑'},
    {'任务': 'M2：分质需水预测完成', '开始': '2025-11-29', '结束': '2025-11-29', '阶段': '需求预测与平衡分析', '类型': '里程碑'},
    {'任务': 'M3：供需平衡分析完成', '开始': '2025-12-16', '结束': '2025-12-16', '阶段': '需求预测与平衡分析', '类型': '里程碑'},
    {'任务': 'M4：供水片区划分确定', '开始': '2026-01-03', '结束': '2026-01-03', '阶段': '方案编制与优化', '类型': '里程碑'},
    {'任务': 'M5：分质供水系统布局方案完成', '开始': '2026-02-10', '结束': '2026-02-10', '阶段': '方案编制与优化', '类型': '里程碑'},
    {'任务': 'M6：报告初稿完成', '开始': '2026-02-25', '结束': '2026-02-25', '阶段': '报告完善与评审', '类型': '里程碑'},
    {'任务': 'M7：送审稿报告提交', '开始': '2026-03-15', '结束': '2026-03-15', '阶段': '报告完善与评审', '类型': '里程碑'},
    {'任务': 'M8：通过专家评审', '开始': '2026-03-20', '结束': '2026-03-20', '阶段': '报告完善与评审', '类型': '里程碑'},
    {'任务': 'M9：最终成果提交', '开始': '2026-03-28', '结束': '2026-03-28', '阶段': '报告完善与评审', '类型': '里程碑'},
]

# 将数据转换为DataFrame
df = pd.DataFrame(tasks_data)
df['开始'] = pd.to_datetime(df['开始'])
df['结束'] = pd.to_datetime(df['结束'])
df['工期'] = (df['结束'] - df['开始']).dt.days + 1

# 设置颜色方案
phase_colors = {
    '项目启动与基础调研': '#4A90E2',
    '需求预测与平衡分析': '#50E3C2', 
    '方案编制与优化': '#F5A623',
    '报告完善与评审': '#E74C3C',
}

type_colors = {
    '工作任务': '#2196F3',
    '里程碑': '#FF5722',
    '子任务': '#9C27B0',
    '假期': '#CCCCCC'
}

df['阶段颜色'] = df['阶段'].map(phase_colors)
df['类型颜色'] = df['类型'].map(type_colors)

# --- 图表 1: 完整项目甘特图 ---
def plot_complete_gantt(df):
    fig, ax = plt.subplots(figsize=(18, 12))
    
    # 按类型分组绘制
    for i, (idx, task) in enumerate(df.iterrows()):
        if task['类型'] == '里程碑':
            # 里程碑用菱形标记
            ax.scatter(task['开始'], i, marker='D', s=200, color=task['类型颜色'], 
                      zorder=3, edgecolor='black', linewidth=2)
            ax.text(task['开始'], i-0.3, '★', ha='center', va='center', 
                   fontsize=16, color='gold', weight='bold')
        else:
            # 普通任务用条形图
            ax.barh(i, task['工期'], left=task['开始'], height=0.6, 
                   color=task['阶段颜色'], alpha=0.8, edgecolor='black')
            
            # 在条形图上添加任务名称
            if task['工期'] > 3:  # 只在足够长的任务上显示文字
                ax.text(task['开始'] + pd.Timedelta(days=task['工期']/2), i, 
                       task['任务'].split('：')[0] if '：' in task['任务'] else task['任务'][:10], 
                       ha='center', va='center', fontsize=8, weight='bold', color='white')
    
    # 设置格式
    ax.set_title('供水配置研究项目完整甘特图（总工期146天）', fontsize=22, pad=20, weight='bold')
    ax.set_xlabel('项目时间线', fontsize=14, labelpad=10)
    ax.set_ylabel('项目任务', fontsize=14, labelpad=10)
    
    # 设置Y轴标签
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df['任务'], fontsize=10)
    ax.invert_yaxis()
    
    # 设置X轴日期格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45, ha='right', fontsize=12)
    
    # 添加图例
    phase_patches = [mpatches.Patch(color=color, label=label) for label, color in phase_colors.items()]
    type_patches = [mpatches.Patch(color=color, label=label) for label, color in type_colors.items()]
    
    legend1 = ax.legend(handles=phase_patches, title='项目阶段', 
                       bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
    legend2 = ax.legend(handles=type_patches, title='任务类型', 
                       bbox_to_anchor=(1.02, 0.7), loc='upper left', fontsize=10)
    ax.add_artist(legend1)
    
    ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.grid(False, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "供水配置研究项目_完整甘特图.png"), dpi=300, bbox_inches='tight')
    plt.show()

# --- 图表 2: 主要任务甘特图 ---
def plot_main_tasks_gantt(df):
    main_tasks_df = df[df['类型'] == '工作任务'].copy()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for i, (idx, task) in enumerate(main_tasks_df.iterrows()):
        ax.barh(i, task['工期'], left=task['开始'], height=0.7, 
               color=task['阶段颜色'], alpha=0.9, edgecolor='black', linewidth=2)
        
        # 添加任务时间标注
        mid_date = task['开始'] + pd.Timedelta(days=task['工期']/2)
        ax.text(mid_date, i, f"{task['开始'].strftime('%m/%d')}-{task['结束'].strftime('%m/%d')}", 
                ha='center', va='center', fontsize=11, weight='bold', color='white')
    
    ax.set_title('供水配置研究项目 - 主要工作任务时间轴', fontsize=18, pad=20, weight='bold')
    ax.set_xlabel('项目时间线', fontsize=14)
    ax.set_ylabel('主要工作任务', fontsize=14)
    
    ax.set_yticks(range(len(main_tasks_df)))
    ax.set_yticklabels(main_tasks_df['任务'], fontsize=12)
    ax.invert_yaxis()
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(fontsize=12, rotation=45, ha='right')
    
    ax.grid(True, which='major', axis='x', linestyle=':', linewidth=0.8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "供水配置研究项目_主要任务甘特图.png"), dpi=300, bbox_inches='tight')
    plt.show()

# --- 图表 3: 里程碑时间线 ---
def plot_milestones_timeline(df):
    milestones_df = df[df['类型'] == '里程碑'].copy()
    
    fig, ax = plt.subplots(figsize=(16, 6))
    
    # 绘制时间线
    y_pos = 0
    ax.plot([milestones_df['开始'].min(), milestones_df['开始'].max()], [y_pos, y_pos], 
            'k-', linewidth=4, alpha=0.3)
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    
    for i, (idx, milestone) in enumerate(milestones_df.iterrows()):
        # 绘制里程碑点
        ax.scatter(milestone['开始'], y_pos, s=400, c=colors[i], 
                  marker='o', edgecolor='black', linewidth=3, zorder=3)
        
        # 添加里程碑标号
        ax.text(milestone['开始'], y_pos, str(i+1), ha='center', va='center', 
               fontsize=14, weight='bold', color='white')
        
        # 添加里程碑名称和日期
        ax.text(milestone['开始'], y_pos + 0.15, milestone['任务'].replace('里程碑', 'M'), 
               ha='center', va='bottom', fontsize=12, weight='bold', rotation=0)
        ax.text(milestone['开始'], y_pos - 0.15, milestone['开始'].strftime('%Y-%m-%d'), 
               ha='center', va='top', fontsize=11, style='italic')
    
    ax.set_title('供水配置研究项目 - 关键里程碑时间线（9个里程碑）', fontsize=18, pad=30, weight='bold')
    ax.set_xlabel('项目时间线', fontsize=14)
    
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))  # 每2周显示一次
    plt.xticks(fontsize=12, rotation=45, ha='right')
    
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "供水配置研究项目_里程碑时间线.png"), dpi=300, bbox_inches='tight')
    plt.show()

# --- 图表 4: 阶段分布饼图 ---
def plot_phase_distribution(df):
    # 计算各阶段的工期分布
    phase_duration = df[df['类型'] != '里程碑'].groupby('阶段')['工期'].sum()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 左图：工期分布饼图
    colors = [phase_colors[phase] for phase in phase_duration.index]
    wedges, texts, autotexts = ax1.pie(phase_duration.values, labels=phase_duration.index, 
                                      autopct='%1.1f%%', colors=colors, startangle=90,
                                      textprops={'fontsize': 12})
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax1.set_title('供水配置研究项目 - 各阶段工期分布', fontsize=16, weight='bold', pad=20)
    
    # 右图：任务数量分布条形图
    task_count = df[df['类型'] != '里程碑'].groupby('阶段').size()
    bars = ax2.bar(range(len(task_count)), task_count.values, 
                   color=[phase_colors[phase] for phase in task_count.index])
    
    ax2.set_title('供水配置研究项目 - 各阶段任务数量分布', fontsize=16, weight='bold', pad=20)
    ax2.set_xlabel('项目阶段', fontsize=12)
    ax2.set_ylabel('任务数量', fontsize=12)
    ax2.set_xticks(range(len(task_count)))
    ax2.set_xticklabels(task_count.index, rotation=45, ha='right')
    
    # 在条形图上添加数值
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom', fontsize=12, weight='bold')
    
    ax2.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "供水配置研究项目_阶段分布图.png"), dpi=300, bbox_inches='tight')
    plt.show()

# --- 图表 5: 任务类型热力图 ---
def plot_task_heatmap(df):
    # 创建一个以周为单位的时间热力图
    start_date = df['开始'].min()
    end_date = df['结束'].max()
    
    # 生成月时间序列
    months = pd.date_range(start=start_date, end=end_date, freq='MS')  # 每月第一天
    
    # 创建阶段 vs 月的矩阵
    phases = df['阶段'].unique()
    heatmap_data = np.zeros((len(phases), len(months)))
    
    for i, phase in enumerate(phases):
        phase_tasks = df[df['阶段'] == phase]
        for _, task in phase_tasks.iterrows():
            for j, month in enumerate(months):
                month_end = month + pd.DateOffset(months=1) - pd.DateOffset(days=1)
                if task['开始'] <= month_end and task['结束'] >= month:
                    heatmap_data[i, j] += 1
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto', interpolation='nearest')
    
    # 设置轴标签
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([month.strftime('%Y-%m') for month in months], rotation=45, ha='right')
    ax.set_yticks(range(len(phases)))
    ax.set_yticklabels(phases)
    
    # 添加数值标注
    for i in range(len(phases)):
        for j in range(len(months)):
            if heatmap_data[i, j] > 0:
                text = ax.text(j, i, f'{int(heatmap_data[i, j])}',
                             ha="center", va="center", color="black", fontweight='bold')
    
    ax.set_title('供水配置研究项目 - 任务密度热力图', fontsize=18, pad=20, weight='bold')
    ax.set_xlabel('项目月份', fontsize=14)
    ax.set_ylabel('项目阶段', fontsize=14)
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('同期任务数量', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "供水配置研究项目_任务密度热力图.png"), dpi=300, bbox_inches='tight')
    plt.show()

# --- 图表 6: 项目进度仪表盘 ---
def plot_project_dashboard(df):
    fig = plt.figure(figsize=(20, 12))
    
    # 创建子图布局
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
    
    # 1. 主甘特图
    ax1 = fig.add_subplot(gs[0:2, 0:3])
    main_tasks = df[df['类型'] == '工作任务']
    for i, (idx, task) in enumerate(main_tasks.iterrows()):
        ax1.barh(i, task['工期'], left=task['开始'], height=0.6, 
                color=task['阶段颜色'], alpha=0.8)
    ax1.set_title('主要任务进度', fontsize=14, weight='bold')
    ax1.set_yticks(range(len(main_tasks)))
    ax1.set_yticklabels([t.split('：')[0] for t in main_tasks['任务']], fontsize=10)
    ax1.invert_yaxis()
    
    # 2. 里程碑进度
    ax2 = fig.add_subplot(gs[0, 3])
    milestones = df[df['类型'] == '里程碑']
    milestone_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    ax2.barh(range(len(milestones)), [1]*len(milestones), 
             color=milestone_colors[:len(milestones)])
    ax2.set_title('里程碑状态', fontsize=14, weight='bold')
    ax2.set_yticks(range(len(milestones)))
    ax2.set_yticklabels([f'M{i+1}' for i in range(len(milestones))], fontsize=10)
    ax2.set_xlim(0, 1)
    ax2.set_xticks([])
    
    # 3. 阶段工期分布
    ax3 = fig.add_subplot(gs[1, 3])
    phase_duration = df[df['类型'] != '里程碑'].groupby('阶段')['工期'].sum()
    ax3.pie(phase_duration.values, labels=list(phase_duration.index), 
            autopct='%1.0f天', colors=[phase_colors[p] for p in phase_duration.index])
    ax3.set_title('阶段工期分布', fontsize=14, weight='bold')
    
    # 4. 项目统计信息
    ax4 = fig.add_subplot(gs[2, 0])
    total_tasks = len(df[df['类型'] != '里程碑'])
    total_days = (df['结束'].max() - df['开始'].min()).days
    ax4.text(0.5, 0.7, f'总任务数: {total_tasks}', ha='center', va='center', 
             fontsize=16, weight='bold', transform=ax4.transAxes)
    ax4.text(0.5, 0.3, f'项目周期: {total_days}天', ha='center', va='center', 
             fontsize=16, weight='bold', transform=ax4.transAxes)
    ax4.set_title('项目统计', fontsize=14, weight='bold')
    ax4.axis('off')
    
    # 5. 月度任务分布
    ax5 = fig.add_subplot(gs[2, 1:3])
    df['开始月份'] = df['开始'].dt.to_period('M')
    monthly_tasks = df[df['类型'] != '里程碑'].groupby('开始月份').size()
    ax5.bar(range(len(monthly_tasks)), monthly_tasks.values, color='#2196F3', alpha=0.7)
    ax5.set_title('月度任务启动数量', fontsize=14, weight='bold')
    ax5.set_xticks(range(len(monthly_tasks)))
    ax5.set_xticklabels([str(m) for m in monthly_tasks.index], rotation=45)
    ax5.set_ylabel('任务数量')
    
    # 6. 关键日期提醒
    ax6 = fig.add_subplot(gs[2, 3])
    key_dates = df[df['类型'] == '里程碑'][['任务', '开始']].copy()
    ax6.text(0.1, 0.9, '关键日期提醒:', fontsize=12, weight='bold', transform=ax6.transAxes)
    for i, (_, row) in enumerate(key_dates.iterrows()):
        ax6.text(0.1, 0.7-i*0.2, f"{row['开始'].strftime('%m-%d')}: M{i+1}", 
                fontsize=10, transform=ax6.transAxes)
    ax6.axis('off')
    
    plt.suptitle('供水配置研究项目 - 综合仪表盘', fontsize=20, weight='bold', y=0.98)
    plt.savefig(os.path.join(OUTPUT_DIR, "供水配置研究项目_综合仪表盘.png"), dpi=300, bbox_inches='tight')
    plt.show()

# --- 主执行函数 ---
if __name__ == '__main__':
    print("正在生成图表 1: 完整项目甘特图...")
    plot_complete_gantt(df)
    
    print("\n正在生成图表 2: 主要任务甘特图...")
    plot_main_tasks_gantt(df)
    
    print("\n正在生成图表 3: 里程碑时间线...")
    plot_milestones_timeline(df)
    
    print("\n正在生成图表 4: 阶段分布图...")
    plot_phase_distribution(df)
    
    print("\n正在生成图表 5: 任务密度热力图...")
    plot_task_heatmap(df)
    
    print("\n正在生成图表 6: 项目综合仪表盘...")
    plot_project_dashboard(df)
    
    print("\n所有图表生成完成！")
    print(f"项目总计：{len(df[df['类型'] != '里程碑'])}个任务，{len(df[df['类型'] == '里程碑'])}个里程碑")
    print(f"项目周期：{(df['结束'].max() - df['开始'].min()).days}天")



#!/bin/bash
# 水利工具环境配置脚本
#
# 使用方法：
#   source ~/useful_scripts/.assets/projects/setup.sh

# 获取脚本所在目录（projects 目录）
PROJECTS_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_HOME="$(cd "$PROJECTS_HOME/.." && pwd)"

# 设置环境变量
export PROJECTS_HOME
export ASSETS_HOME
# 兼容旧变量名
export HYDRAULIC_HOME="$PROJECTS_HOME"

# 添加公共库到 PYTHONPATH
export PYTHONPATH="$ASSETS_HOME/lib:$PYTHONPATH"

# 添加脚本目录到 PATH（这样可以直接执行脚本）
export PATH="$PROJECTS_HOME/qgis/pipeline:$PROJECTS_HOME/qgis/tools:$PROJECTS_HOME/risk_data:$PATH"

# 设置全省数据库路径（可通过环境变量覆盖）
export HYDRAULIC_DATA_BASE="${HYDRAULIC_DATA_BASE:-$HOME/Downloads/zdwp/数据与分析/全省水资源基础数据}"

# 设置模板路径
export HYDRAULIC_TEMPLATES="$PROJECTS_HOME/templates"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}✅ 水利工具环境已配置${NC}"
echo -e "   ${BLUE}PROJECTS_HOME:${NC} $PROJECTS_HOME"
echo -e "   ${BLUE}ASSETS_HOME:${NC} $ASSETS_HOME"
echo -e "   ${BLUE}数据库路径:${NC} $HYDRAULIC_DATA_BASE"
echo -e "   ${BLUE}模板路径:${NC} $HYDRAULIC_TEMPLATES"
echo ""
echo -e "${GREEN}💡 现在可以在任何目录直接执行脚本：${NC}"
echo "   3.03_risk_protection_dike_relation.py"
echo "   01_generate_river_points.py"
echo "   run_pipeline.sh"
echo ""
echo -e "${GREEN}📋 查看可用脚本：${NC}"
echo "   ls \$PROJECTS_HOME/risk_data/"
echo "   ls \$PROJECTS_HOME/qgis/pipeline/"

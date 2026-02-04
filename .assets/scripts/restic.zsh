# ============================================================
# 文件名称: restic.zsh
# 功能描述: Restic 备份环境变量配置
# 来源: ~/useful_scripts/system/backup/restic.zsh
# 创建日期: 2025-12-16
# 作者: 开发部
# ============================================================

export RESTIC_PASSWORD="${RESTIC_PASSWORD:-x}"
export RESTIC_REPO="${RESTIC_REPO:-$HOME/backups/restic-repo}"

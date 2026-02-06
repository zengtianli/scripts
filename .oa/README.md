# 开发部脚本看板 (.oa)

脚本管理系统，提供多维度筛选、双链关系等功能。

## 快速启动

```bash
cd /Users/tianli/useful_scripts/.oa

# 安装依赖（首次）
pnpm install

# 启动开发服务器
pnpm dev
```

访问 http://localhost:3000（如端口被占用会自动切换到 3001/3002）

## 功能

- **脚本看板**：按类型、功能、平台筛选脚本
- **搜索**：支持名称、标题、描述、标签搜索
- **脚本详情**：查看脚本信息、依赖模块、双链关系
- **双链**：
  - → Link Out：该脚本依赖的本地脚本
  - ← Link In：依赖该脚本的所有脚本
- **操作**：编辑脚本、打开目录、运行 CLI 脚本
- **AI 助手**：右下角聊天按钮，查询脚本相关问题

## 数据同步

当脚本有变动时，重新生成数据：

```bash
python3 scripts/sync-scripts.py
```

## 目录结构

```
.oa/
├── app/
│   ├── api/           # API 路由
│   │   ├── chat/      # AI 助手
│   │   ├── open-file/ # 打开脚本
│   │   ├── open-folder/ # 打开目录
│   │   └── run-script/  # 运行脚本
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx       # 主页面
├── data/
│   ├── scripts.json   # 脚本元数据（含双链）
│   └── dependencies.json
├── scripts/
│   └── sync-scripts.py  # 数据同步脚本
├── package.json
└── README.md
```

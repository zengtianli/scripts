# Streamlit 应用部署规范

> gh CLI + Streamlit Cloud 一键部署

## 标准目录结构

```
project/
├── .gitignore                # 忽略 __pycache__、output 等
├── .streamlit/
│   └── config.toml           # 主题配置
├── app.py                    # Streamlit 入口
├── run.py                    # 命令行入口（可选）
├── requirements.txt          # 依赖（精简版）
├── README.md
├── src/                      # 核心模块
│   ├── __init__.py
│   └── *.py
└── data/
    ├── sample/               # 示例输入数据
    └── output/               # 计算输出（.gitignore 忽略）
```

## app.py 标准功能

### 1. 数据来源选择

```python
data_source = st.radio(
    "选择数据来源",
    options=["sample", "upload"],
    format_func=lambda x: "使用示例数据" if x == "sample" else "上传自己的数据",
    horizontal=True
)
```

### 2. 上传 ZIP 功能

```python
uploaded_zip = st.file_uploader("选择 ZIP 文件", type=["zip"])

if uploaded_zip:
    import tempfile
    import zipfile
    
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(uploaded_zip, 'r') as zf:
        zf.extractall(temp_dir)
    data_path = Path(temp_dir)
```

### 3. 下载示例文件

```python
def create_sample_zip():
    """将示例数据打包成 ZIP"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in DATA_SAMPLE_DIR.glob('*.txt'):
            zf.write(file, file.name)
    zip_buffer.seek(0)
    return zip_buffer

st.download_button(
    "📥 下载示例文件",
    data=create_sample_zip(),
    file_name="示例数据.zip",
    mime="application/zip"
)
```

## 一键部署流程

### Step 1: 创建 .gitignore

```gitignore
__pycache__/
*.pyc
data/output/
*.tmp
.DS_Store
```

### Step 2: 创建 .streamlit/config.toml

```toml
[theme]
primaryColor = "#2e7d32"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f4f0"

[server]
maxUploadSize = 50
```

### Step 3: 精简 requirements.txt

```
pandas>=1.5.0
numpy>=1.21.0
streamlit>=1.28.0
openpyxl>=3.0.0
```

移除云端安装慢的大包：❌ netCDF4、matplotlib、scipy

### Step 4: 准备示例数据

```bash
mkdir -p data/sample data/output
# 只放必要的输入文件到 sample/
```

### Step 5: gh 创建仓库并推送

```bash
cd /path/to/project
git init
git add .
git commit -m "feat: xxx Web 界面"
gh repo create <repo-name> --public --source=. --remote=origin \
  --description "<描述>" --push
```

### Step 6: Streamlit Cloud 部署

1. 访问 https://share.streamlit.io/
2. 点击 "New app"
3. 选择仓库、分支、主文件 app.py
4. 点击 Deploy

## 部署平台对比

| 平台 | 命令/操作 | 费用 |
|------|----------|------|
| Streamlit Cloud | 连接 GitHub 仓库 | 免费（公开仓库） |
| Hugging Face | 创建 Space | 免费 |
| Railway | `railway up` | 免费额度 $5/月 |
| 自有服务器 | systemd + nginx | 服务器费用 |

## 注意事项

1. **示例数据**：`data/sample/` 只放输入文件，用户打开即可演示
2. **输出隔离**：计算输出写到 `data/output/`，被 .gitignore 忽略
3. **上传支持**：用 ZIP 上传，解压到临时目录
4. **下载示例**：打包 sample 目录供用户下载参考格式
5. **相对路径**：使用 `Path(__file__).parent`
6. **gh 登录**：首次需 `gh auth login`

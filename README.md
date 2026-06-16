![fastapi-awa-fuzzy-search-minecraft-backend](https://socialify.git.ci/VincentZyuApps/fastapi-awa-fuzzy-search-minecraft-backend/image?description=1&font=JetBrains+Mono&forks=1&issues=1&language=1&logo=https%3A%2F%2Fgithub.com%2FVincentZyuApps%2Ffastapi-awa-fuzzy-search-minecraft-backend%2Fblob%2Fmain%2Fassets%2F4icon.png%3Fraw%3Dtrue&name=1&owner=1&pulls=1&stargazers=1&theme=Auto)

<div align="center">
  <a href="https://github.com/VincentZyuApps/fastapi-awa-fuzzy-search-minecraft-backend"><img src="https://img.shields.io/badge/GitHub-VincentZyuApps/fastapi--awa--fuzzy--search--minecraft--backend-181717?style=flat-square&logo=github" alt="GitHub"></a>
  <a href="https://gitee.com/vincent-zyu/fastapi-awa-fuzzy-search-backend"><img src="https://img.shields.io/badge/Gitee-vincent--zyu/fastapi--awa--fuzzy--search--backend-C71D23?style=flat-square&logo=gitee" alt="Gitee"></a>
</div>

# 🎮 fastapi-awa-fuzzy-search-minecraft-backend

Minecraft 材质模糊搜索后端，支持 🌏 中英文混合搜索、🧠 语义匹配与 🔍 模糊匹配。

## 📁 项目结构

```
.
├── 📄 config.example.yaml     # 配置模板
├── 🔧 config.yaml             # 实际配置（gitignore）
├── 📦 src/
│   ├── __init__.py
│   ├── ⚙️  config.py          # YAML 配置加载
│   ├── 🔍 fuzzy_search.py     # 模糊 + 语义搜索核心
│   ├── 🛣️  routes.py          # API 路由 / 异常处理
│   └── 🚀 main.py             # App 工厂 / lifespan / 入口
├── 🖼️  static/                # 纹理文件（gitignore，需下载）
│   └── <version>/
│       └── textures/
│           ├── block/
│           ├── item/
│           └── ...
├── 🛠️  scripts/
│   ├── 📥 download_mc_textures.py  # 纹理下载脚本
│   └── 📖 readme.md
├── 📦 temp/                   # JAR 缓存（gitignore）
├── 🧪 test/
│   └── 🖥️  test_cuda.py
└── 🤖 models/                 # 模型缓存（gitignore）
```

## 🚀 快速开始

### 1️⃣ 创建并编辑配置

> [🛠️点我查看配置样例](./config.example.yaml)

```bash
# 📋 复制配置模板
cp config.example.yaml config.yaml
# ✏️ 按需编辑 config.yaml
```

### 2️⃣ 安装 uv

本项目推荐使用 [uv](https://github.com/astral-sh/uv) 管理 Python 环境和依赖，速度比 pip 快 10~100 倍。

```bash
# 🌍 官方安装
curl -LsSf https://astral.sh/uv/install.sh | sh
# 🇨🇳 国内镜像（Gitee，适用于无法访问 GitHub 的环境）
curl -LsSf https://gitee.com/wangnov/uv-custom/releases/download/latest/uv-installer.sh | sh
```

### 3️⃣ 编译依赖并安装

```bash
# 🐍 创建 Python 3.13 虚拟环境
uv venv --python 3.13
# 🔒 解析依赖并生成锁定文件，然后从txt安装依赖
uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt
# 📦 或者直接从txt安装所有依赖，跳过pip compile
uv pip install -r requirements.txt
```

> ⚠️ **GPU 兼容性说明**：不同 GPU 可能需要不同的 PyTorch 版本。
> 以作者的开发测试环境机器为例：
> - 🖥️ GPU: NVIDIA P104-100
> - 🐧 OS:   Debian 13 (Linux 6.12)
> - 📦 手动安装兼容版本：
> ```bash
> # 📦 从 PyTorch 官方源安装 CUDA 12.4 兼容版本
> uv pip install --find-links https://download.pytorch.org/whl/cu124 "torch>=2.5,<2.7"
> ```

### 4️⃣ 下载材质纹理

> [📖点我查看详细使用文档](./scripts/readme.md)

```bash
# 🎮 交互式选择版本（推荐，自动下载对应 JAR 并提取纹理）
uv run python scripts/download_mc_textures.py
# 📦 或指定下载某个版本
uv run python scripts/download_mc_textures.py --version 1.21.8
# 📂 或从本地已有 JAR 提取
uv run python scripts/download_mc_textures.py --jar /path/to/minecraft.jar --version 26.1.2
```

> 🌍 如需代理，`--proxy http://127.0.0.1:7890` 或参考下方代理设置。详见 [`scripts/readme.md`](scripts/readme.md)。

下载后 `config.yaml` 中的 `mc_version` 需与下载的版本文件夹名一致。

### 5️⃣ GPU 验证

```bash
# 🖥️ 检测 CUDA 是否可用
uv run python test/test_cuda.py
```

### 6️⃣ 启动服务

```bash
# 🚀 启动 FastAPI 后端服务
uv run python -m src.main
```

🌐 服务默认监听 `http://0.0.0.0:60615`，可在 `config.yaml` 中修改 `host` / `port`。

> ⚡ **模型下载说明**：首次启动时会从 HuggingFace 自动下载所需模型。在国内使用务必配置代理，否则下载会失败。

---

## 🌍 代理设置

HuggingFace 模型下载可能需要代理（国内环境）。按优先级高低提供三种方式：

| 优先级 | 方式 | 说明 |
|:---:|------|------|
| 🥇 | `--proxy` CLI 参数 | 🎯 命令行直接指定 |
| 🥈 | `config.yaml` | 💾 配置文件持久化 |
| 🥉 | 环境变量 | 🐚 `export` 到 shell |

### 🥇 方式一：`--proxy` CLI 参数（最高优先级）

```bash
# 🥇 最高优先级：通过 CLI 参数指定代理
uv run python -m src.main --proxy "http://127.0.0.1:7890"
```

### 🥈 方式二：`config.yaml`

```yaml
proxy: "http://127.0.0.1:7890"
```

### 🥉 方式三：环境变量

```bash
# 🥉 设置代理环境变量
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
# 🚀 启动服务
uv run python -m src.main
```

---

## 📡 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| 📖 `/docs` | GET | ReDoc 文档 |
| 🖼️ `/mcimg/{path}` | GET | 获取材质图片 |
| 📂 `/ls` | GET | 目录列表（ascending / descending / random） |
| 🌳 `/tree` | GET | 递归文件列表 |
| 🔎 `/fuzzy_guess` | GET | 模糊搜索（keyword + limit） |

### 📝 示例请求

```bash
# 🔎 模糊搜索 — 根据关键词搜索材质文件
curl "http://localhost:60615/fuzzy_guess?keyword=stone&limit=5"

# 📂 目录列表 — 列出指定目录下的文件与子目录
curl "http://localhost:60615/ls?dir_path=block&mode=ascending&limit=10"

# 🖼️ 获取图片 — 下载指定路径的材质图片
curl "http://localhost:60615/mcimg/block/stone.png"
```

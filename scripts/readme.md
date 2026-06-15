# 🛠️ Scripts

## 📥 download_mc_textures.py

从 Minecraft JAR 或 CDN 下载纹理文件到 `static/<version>/textures/`。

### 🚀 基础用法

```bash
cd fastapi-awa-fuzzy-search-backend
# 🎮 交互式选择版本（推荐）
uv run python scripts/download_mc_textures.py
# 📋 仅列出可用版本（不下载）
uv run python scripts/download_mc_textures.py --list
# 📦 下载指定正式版
uv run python scripts/download_mc_textures.py --version 1.21.8
# 🧪 下载指定快照版
uv run python scripts/download_mc_textures.py --version 26.2-rc-2
# 📂 从本地 JAR 提取（自定义文件夹名）
uv run python scripts/download_mc_textures.py --jar /path/to/minecraft.jar --version 26.1.2
```

### 🌍 代理设置

优先级：`--proxy` > `config.yaml` > 环境变量

```bash
# 🥇 CLI 参数（最高优先级）
uv run python scripts/download_mc_textures.py --proxy http://127.0.0.1:7890 --version 1.21.8
```

```yaml
# 🥈 config.yaml 配置
proxy: "http://127.0.0.1:7890"
```

```bash
# 🥉 环境变量
export HTTP_PROXY=http://127.0.0.1:7890
uv run python scripts/download_mc_textures.py --version 1.21.8
```

### 📁 输出结构

```
static/
├── 26.1.2/            
│   └── textures/
│       ├── block/
│       ├── entity/
│       └── ...
├── 1.21.8/             
│   └── textures/
│       └── ...
└── <version>/         
```

### 🔗 下载源

| 用途 | 源 |
|------|----|
| 🌐 版本清单 | `piston-meta.mojang.com` (Mojang 官方) |
| 🇨🇳 版本清单镜像 | `bmclapi2.bangbang93.com` (BMCLAPI) |
| 📦 JAR 下载 | 优先 BMCLAPI 镜像，失败自动回退官方 |
| 🔧 提取方式 | `zipfile` 标准库，无需 7z |

### ⚙️ 切换版本

下载后修改 `config.yaml` 中的 `mc_version` 即可：

```yaml
mc_version: "21.6.2"   # 切换到已下载的版本
```

重启 FastAPI 服务后生效。

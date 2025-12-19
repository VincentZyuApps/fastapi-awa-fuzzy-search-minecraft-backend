```bash
pip freeze > requirements.txt
```

## venv
```bash
python -m venv venv # Python 3.12.5
.\venv\Scripts\activate.bat # win
source ./venv/bin/activate # linux
pip freeze > requirements.txt
pip install -r requirements.txt
uvicorn main:app --reload --port 8989 --host 0.0.0.0
proxychains4 python -m uvicorn main:app --reload --port 8989 --host 0.0.0.0
```

## uv
```bash
pipx install uv
uv venv --python 3.12.5
# 虽然 uv 简化了许多步骤，但在某些情况下你仍然需要手动激活环境，例如当你想要运行一个不带 uv 命令的脚本时。激活命令与你之前使用的相同：
# .\.venv\Scripts\activate.bat
# source ./.venv/bin/activate
uv pip compile requirements.in -o requirements.txt
uv pip install -r requirements.txt
uv pip sync requirements.txt
uv run python test_pytorch.py
proxychains4 /root/.local/bin/uv run uvicorn main:app --reload --port 8989 --host 0.0.0.0
proxychains4 /root/.local/bin/uv run uvicorn main:app --port 8989 --host 0.0.0.0
```

## git
```bash
git ls-files --others --ignored --exclude-standard
git ls-files --others --ignored --exclude-standard | grep -v ".venv"
```

## dotenv
```dotenv
DEVICE=cuda
HOST=0.0.0.0
PORT=8830

MC_VERSION=1.21.8
```

## static tree
```bash

root@pop-os:/home/zyu/SSoftwareFiles/fastapi/fastapi-awa-fuzzy-search-backend/static# tree -L 2
.
├── mc1.21.8_textures.zip
└── textures
    ├── block
    ├── colormap
    ├── effect
    ├── entity
    ├── environment
    ├── font
    ├── gui
    ├── item
    ├── map
    ├── misc
    ├── mob_effect
    ├── painting
    ├── particle
    └── trims

15 directories, 1 file
root@pop-os:/home/zyu/SSoftwareFiles/fastapi/fastapi-awa-fuzzy-search-backend/static# 
```

### 一些todo:

# todo 缓存，缩略图

"""
添加缓存机制

python

from fastapi.middleware.http import HTTPMiddleware
# 添加Cache-Control头（示例缓存1小时）
app.add_middleware(HTTPMiddleware, headers={"Cache-Control": "public, max-age=3600"})

    ​实现缩略图生成 


    可添加图像处理接口：

python

@app.get("/thumbnail/{path:path}")
async def get_thumbnail(path: str, size: int = 128):
    # 使用PIL库生成缩略图
    from PIL import Image
    # ... 图像处理逻辑 ...
"""

"""
三、性能优化策略

    ​向量预计算

    python

    # 启动时预计算所有文件向量
    self.file_vectors = self._precompute_vectors()

    ​异步翻译处理

    python

    # 使用异步线程池避免阻塞
    await asyncio.to_thread(self.translator_zh2en, ...)

    ​缓存机制

    python

    from functools import lru_cache

    @lru_cache(maxsize=1000)
    def cached_translate(text: str):
        return self.translator(text)

    ​GPU加速

    python

    # 在初始化时指定设备
    self.semantic_model = SentenceTransformer(..., device='cuda')

五、测试案例验证
测试请求：

bash

GET /fuzzy_guess?keyword=stome&limit=3

预期响应：

json

{
  "results": [
    {"name": "textures/block/stone.png", "score": "0.92"},
    {"name": "textures/item/stone_axe.png", "score": "0.85"},
    {"name": "textures/block/cobblestone.png", "score": "0.78"}
  ]
}

​六、扩展建议

    ​多语言映射表增强

    python

    # 添加游戏术语专用词典
    CUSTOM_MAP = {
        "铁铲": ["shovel", "spade"],
        "红石块": ["redstone_block"]
    }

    ​混合检索模式

    python

    # 结合Elasticsearch实现关键词检索
    def hybrid_search():
        es_results = elastic_search(keyword)
        semantic_results = semantic_search(keyword)
        return merge_results(es_results, semantic_results)

    ​动态权重调整

    python

    # 根据输入类型自动调整权重
    if keyword.isalpha():
        weights = (0.4, 0.6)  # 西文字符加强模糊匹配
    else:
        weights = (0.6, 0.4)  # 中文加强语义匹配

该方案完整实现了：

    中英文自动翻译（基于网页2）
    语义+模糊混合匹配（网页1/5）
    预加载机制提升性能
    错误处理与日志追踪

部署时需注意模型下载：

bash

HF_ENDPOINT=https://hf-mirror.com huggingface-cli download --resume-download sentence-transformers/para
"""

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

## static dir tree
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

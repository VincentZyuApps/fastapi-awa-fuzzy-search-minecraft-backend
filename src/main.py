import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.fuzzy_search import FuzzySearch
from src.routes import router

from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
BASE_DIR = PROJECT_ROOT / "static" / settings.mc_version / "textures"

if settings.proxy:
    os.environ["HTTP_PROXY"] = settings.proxy
    os.environ["HTTPS_PROXY"] = settings.proxy

if settings.models_cache_dir:
    cache_path = Path(settings.models_cache_dir)
    if not cache_path.is_absolute():
        cache_path = PROJECT_ROOT / cache_path
    cache_path.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    file_list = []
    for root, _, files in os.walk(BASE_DIR):
        rel_root = Path(root).relative_to(BASE_DIR)
        file_list.extend(str(rel_root / f) for f in files)

    fuzzy_searcher = FuzzySearch(file_list, device=settings.device)
    await fuzzy_searcher.init_models()

    app.state.fuzzy_searcher = fuzzy_searcher
    app.state.base_dir = BASE_DIR
    yield


app = FastAPI(lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=str(PROJECT_ROOT / "static")),
    name="static",
)

app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未捕获异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--proxy", type=str, default=None,
        help="代理地址，优先级高于 config.yaml 和环境变量",
    )
    args, _ = parser.parse_known_args()

    if args.proxy:
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )

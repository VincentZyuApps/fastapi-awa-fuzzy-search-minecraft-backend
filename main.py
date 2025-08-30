# main.py
import random
from typing import Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
import logging
from pydantic import BaseModel

from fuzzy_search import FuzzySearch
from config_manager import settings


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """生命周期管理：预加载文件列表和模型"""
    file_list = []
    # 获取所有文件路径
    for root, _, files in os.walk(BASE_DIR):
        rel_root = Path(root).relative_to(BASE_DIR)
        file_list.extend(str(rel_root / f) for f in files)

    # 传递设备设置给 FuzzySearch 实例
    fuzzy_searcher: FuzzySearch = FuzzySearch(file_list, device=settings.DEVICE)
    # 初始化搜索模块
    await fuzzy_searcher.init_models()
    fastapi_app.state.fuzzy_searcher = fuzzy_searcher
    yield


app = FastAPI(
    lifespan=lifespan
)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ResponseModel(BaseModel):
    code: int
    message: str
    data: dict


# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定义材质根目录
BASE_DIR = Path(__file__).parent / "static" / "textures"


# -------------------------- 统一异常处理 --------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未捕获异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None}
    )


# -------------------------- 路径安全验证工具 --------------------------
def safe_path_join(base: Path, path: str) -> Path:
    """安全路径拼接函数（防路径遍历攻击）"""
    try:
        resolved_path = (base / path).resolve()
        if not resolved_path.is_relative_to(base.resolve()):
            raise ValueError("路径越界")
        return resolved_path
    except (ValueError, FileNotFoundError) as e:
        logger.warning(f"非法路径访问尝试: {base}/{path}")
        raise HTTPException(status_code=403, detail=str(e))


# -------------------------- API 端点 --------------------------

@app.get("/docs", include_in_schema=False)
async def redoc_docs():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Minecraft Texture API Documentation",
    )


@app.get("/mcimg/{path:path}")
async def get_minecraft_image(path: str):
    """获取材质图片端点"""
    try:
        full_path = safe_path_join(BASE_DIR, path)

        if not full_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(full_path, headers={"Cache-Control": "max-age=3600"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片获取失败: {str(e)}")
        raise HTTPException(status_code=500, detail="文件读取失败")


@app.get("/ls")
async def list_directory(dir_path: str = None, limit: int = None, mode: str = "ascending"):
    """目录列表查询端点"""
    try:
        target_dir = safe_path_join(BASE_DIR, dir_path) if dir_path else BASE_DIR

        # 增强型路径验证
        if not target_dir.exists():
            raise HTTPException(status_code=404, detail="路径不存在")
        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="请求路径不是目录")

        # 构建目录列表
        items = []
        for item in os.listdir(target_dir):
            item_path = target_dir / item
            items.append({
                "name": item,
                "type": "directory" if item_path.is_dir() else "file",
                "size": item_path.stat().st_size,
                "modified": item_path.stat().st_mtime,
                "path": str(item_path.relative_to(BASE_DIR))
            })

        # 根据 mode 参数进行排序
        if mode == "ascending":
            items.sort(key=lambda x: x["name"])  # 升序排序
        elif mode == "descending":
            items.sort(key=lambda x: x["name"], reverse=True)  # 降序排序
        elif mode == "random":
            random.shuffle(items)  # 随机排序
        else:
            raise HTTPException(status_code=400, detail="无效的 mode 参数")

        # 应用 limit 约束
        if limit is not None:
            items = items[:limit]

        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": {
                "current_path": str(target_dir.relative_to(BASE_DIR)),
                "items": items
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"目录列表获取失败: {str(e)}")
        raise HTTPException(status_code=500, detail="目录读取失败")


@app.get("/tree")
async def list_tree(dir_path: str = None, limit: int = None, mode: str = "ascending"):
    """递归列出所有文件的扁平化结构"""
    try:
        # 安全路径验证（复用现有安全函数）
        target_dir = safe_path_join(BASE_DIR, dir_path) if dir_path else BASE_DIR

        # 参数有效性验证
        if not target_dir.exists():
            raise HTTPException(404, "路径不存在")
        if not target_dir.is_dir():
            raise HTTPException(400, "请求路径不是目录")
        if limit is not None and limit < 0:
            raise HTTPException(400, "限制数必须大于等于0")
        if mode not in ["ascending", "descending", "random"]:
            raise HTTPException(status_code=400, detail="无效的 mode 参数")

        # 递归收集文件路径
        file_list = []
        for root, _, files in os.walk(target_dir):
            rel_root = Path(root).relative_to(BASE_DIR)
            for file in sorted(files):
                file_path = rel_root / file
                file_list.append(str(file_path))

        # 根据 mode 参数进行排序
        if mode == "ascending":
            file_list.sort()  # 升序排序
        elif mode == "descending":
            file_list.sort(reverse=True)  # 降序排序
        elif mode == "random":
            random.shuffle(file_list)  # 随机排序

        # 应用限制参数
        if limit is not None:
            file_list = file_list[:limit]

        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": {
                "current_root": str(target_dir.relative_to(BASE_DIR)),
                "total_files": len(file_list),
                "files": file_list
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"目录树遍历失败: {str(e)}")
        raise HTTPException(500, "目录遍历失败")


@app.get("/fuzzy_guess")
async def fuzzy_search_endpoint(
        keyword: str,
        limit: int = Query(10, ge=1, le=300)
):
    """模糊搜索端点"""
    searcher = app.state.fuzzy_searcher

    try:
        # 执行搜索操作
        search_results = await searcher.search(keyword, limit)

        # 返回包裹 code 和 message 的格式
        return ResponseModel(
            code=200,
            message="搜索成功",
            data={"results": search_results}
        )

    except Exception as e:
        # 捕获异常并返回错误信息
        return ResponseModel(
            code=500,
            message=f"搜索失败: {str(e)}",
            data={}
        )
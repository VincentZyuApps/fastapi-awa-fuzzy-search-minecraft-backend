import os
import random
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ResponseModel(BaseModel):
    code: int
    message: str
    data: dict


def safe_path_join(base: Path, path: str) -> Path:
    try:
        resolved_path = (base / path).resolve()
        if not resolved_path.is_relative_to(base.resolve()):
            raise ValueError("路径越界")
        return resolved_path
    except (ValueError, FileNotFoundError) as e:
        logger.warning(f"非法路径访问尝试: {base}/{path}")
        raise HTTPException(status_code=403, detail=str(e))


# -------------------------- 异常处理 --------------------------

@router.get("/docs", include_in_schema=False)
async def redoc_docs():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Minecraft Texture API Documentation",
    )


@router.get("/mcimg/{path:path}")
async def get_minecraft_image(path: str, request: Request):
    base_dir: Path = request.app.state.base_dir
    try:
        full_path = safe_path_join(base_dir, path)
        if not full_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(full_path, headers={"Cache-Control": "max-age=3600"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片获取失败: {str(e)}")
        raise HTTPException(status_code=500, detail="文件读取失败")


@router.get("/ls")
async def list_directory(
    request: Request,
    dir_path: str = None,
    limit: int = None,
    mode: str = "ascending",
):
    base_dir: Path = request.app.state.base_dir
    try:
        target_dir = safe_path_join(base_dir, dir_path) if dir_path else base_dir

        if not target_dir.exists():
            raise HTTPException(status_code=404, detail="路径不存在")
        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="请求路径不是目录")

        if mode not in ("ascending", "descending", "random"):
            raise HTTPException(status_code=400, detail="无效的 mode 参数")

        items = []
        for item in os.listdir(target_dir):
            item_path = target_dir / item
            items.append({
                "name": item,
                "type": "directory" if item_path.is_dir() else "file",
                "size": item_path.stat().st_size,
                "modified": item_path.stat().st_mtime,
                "path": str(item_path.relative_to(base_dir)),
            })

        if mode == "ascending":
            items.sort(key=lambda x: x["name"])
        elif mode == "descending":
            items.sort(key=lambda x: x["name"], reverse=True)
        elif mode == "random":
            random.shuffle(items)

        if limit is not None:
            items = items[:limit]

        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": {
                "current_path": str(target_dir.relative_to(base_dir)),
                "items": items,
            },
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"目录列表获取失败: {str(e)}")
        raise HTTPException(status_code=500, detail="目录读取失败")


@router.get("/tree")
async def list_tree(
    request: Request,
    dir_path: str = None,
    limit: int = None,
    mode: str = "ascending",
):
    base_dir: Path = request.app.state.base_dir
    try:
        target_dir = safe_path_join(base_dir, dir_path) if dir_path else base_dir

        if not target_dir.exists():
            raise HTTPException(404, "路径不存在")
        if not target_dir.is_dir():
            raise HTTPException(400, "请求路径不是目录")
        if limit is not None and limit < 0:
            raise HTTPException(400, "限制数必须大于等于0")
        if mode not in ("ascending", "descending", "random"):
            raise HTTPException(status_code=400, detail="无效的 mode 参数")

        file_list = []
        for root, _, files in os.walk(target_dir):
            rel_root = Path(root).relative_to(base_dir)
            for file in sorted(files):
                file_path = rel_root / file
                file_list.append(str(file_path))

        if mode == "ascending":
            file_list.sort()
        elif mode == "descending":
            file_list.sort(reverse=True)
        elif mode == "random":
            random.shuffle(file_list)

        if limit is not None:
            file_list = file_list[:limit]

        return JSONResponse({
            "code": 200,
            "message": "success",
            "data": {
                "current_root": str(target_dir.relative_to(base_dir)),
                "total_files": len(file_list),
                "files": file_list,
            },
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"目录树遍历失败: {str(e)}")
        raise HTTPException(500, "目录遍历失败")


@router.get("/fuzzy_guess")
async def fuzzy_search_endpoint(
    request: Request,
    keyword: str,
    limit: int = Query(10, ge=1, le=300),
):
    searcher = request.app.state.fuzzy_searcher

    try:
        search_results = await searcher.search(keyword, limit)
        return ResponseModel(
            code=200,
            message="搜索成功",
            data={"results": search_results},
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"搜索失败: {str(e)}",
            data={},
        )

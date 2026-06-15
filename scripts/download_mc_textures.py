#!/usr/bin/env python3
"""
Minecraft 纹理下载脚本
从本地 JAR 或 CDN 获取 textures 到 static/<version>/textures/

用法:
  python scripts/download_mc_textures.py                    # 交互式选择版本
  python scripts/download_mc_textures.py --version 1.21.8   # 下载指定版本
  python scripts/download_mc_textures.py --jar /path/x.jar  # 从本地 JAR 提取
  python scripts/download_mc_textures.py --jar x.jar --version 26.1.2  # 指定文件夹名
"""

import argparse
import json
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    TaskID,
)
from rich.table import Table

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "temp"

# ---------- CDN 源 ----------

MANIFEST_URLS = [
    "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
    "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json",
]

BMCLAPI_CLIENT_JAR = "https://bmclapi2.bangbang93.com/version/{version}/client"


# ---------- 代理 ----------

def resolve_proxy(cli_proxy: str | None) -> str | None:
    if cli_proxy:
        return cli_proxy
    config_path = PROJECT_ROOT / "config.yaml"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if data.get("proxy"):
            return data["proxy"]
    for key in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        if os.environ.get(key):
            return os.environ[key]
    return None


def setup_proxy(proxy: str | None):
    if not proxy:
        return
    handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    urllib.request.install_opener(urllib.request.build_opener(handler))
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy
    console.print(f"  [dim]🌍 代理: {proxy}[/dim]")


# ---------- HTTP ----------

def _http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "awa-mc-tex/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _http_get_json(url: str) -> dict:
    return json.loads(_http_get(url))


# ---------- 版本清单 ----------

def fetch_version_manifest() -> dict:
    for url in MANIFEST_URLS:
        host = urlparse(url).hostname or url
        source = "镜像" if "bmclapi" in host else "官方"
        try:
            console.print(f"  [dim]🔗 版本清单: {host} ({source})[/dim]")
            return _http_get_json(url)
        except (URLError, OSError) as e:
            console.print(f"  [yellow]⚠  {host}: {e}[/yellow]")
    raise RuntimeError("所有源均不可用，请检查网络或代理设置")


def _download_with_progress(url: str, desc: str) -> tuple[bytes, int]:
    """带进度条的 HTTP 下载"""
    req = urllib.request.Request(url, headers={"User-Agent": "awa-mc-tex/1.0"})
    resp = urllib.request.urlopen(req, timeout=120)

    total = int(resp.headers.get("Content-Length", 0))
    chunks: list[bytes] = []

    with Progress(
        TextColumn(f"  [bold white]{desc}[/bold white]"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        transient=False,
    ) as progress:
        task = progress.add_task("下载中", total=total or None)
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            chunks.append(chunk)  # type: ignore[arg-type]
            progress.advance(task, len(chunk))
    data = b"".join(chunks)
    return data, len(data)


# ---------- JAR 下载 ----------

def download_jar(version: str, manifest: dict | None = None) -> tuple[Path, str]:
    if manifest is None:
        manifest = fetch_version_manifest()
    versions = {v["id"]: v for v in manifest["versions"]}

    if version not in versions:
        similar = sorted(
            [v for v in versions if version.lower() in v.lower()],
            key=lambda v: list(versions).index(v),
        )[:8]
        hint = f"  类似版本: {', '.join(similar)}" if similar else ""
        raise ValueError(f"版本 '{version}' 不在清单中。\n{hint}")

    version_url = versions[version]["url"]
    vdata = _http_get_json(version_url)
    actual_id = vdata.get("id", version)

    official_url = vdata.get("downloads", {}).get("client", {}).get("url", "")
    mirror_url = BMCLAPI_CLIENT_JAR.format(version=version)

    mirror_host = urlparse(mirror_url).hostname or "bmclapi"
    official_host = urlparse(official_url).hostname or "mojang"

    TEMP_DIR.mkdir(exist_ok=True)
    jar_path = TEMP_DIR / f"{actual_id}.jar"

    try:
        data, _ = _download_with_progress(mirror_url, f"📥 镜像: {mirror_host}")
    except (URLError, OSError):
        console.print(f"  [yellow]⚠  镜像不可用，回退官方源[/yellow]")
        data, _ = _download_with_progress(official_url, f"📥 官方: {official_host}")

    jar_path.write_bytes(data)

    size_mb = len(data) / 1024 / 1024
    console.print(f"  [green]✓ 已保存:[/green] [dim]{jar_path}[/dim] ([cyan]{size_mb:.1f} MB[/cyan])")
    return jar_path, actual_id


# ---------- 纹理提取 ----------

def extract_textures(jar_path: Path, output_dir: Path) -> int:
    prefix = "assets/minecraft/textures/"
    with zipfile.ZipFile(jar_path) as zf:
        names = [n for n in zf.namelist() if n.startswith(prefix) and not n.endswith("/")]
        with Progress(
            TextColumn("  [bold white]提取纹理[/bold white]"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            transient=False,
        ) as progress:
            task = progress.add_task("", total=len(names))
            for name in names:
                rel = name[len(prefix):]
                target = output_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(name))
                progress.advance(task)
    return len(names)


# ---------- 交互式版本选择 ----------

def interactive_pick_version(manifest: dict) -> str:
    versions = manifest["versions"]
    latest = manifest.get("latest", {})
    latest_release = latest.get("release", "")
    latest_snapshot = latest.get("snapshot", "")

    releases = [v for v in versions if v["type"] == "release"]
    snapshots = [v for v in versions if v["type"] == "snapshot"]

    console.print()
    console.print(Panel(
        "[bold cyan]Minecraft 版本选择[/bold cyan]",
        border_style="cyan",
        width=52,
    ))
    console.print(f"  [bold]最新正式版:[/bold] [green]{latest_release}[/green]")
    console.print(f"  [bold]最新快照版:[/bold] [yellow]{latest_snapshot}[/yellow]")

    def _show_table(title: str, items: list, style: str, count: int = 15):
        table = Table(title=title, title_style=f"bold {style}", show_header=True, box=None)
        table.add_column("#", style="dim", width=4)
        table.add_column("版本", style=style)
        table.add_column("日期", style="dim")
        for i, v in enumerate(items[:count], 1):
            table.add_row(str(i), v["id"], v["releaseTime"][:10])
        console.print(table)

    _show_table("正式版", releases, "green")
    _show_table("快照版", snapshots, "yellow")

    console.print()
    console.print("  [dim]输入版本号 (例: 1.21.8)，直接回车使用最新正式版[/dim]")
    console.print("  [dim]Ctrl+C 退出[/dim]")

    try:
        choice = console.input("  [bold]版本号: [/bold]").strip()
    except (KeyboardInterrupt, EOFError):
        console.print()
        sys.exit(0)
    return choice or latest_release


def show_versions(manifest: dict):
    versions = manifest["versions"]
    latest = manifest.get("latest", {})
    latest_release = latest.get("release", "")
    latest_snapshot = latest.get("snapshot", "")

    releases = [v for v in versions if v["type"] == "release"]
    snapshots = [v for v in versions if v["type"] == "snapshot"]

    console.print(f"  [bold]最新正式版:[/bold] [green]{latest_release}[/green]")
    console.print(f"  [bold]最新快照版:[/bold] [yellow]{latest_snapshot}[/yellow]")

    def _print_table(title: str, items: list, style: str, count: int = 15):
        table = Table(title=title, title_style=f"bold {style}", show_header=True, box=None)
        table.add_column("#", style="dim", width=4)
        table.add_column("版本", style=style)
        table.add_column("日期", style="dim")
        for i, v in enumerate(items[:count], 1):
            table.add_row(str(i), v["id"], v["releaseTime"][:10])
        console.print(table)

    _print_table("正式版", releases, "green")
    _print_table("快照版", snapshots, "yellow")


# ---------- 主入口 ----------

def main():
    parser = argparse.ArgumentParser(
        description="Minecraft 纹理下载工具 — 从 JAR 或 CDN 获取 textures",
    )
    parser.add_argument("--jar", help="本地 JAR 文件路径")
    parser.add_argument("--version", "-v", help="版本号 (如 1.21.8)")
    parser.add_argument("--proxy", help="代理地址 (例: http://127.0.0.1:7890)")
    parser.add_argument("--output-dir", default="static", help="输出根目录 (默认 static/)")
    parser.add_argument("--list", action="store_true", help="仅列出可用版本")
    args = parser.parse_args()

    proxy = resolve_proxy(args.proxy)
    setup_proxy(proxy)

    output_base = PROJECT_ROOT / args.output_dir

    console.print()
    console.print(Panel(
        "[bold cyan]Minecraft Texture Downloader[/bold cyan]",
        border_style="cyan",
        width=52,
    ))

    # --list: 仅列版本
    if args.list:
        manifest = fetch_version_manifest()
        show_versions(manifest)
        return

    # --jar 模式
    if args.jar:
        jar_path = Path(args.jar).resolve()
        if not jar_path.exists():
            console.print(f"  [red]✘ 文件不存在: {jar_path}[/red]")
            sys.exit(1)
        version_name = args.version or jar_path.stem
    else:
        # --version 或交互模式
        manifest = fetch_version_manifest()
        version = args.version or interactive_pick_version(manifest)
        if not version:
            console.print("  [red]✘ 未选择版本[/red]")
            sys.exit(1)
        jar_path, actual_version = download_jar(version, manifest)
        version_name = actual_version

    textures_dir = output_base / version_name / "textures"
    if textures_dir.exists():
        console.print(f"  [yellow]⚠  目录已存在: {textures_dir}[/yellow]")
        if console.input("  [bold]覆盖? (y/N): [/bold]").strip().lower() != "y":
            console.print("  [dim]已取消[/dim]")
            return
        shutil.rmtree(textures_dir)

    count = extract_textures(jar_path, textures_dir)

    console.print()
    console.print(Panel(
        f"[bold green]完成![/bold green]\n"
        f"版本: [cyan]{version_name}[/cyan]  |  纹理: [cyan]{count}[/cyan]\n"
        f"路径: [dim]{textures_dir}[/dim]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()

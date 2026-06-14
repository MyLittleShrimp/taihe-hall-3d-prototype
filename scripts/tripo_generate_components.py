import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from tripo3d import TripoClient

from tripo_ab_test import enable_aiohttp_env_proxy


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "assets" / "models" / "tripo" / "taihe-components"

COMPONENTS = [
    {
        "id": "overview",
        "name": "整体建筑",
        "image": ROOT / "assets" / "ai" / "illustration-overview.png",
    },
    {
        "id": "roof",
        "name": "屋顶系统",
        "image": ROOT / "assets" / "ai" / "illustration-roof.png",
    },
    {
        "id": "dougong",
        "name": "斗拱层",
        "image": ROOT / "assets" / "ai" / "illustration-dougong.png",
        "reuse_model": ROOT
        / "assets"
        / "models"
        / "tripo"
        / "ab-dougong"
        / "standard"
        / "a2f6df10-a4ef-439e-9eb3-5e43ec1bf9a7_pbr.glb",
        "reuse_preview": ROOT
        / "assets"
        / "models"
        / "tripo"
        / "ab-dougong"
        / "standard"
        / "a2f6df10-a4ef-439e-9eb3-5e43ec1bf9a7_rendered.webp",
        "reuse_task_id": "a2f6df10-a4ef-439e-9eb3-5e43ec1bf9a7",
    },
    {
        "id": "columns",
        "name": "柱梁系统",
        "image": ROOT / "assets" / "ai" / "illustration-columns.png",
    },
    {
        "id": "platform",
        "name": "台基系统",
        "image": ROOT / "assets" / "ai" / "illustration-platform.png",
    },
    {
        "id": "decor",
        "name": "脊兽装饰",
        "image": ROOT / "assets" / "ai" / "illustration-decor.png",
    },
    {
        "id": "painting",
        "name": "彩画纹样",
        "image": ROOT / "assets" / "ai" / "illustration-painting.png",
    },
]


def setup_env():
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("TRIPO_API_KEY")
    if not api_key:
        raise SystemExit("TRIPO_API_KEY is missing. Put it in .env first.")
    proxy = os.environ.get("TRIPO_PROXY")
    if proxy:
        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy
        enable_aiohttp_env_proxy()
    return api_key, proxy


def download_url(url: str, path: Path, proxy: str | None) -> int:
    proxies = {"http": proxy, "https": proxy} if proxy else None
    tmp = path.with_suffix(path.suffix + ".download")
    with requests.get(url, stream=True, timeout=120, proxies=proxies) as response:
        response.raise_for_status()
        expected = int(response.headers.get("content-length", "0") or "0")
        got = 0
        with tmp.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
                    got += len(chunk)
    if expected and got != expected:
        raise RuntimeError(f"incomplete download for {path.name}: expected {expected}, got {got}")
    tmp.replace(path)
    return got


def file_size_mb(path: Path) -> float:
    return round(path.stat().st_size / 1024 / 1024, 2)


def balance_to_dict(balance):
    return {
        "balance": getattr(balance, "balance", None),
        "frozen": getattr(balance, "frozen", None),
    }


async def generate_component(client, component, proxy, force=False):
    component_dir = OUT_ROOT / component["id"]
    component_dir.mkdir(parents=True, exist_ok=True)
    model_path = component_dir / f"{component['id']}_standard.glb"
    preview_path = component_dir / f"{component['id']}_standard.webp"

    if component.get("reuse_model") and not force:
        if not model_path.exists():
            model_path.write_bytes(component["reuse_model"].read_bytes())
        if component.get("reuse_preview") and not preview_path.exists():
            preview_path.write_bytes(component["reuse_preview"].read_bytes())
        return {
            "id": component["id"],
            "name": component["name"],
            "status": "reused",
            "task_id": component.get("reuse_task_id"),
            "source_image": str(component["image"].relative_to(ROOT)),
            "pbr_model": str(model_path.relative_to(ROOT)).replace("\\", "/"),
            "rendered_image": str(preview_path.relative_to(ROOT)).replace("\\", "/"),
            "file_size_mb": file_size_mb(model_path),
        }

    if model_path.exists() and preview_path.exists() and not force:
        return {
            "id": component["id"],
            "name": component["name"],
            "status": "exists",
            "source_image": str(component["image"].relative_to(ROOT)),
            "pbr_model": str(model_path.relative_to(ROOT)).replace("\\", "/"),
            "rendered_image": str(preview_path.relative_to(ROOT)).replace("\\", "/"),
            "file_size_mb": file_size_mb(model_path),
        }

    started = time.monotonic()
    task_id = await client.image_to_model(
        str(component["image"]),
        model_version="v3.1-20260211",
        texture=True,
        pbr=True,
        texture_quality="standard",
        geometry_quality="standard",
        texture_alignment="original_image",
        orientation="align_image",
        auto_size=True,
        quad=False,
        compress=False,
        generate_parts=False,
        smart_low_poly=False,
        enable_image_autofix=True,
        export_uv=True,
    )
    print(f"{component['id']}: submitted {task_id}", flush=True)
    task = await client.wait_for_task(task_id, polling_interval=5, timeout=1800, verbose=True)
    elapsed = round(time.monotonic() - started)

    result = {
        "id": component["id"],
        "name": component["name"],
        "status": str(task.status),
        "task_id": task_id,
        "source_image": str(component["image"].relative_to(ROOT)),
        "generation_seconds": elapsed,
        "error_code": task.error_code,
        "error_msg": task.error_msg,
    }
    if not str(task.status).upper().endswith("SUCCESS"):
        return result

    model_url = task.output.pbr_model or task.output.model or task.output.base_model
    preview_url = task.output.rendered_image
    if not model_url:
        raise RuntimeError(f"{component['id']} succeeded but no model URL was returned")

    download_url(model_url, model_path, proxy)
    if preview_url:
        download_url(preview_url, preview_path, proxy)

    result.update(
        {
            "pbr_model": str(model_path.relative_to(ROOT)).replace("\\", "/"),
            "rendered_image": str(preview_path.relative_to(ROOT)).replace("\\", "/")
            if preview_path.exists()
            else None,
            "file_size_mb": file_size_mb(model_path),
            "source_host": urlparse(model_url).hostname,
        }
    )
    return result


async def main():
    parser = argparse.ArgumentParser(description="Generate standard Tripo3D models for Taihe Hall components.")
    parser.add_argument("--force", action="store_true", help="Regenerate even when local files already exist.")
    parser.add_argument("--region", choices=["global", "china"], default="global")
    args = parser.parse_args()

    api_key, proxy = setup_env()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    client = TripoClient(api_key=api_key, IS_GLOBAL=(args.region == "global"))
    try:
        balance_before = await client.get_balance()
        balance_before_data = balance_to_dict(balance_before)
        print(f"balance_before: {balance_before}", flush=True)
        results = []
        for component in COMPONENTS:
            results.append(await generate_component(client, component, proxy, force=args.force))
            manifest = {
                "model_version": "v3.1-20260211",
                "quality": "standard",
                "balance_before": balance_before_data,
                "results": results,
            }
            (OUT_ROOT / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        balance_after = await client.get_balance()
        balance_after_data = balance_to_dict(balance_after)
        manifest = {
            "model_version": "v3.1-20260211",
            "quality": "standard",
            "balance_before": balance_before_data,
            "balance_after": balance_after_data,
            "results": results,
        }
        (OUT_ROOT / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from tripo3d import TripoClient


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = ROOT / "assets" / "ai" / "illustration-dougong.png"
DEFAULT_OUT = ROOT / "assets" / "models" / "tripo" / "ab-dougong"


def enable_aiohttp_env_proxy():
    try:
        import aiohttp
        from tripo3d.client_impl.aiohttp_client_impl import AioHttpClientImpl
    except Exception:
        return

    async def _ensure_session_with_env_proxy(self):
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=self._ssl_context)
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"},
                connector=connector,
                trust_env=True,
            )
        return self._session

    AioHttpClientImpl._ensure_session = _ensure_session_with_env_proxy


async def run_one(client, image_path: Path, quality: str, out_dir: Path) -> dict:
    task_id = await client.image_to_model(
        str(image_path),
        model_version="v3.1-20260211",
        texture=True,
        pbr=True,
        texture_quality=quality,
        geometry_quality=quality,
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
    print(f"{quality}: submitted {task_id}")
    task = await client.wait_for_task(task_id, polling_interval=5, timeout=1800, verbose=True)
    result = {
        "quality": quality,
        "task_id": task_id,
        "status": str(task.status),
        "error_code": task.error_code,
        "error_msg": task.error_msg,
    }
    if str(task.status).upper().endswith("SUCCESS"):
        quality_dir = out_dir / quality
        quality_dir.mkdir(parents=True, exist_ok=True)
        downloads = await client.download_task_models(task, str(quality_dir))
        result["downloads"] = downloads
    return result


async def main():
    parser = argparse.ArgumentParser(description="Generate standard and detailed Tripo3D A/B test models.")
    parser.add_argument("--image", default=str(DEFAULT_IMAGE), help="Reference image path.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output directory.")
    parser.add_argument("--region", choices=["global", "china"], default="global")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("TRIPO_API_KEY")
    if not api_key:
      raise SystemExit("TRIPO_API_KEY is missing. Put it in .env first.")
    proxy = os.environ.get("TRIPO_PROXY")
    if proxy:
        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy
        enable_aiohttp_env_proxy()

    image_path = Path(args.image).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    client = TripoClient(api_key=api_key, IS_GLOBAL=(args.region == "global"))
    try:
        results = []
        for quality in ("standard", "detailed"):
            results.append(await run_one(client, image_path, quality, out_dir))
        manifest = {
            "source_image": str(image_path),
            "model_version": "v3.1-20260211",
            "results": results,
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

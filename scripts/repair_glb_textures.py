import argparse
import io
import json
import struct
from pathlib import Path

from PIL import Image


def align4(data: bytearray) -> None:
    while len(data) % 4:
        data.append(0)


def read_glb(path: Path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67 or version != 2:
        raise ValueError(f"{path} is not a GLB v2 file")

    offset = 12
    chunks = {}
    while offset < length:
        chunk_length, chunk_type = struct.unpack_from("<I4s", data, offset)
        offset += 8
        chunks[chunk_type] = data[offset : offset + chunk_length]
        offset += chunk_length

    gltf = json.loads(chunks[b"JSON"].decode("utf-8").rstrip(" \t\r\n\0"))
    return gltf, chunks[b"BIN\0"]


def write_glb(path: Path, gltf: dict, bin_data: bytes) -> None:
    json_data = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_padded = bytearray(json_data)
    while len(json_padded) % 4:
        json_padded.append(0x20)

    bin_padded = bytearray(bin_data)
    align4(bin_padded)

    total_length = 12 + 8 + len(json_padded) + 8 + len(bin_padded)
    out = bytearray()
    out += struct.pack("<III", 0x46546C67, 2, total_length)
    out += struct.pack("<I4s", len(json_padded), b"JSON")
    out += json_padded
    out += struct.pack("<I4s", len(bin_padded), b"BIN\0")
    out += bin_padded
    path.write_bytes(out)


def main():
    parser = argparse.ArgumentParser(description="Re-encode embedded GLB image bufferViews to PNG.")
    parser.add_argument("src")
    parser.add_argument("dst")
    args = parser.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    gltf, old_bin = read_glb(src)

    old_views = gltf.get("bufferViews", [])
    new_bin = bytearray()
    new_views = []

    image_views = {image.get("bufferView") for image in gltf.get("images", []) if image.get("bufferView") is not None}

    for index, view in enumerate(old_views):
        align4(new_bin)
        source_start = view.get("byteOffset", 0)
        source_end = source_start + view["byteLength"]
        chunk = old_bin[source_start:source_end]

        if index in image_views:
            image = Image.open(io.BytesIO(chunk))
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA")
            out = io.BytesIO()
            image.save(out, format="PNG", optimize=True)
            chunk = out.getvalue()

        next_view = dict(view)
        next_view["byteOffset"] = len(new_bin)
        next_view["byteLength"] = len(chunk)
        new_views.append(next_view)
        new_bin += chunk

    for image in gltf.get("images", []):
        if image.get("bufferView") is not None:
            image["mimeType"] = "image/png"

    gltf["bufferViews"] = new_views
    gltf["buffers"] = [{"byteLength": len(new_bin)}]
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_glb(dst, gltf, bytes(new_bin))
    print(dst)


if __name__ == "__main__":
    main()

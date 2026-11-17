"""Sabit Hugging Face revizyonunu proje içine indirir; hiçbir belge göndermez."""

import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

repo = "mlx-community/Qwen3-VL-2B-Instruct-4bit"
revision = "9c4f5209e57b31f4b9dfba735de3fb983739c9cc"
root = Path(__file__).resolve().parents[1] / "lab_models/qwen3-vl-2b-4bit"
root.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen(
    f"https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true"
) as response:
    metadata = json.load(response)
revision = metadata["sha"]
files = []
for entry in metadata["siblings"]:
    name = entry["rfilename"]
    if "/" in name or name.startswith("."):
        continue
    target = root / name
    expected = entry.get("size") or entry.get("lfs", {}).get("size")
    if target.exists() and expected and target.stat().st_size == expected:
        print("Mevcut:", name, flush=True)
    else:
        print("İndiriliyor:", name, expected, flush=True)
        url = f"https://huggingface.co/{repo}/resolve/{revision}/{name}"
        temp = target.with_suffix(target.suffix + ".partial")
        with urllib.request.urlopen(url, timeout=120) as response, temp.open(
            "wb"
        ) as stream:
            shutil.copyfileobj(response, stream, length=1024 * 1024)
        if expected and temp.stat().st_size != expected:
            raise ValueError(f"Eksik dosya: {name}")
        temp.replace(target)
    # Büyük ağırlık dosyasını belleğe almadan gerçek özetini hesaplarız.
    with target.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    expected_sha = entry.get("lfs", {}).get("sha256")
    if expected_sha and sha != expected_sha:
        raise ValueError(f"Dosya özeti uyuşmuyor: {name}")
    files.append({"file": name, "size": target.stat().st_size, "sha256": sha})
(root / "download_manifest.json").write_text(
    json.dumps(
        {"repo": repo, "revision": revision, "license": "Apache-2.0", "files": files},
        indent=2,
    )
)
print("Qwen ağırlıkları indirildi.", flush=True)

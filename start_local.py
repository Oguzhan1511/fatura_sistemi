"""Uygun yerel Python ortamını bulup web uygulamasını başlatır."""

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
candidates = (
    [ROOT / ".venv-lab" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")]
    if "--lab" in sys.argv
    else []
) + [
    ROOT / ".venv-ocr" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
    ROOT / ".venv-lab" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
    ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
    Path(sys.executable),
]
if sys.platform == "darwin":
    candidates.append(
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    )
for candidate in candidates:
    if not candidate.is_file():
        continue
    check = subprocess.run(
        [str(candidate), "-c", "import pdfplumber; from PIL import Image"],
        capture_output=True,
    )
    if check.returncode == 0:
        os.chdir(ROOT)
        arguments = sys.argv[1:]
        entry = "lab.py" if "--lab" in arguments else "app.py"
        arguments = [arg for arg in arguments if arg != "--lab"]
        os.execv(str(candidate), [str(candidate), str(ROOT / entry), *arguments])
print(
    "Gerekli Python paketleri bulunamadı. Önce: python -m pip install -r requirements.txt",
    file=sys.stderr,
)
sys.exit(1)

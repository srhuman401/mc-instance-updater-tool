#!/usr/bin/env python3
"""Build the Minecraft modpack tools as separate PyInstaller executables."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = (
    "generate-patch-tool.py",
    "update-mc-modpack-tool.py",
)


def main() -> int:
    missing = [name for name in SCRIPTS if not (ROOT / name).is_file()]
    if missing:
        print("ERROR: Missing script(s) next to build-tools.py:")
        for name in missing:
            print(f"  - {name}")
        print(f"Expected folder: {ROOT}")
        return 1

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed for this Python interpreter.")
        print(f'Install it with: "{sys.executable}" -m pip install pyinstaller')
        return 1

    dist_dir = ROOT / "dist"
    build_dir = ROOT / "build"
    dist_dir.mkdir(exist_ok=True)
    build_dir.mkdir(exist_ok=True)

    for script in SCRIPTS:
        stem = Path(script).stem
        command = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean", "--onefile", "--windowed",
            "--distpath", str(dist_dir),
            "--workpath", str(build_dir / stem),
            "--specpath", str(build_dir),
            str(ROOT / script),
        ]
        print(f"\n{'=' * 68}\nBuilding {script}\n{'=' * 68}", flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode != 0:
            print(f"ERROR: PyInstaller failed while building {script}.")
            return result.returncode

    print("\nBuild complete. Output folder:")
    print(f"  {dist_dir}")
    for script in SCRIPTS:
        exe = dist_dir / f"{Path(script).stem}.exe"
        print(f"  {'OK' if exe.is_file() else 'NOT FOUND'}: {exe.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate a simple Minecraft modpack patch folder using only Python's stdlib."""
from __future__ import annotations
import json, re, shutil, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

MANIFEST_NAME = "patch-modpack-manifest.json"
PATCH_MANIFEST_NAME = "patch-manifest.json"


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower())
    return re.sub(r"-+", "-", value).strip("-_") or "minecraft-modpack"


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read valid JSON from:\n{path}\n\n{exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in:\n{path}")
    return data


def main() -> int:
    root = tk.Tk()
    root.withdraw()
    try:
        selected = filedialog.askdirectory(
            parent=root,
            title="Select Minecraft instance folder (must contain saves and mods)",
            mustexist=True,
        )
        if not selected:
            return 0
        instance = Path(selected)
        mods_dir = instance / "mods"
        if not (instance / "saves").is_dir() or not mods_dir.is_dir():
            messagebox.showerror(
                "Invalid Minecraft instance",
                "The selected folder must contain both a 'saves' folder and a 'mods' folder.",
                parent=root,
            )
            return 1

        manifest_path = instance / MANIFEST_NAME
        if manifest_path.exists():
            manifest = load_json(manifest_path)
            pack_id = manifest.get("packId")
            version = manifest.get("patchVersion", 0)
            if not isinstance(pack_id, str) or not pack_id.strip():
                raise ValueError(f"'{MANIFEST_NAME}' must contain a non-empty 'packId'.")
            if not isinstance(version, int) or isinstance(version, bool) or version < 0:
                raise ValueError("'patchVersion' must be a non-negative integer.")
            manifest.setdefault("patchVersion", version)
        else:
            pack_id = slugify(instance.parent.name)
            manifest = {"packId": pack_id, "patchVersion": 0}
            version = 0
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        patch_version = version + 1
        patches_dir = instance / "PatchesGenerated"
        patches_dir.mkdir(exist_ok=True)
        patch_dir = patches_dir / f"Patch-{patch_version:03d}"
        if patch_dir.exists():
            messagebox.showerror(
                "Patch already exists",
                f"'{patch_dir}' already exists. Nothing was overwritten.\n\n"
                "Move or rename the old patch folder, or update patchVersion in the instance manifest if appropriate.",
                parent=root,
            )
            return 1

        mod_files = sorted(
            (p for p in mods_dir.iterdir() if p.is_file() and p.suffix.lower() == ".jar"),
            key=lambda p: p.name.lower(),
        )
        patch_mods = patch_dir / "mods"
        patch_mods.mkdir(parents=True)
        try:
            for source in mod_files:
                shutil.copy2(source, patch_mods / source.name)
            patch_manifest = {
                "packId": pack_id,
                "patchVersion": patch_version,
                "remove": [],
                "add": [p.name for p in mod_files],
            }
            (patch_dir / PATCH_MANIFEST_NAME).write_text(
                json.dumps(patch_manifest, indent=2) + "\n", encoding="utf-8"
            )
            # The generator's source instance represents the newest pack state.
            # Client instances are advanced separately by the updater after applying a patch.
            manifest["patchVersion"] = patch_version
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        except Exception:
            shutil.rmtree(patch_dir, ignore_errors=True)
            raise

        messagebox.showinfo(
            "Patch generated",
            f"Patch generated successfully.\n\nFolder: {patch_dir}\nPack ID: {pack_id}\n"
            f"Patch version: {patch_version}\nMods copied: {len(mod_files)}\n\n"
            "The source instance manifest was advanced to this patch version. Client instances are advanced only after the updater successfully applies the patch.",
            parent=root,
        )
        return 0
    except Exception as exc:
        messagebox.showerror("Patch generation failed", str(exc), parent=root)
        return 1
    finally:
        root.destroy()


if __name__ == "__main__":
    raise SystemExit(main())

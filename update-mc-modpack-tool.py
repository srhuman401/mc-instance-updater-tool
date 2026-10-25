#!/usr/bin/env python3
"""Apply a ZIP-based Minecraft modpack patch with staging and rollback."""
from __future__ import annotations
import json, os, shutil, tkinter as tk
from pathlib import Path, PurePosixPath
from tkinter import filedialog, messagebox
from zipfile import ZipFile, BadZipFile

MANIFEST_NAME = "patch-modpack-manifest.json"
PATCH_MANIFEST_NAME = "patch-manifest.json"
TEMP_DIR_NAME = ".TempPatchLoadMods"
BACKUP_DIR_NAME = ".TempPatchBackupMods"


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read valid JSON from:\n{path}\n\n{exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in:\n{path}")
    return data


def safe_jar_name(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Every entry in '{field_name}' must be a non-empty filename.")
    if Path(value).name != value or "/" in value or "\\" in value or value in {".", ".."}:
        raise ValueError(f"Unsafe filename in '{field_name}': {value!r}")
    if not value.lower().endswith(".jar"):
        raise ValueError(f"Expected a .jar filename in '{field_name}': {value!r}")
    return value


def validate_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"Patch manifest field '{field_name}' must be a list.")
    names = [safe_jar_name(item, field_name) for item in value]
    if len(set(names)) != len(names):
        raise ValueError(f"Patch manifest field '{field_name}' contains duplicate filenames.")
    return names


def choose_instance(root: tk.Tk) -> Path | None:
    value = filedialog.askdirectory(parent=root, title="Select your Minecraft instance folder", mustexist=True)
    return Path(value) if value else None


def choose_patch(root: tk.Tk) -> Path | None:
    value = filedialog.askopenfilename(
        parent=root, title="Select the patch ZIP file",
        filetypes=[("Patch ZIP", "*.zip"), ("All files", "*.*")],
    )
    return Path(value) if value else None


def read_patch_zip(zip_path: Path) -> tuple[dict, dict[str, bytes]]:
    try:
        with ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            if PATCH_MANIFEST_NAME not in names:
                raise ValueError(f"The ZIP must contain '{PATCH_MANIFEST_NAME}' at its root.")
            manifest = json.loads(archive.read(PATCH_MANIFEST_NAME).decode("utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("The patch manifest must be a JSON object.")
            payloads: dict[str, bytes] = {}
            for name in names:
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError(f"The ZIP contains an unsafe path: {name!r}")
                if len(path.parts) == 2 and path.parts[0] == "mods" and path.suffix.lower() == ".jar":
                    filename = safe_jar_name(path.name, "ZIP mods folder")
                    if filename in payloads:
                        raise ValueError(f"The ZIP contains duplicate mod filename: {filename}")
                    payloads[filename] = archive.read(name)
            return manifest, payloads
    except BadZipFile as exc:
        raise ValueError("The selected file is not a valid ZIP archive.") from exc
    except UnicodeDecodeError as exc:
        raise ValueError("The patch manifest is not valid UTF-8.") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"The patch manifest contains invalid JSON:\n{exc}") from exc


def main() -> int:
    root = tk.Tk()
    root.withdraw()
    staging: Path | None = None
    try:
        instance = choose_instance(root)
        if not instance:
            return 0
        mods_dir = instance / "mods"
        instance_manifest_path = instance / MANIFEST_NAME
        if not mods_dir.is_dir():
            messagebox.showerror("Invalid instance", "The selected folder does not contain a 'mods' folder.", parent=root)
            return 1
        if not instance_manifest_path.is_file():
            messagebox.showerror(
                "Missing modpack manifest",
                f"This instance does not contain '{MANIFEST_NAME}'. It may not be the intended modpack instance.",
                parent=root,
            )
            return 1

        instance_manifest = load_json(instance_manifest_path)
        pack_id = instance_manifest.get("packId")
        installed_version = instance_manifest.get("patchVersion", 0)
        if not isinstance(pack_id, str) or not pack_id.strip():
            raise ValueError(f"'{MANIFEST_NAME}' must contain a non-empty 'packId'.")
        if not isinstance(installed_version, int) or isinstance(installed_version, bool) or installed_version < 0:
            raise ValueError("Installed 'patchVersion' must be a non-negative integer.")

        patch_zip = choose_patch(root)
        if not patch_zip:
            return 0
        patch_manifest, payloads = read_patch_zip(patch_zip)
        patch_pack_id = patch_manifest.get("packId")
        patch_version = patch_manifest.get("patchVersion")
        if not isinstance(patch_pack_id, str) or not patch_pack_id.strip():
            raise ValueError("The patch manifest must contain a non-empty 'packId'.")
        if patch_pack_id != pack_id:
            messagebox.showerror("Wrong modpack", f"This patch is for '{patch_pack_id}', but this instance is '{pack_id}'.", parent=root)
            return 1
        if not isinstance(patch_version, int) or isinstance(patch_version, bool) or patch_version < 1:
            raise ValueError("Patch 'patchVersion' must be a positive integer.")
        if patch_version < installed_version:
            messagebox.showerror(
                "Patch is older", f"Installed patch version: {installed_version}\nPatch version: {patch_version}\n\nOlder patches cannot be applied.", parent=root
            )
            return 1
        if patch_version == installed_version:
            messagebox.showerror(
                "Patch already applied", f"Installed patch version: {installed_version}\nPatch version: {patch_version}\n\nThis is the current patch version.", parent=root
            )
            return 1

        remove_names = validate_list(patch_manifest.get("remove", []), "remove")
        add_names = validate_list(patch_manifest.get("add", []), "add")
        missing_payloads = [name for name in add_names if name not in payloads]
        usable_adds = [name for name in add_names if name in payloads]

        current_names = {p.name for p in mods_dir.iterdir() if p.is_file() and p.suffix.lower() == ".jar"}
        remove_existing = [name for name in remove_names if name in current_names]
        replacing = [name for name in usable_adds if name in current_names]
        # If an item is explicitly removed and added under the same filename, it is a replacement.
        adding = [name for name in usable_adds if name not in current_names]
        removing_only = [name for name in remove_existing if name not in usable_adds]

        staging = instance / TEMP_DIR_NAME
        backup = instance / BACKUP_DIR_NAME
        if staging.exists():
            if not messagebox.askyesno(
                "Temporary folder exists", f"'{TEMP_DIR_NAME}' already exists, possibly from an interrupted run. Delete it and rebuild staging?", parent=root
            ):
                return 1
            shutil.rmtree(staging)
        if backup.exists():
            messagebox.showerror(
                "Backup folder exists", f"'{BACKUP_DIR_NAME}' already exists. Inspect or rename it before trying again; it may contain recoverable files.", parent=root
            )
            return 1

        staging.mkdir()
        # Copy the complete mods directory, preserving unmanaged mods and subfolders.
        for item in mods_dir.iterdir():
            destination = staging / item.name
            if item.is_dir():
                shutil.copytree(item, destination)
            elif item.is_file():
                shutil.copy2(item, destination)

        # Apply changes to the staging copy only.
        for filename in remove_names:
            target = staging / filename
            if target.is_file():
                target.unlink()
            elif target.exists():
                raise ValueError(f"Expected a mod file but found a non-file at:\n{target}")
        for filename in usable_adds:
            (staging / filename).write_bytes(payloads[filename])

        preview = (
            "Apply Patch Updates?\n\n"
            f"({len(adding)}) Mods will be added\n"
            f"({len(replacing)}) Mods will be replaced\n"
            f"({len(removing_only)}) Mods will be removed\n"
            f"({len(missing_payloads)}) Mods could not be found and will not be added!\n\n"
            f"Installed patch version: {installed_version}\nPatch version: {patch_version}\n\n"
            "YES = Apply patch\nCANCEL = Discard staging files"
        )
        if missing_payloads:
            preview += "\n\nMissing from patch ZIP:\n" + "\n".join(missing_payloads[:20])
            if len(missing_payloads) > 20:
                preview += f"\n...and {len(missing_payloads) - 20} more"
        if not messagebox.askyesno("Apply Patch Updates?", preview, parent=root):
            shutil.rmtree(staging, ignore_errors=True)
            staging = None
            messagebox.showinfo("Patch cancelled", "No changes were made to the instance.", parent=root)
            return 0

        moved_original = False
        installed_staging = False
        try:
            mods_dir.rename(backup)
            moved_original = True
            staging.rename(mods_dir)
            installed_staging = True
            staging = None

            updated_manifest = dict(instance_manifest)
            updated_manifest["patchVersion"] = patch_version
            temporary_manifest = instance_manifest_path.with_name(instance_manifest_path.name + ".tmp")
            temporary_manifest.write_text(json.dumps(updated_manifest, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary_manifest, instance_manifest_path)
        except Exception as apply_error:
            rollback_errors = []
            try:
                if installed_staging and mods_dir.exists():
                    shutil.rmtree(mods_dir)
                if moved_original and backup.exists():
                    backup.rename(mods_dir)
            except Exception as rollback_error:
                rollback_errors.append(str(rollback_error))
            detail = f"Patch application failed:\n{apply_error}"
            if rollback_errors:
                detail += f"\n\nRollback also failed:\n{rollback_errors[0]}\n\nBackup may remain at:\n{backup}"
            messagebox.showerror("Update failed — rollback attempted", detail, parent=root)
            return 1

        try:
            shutil.rmtree(backup)
        except Exception as exc:
            messagebox.showwarning("Patch applied; backup remains", f"Patch applied, but backup cleanup failed:\n{backup}\n\n{exc}", parent=root)
        messagebox.showinfo("Patch applied successfully", f"Patch {patch_version} was applied.\n\nRestart Minecraft before joining the server.", parent=root)
        return 0

    except Exception as exc:
        if staging is not None and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        messagebox.showerror("Update failed", str(exc), parent=root)
        return 1
    finally:
        root.destroy()


if __name__ == "__main__":
    raise SystemExit(main())

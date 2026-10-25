# HELP

## SECURITY WARNING!

This tool does **NOT** verify whether mods are safe or malicious.

It can be used to distribute malicious content that may harm your computer or compromise your data.

The tool itself does not automatically execute the mods it installs. However, Minecraft mods are executable code and may run when you launch Minecraft.

**ONLY apply patches from people you trust!**

Never run this tool on a modpack or patch from an untrusted source.

## Updating a Modpack / Instance

1. Run `update-mc-modpack-tool.exe`.
2. Navigate to your Minecraft instance folder.
3. Open the `Minecraft` sub-folder if your launcher uses one (It can be any folder as long as it contains your saves and mods folder.).
4. Select the folder containing the instance's `mods` folder and modpack manifest.

   If the tool does not prompt you to select a patch ZIP afterward, you may have selected the wrong folder.

5. Select the supplied patch file. It should be a `.zip` file.
6. Review the update summary and select **YES** to apply the patch, or **CANCEL** to abort.
7. Wait for the tool to finish. If successful, it will display a confirmation message.

**IMPORTANT:** Close Minecraft before applying a patch.

## If an Update Fails

Possible reasons include:

- **Already up-to-date:** The patch version matches your installed version. No update is needed.
- **Your instance is newer:** The patch is older than your installed version. Do not attempt to downgrade unless instructed by the pack maintainer.
- **Invalid patch:** The ZIP or its manifest is missing required information or contains invalid data.
- **Wrong modpack:** The patch belongs to a different modpack.
- **Missing mods:** Some mods listed in the patch could not be found in the patch ZIP.

If the tool reports missing mods or an invalid patch, contact the person who supplied the patch. Do not assume the update completed correctly.

If the tool reports that the update failed while applying files, check the error message before attempting the patch again.

## Need Help?

Contact the person who supplied your modpack or patch. Include the exact error message displayed by the tool so they can help diagnose the problem.
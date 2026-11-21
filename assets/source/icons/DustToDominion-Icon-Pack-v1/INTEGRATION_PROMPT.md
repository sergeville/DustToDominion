# Give this to the game development agent

Integrate this Dust to Dominion icon package into the current game application.
Carry the task through implementation and relevant verification.

1. Inspect the current repository, launcher and packaging configuration. Preserve
   existing work. Treat the old artwork review commit 844ad1d as historical context,
   not as an instruction to reset the current branch.
2. Use `01-original` by default, or Serge's chosen alternative. Read `manifest.json`
   and run `python3 tools/verify_package.py`. Keep source artwork and provenance
   separate from runtime assets.
3. Add the selected PNGs, ICNS and ICO through the repository's existing resource
   and packaging conventions. Do not add all six large variants to the shipped
   game unless they are actually used by a user-facing feature.
4. Set the pygame runtime icon using the selected PNG before initial window creation
   where supported. Use the existing resource resolver so source and packaged launches
   both work. `integration/pygame_icon.py` is an optional adapter, not a drop-in patch
   for an inspected current repository.
5. Configure the existing macOS bundle to use the ICNS and the Windows packaging,
   if supported, to use the ICO. Modify the existing build configuration. Do not
   introduce a new packager or replace launcher behavior merely to apply an icon.
6. If there is only a .command/Python launcher, state that clearly. A runtime window
   icon and a macOS application-bundle icon are different integration surfaces.
   Do not claim that copying an ICNS changes the Terminal application icon.
7. Validate source launch, packaged asset lookup and applicable native app icons.
   Exercise fullscreen/windowed transitions and restart. Check the icon at small
   and large OS display sizes. Use the normal build/signing flow for changed bundles.
8. Report changed files, the selected view, checks performed and any checks that
   remain pending on unavailable operating systems. Do not claim native integration
   based solely on successful image decoding.

Keep changes focused on application identity. Gameplay, camera, saves, economy,
audio implementation and existing work remain governed by their current tasks.

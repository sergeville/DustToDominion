# Realistic campaign artwork

These thirteen original raster assets were generated for this local game upgrade
with the built-in `image_gen.imagegen` tool on 2026-11-20. Each `.prompt.txt` is
the exact generation instruction. `manifest.json` records source/export paths,
dimensions, hashes, alpha checks, provenance and the lighting compromise.

The accompanying PNGs are the original editable raster sources. No layered
painting file, rig, mesh or 3D scene was produced. Runtime exports in
`resources/campaign/realistic/` are byte-identical copies; there is no destructive
crop, background removal or reference-board extraction. Generation is not
bit-deterministic; retaining these originals is necessary for exact reproduction.

The first three assets (Prospector, iron asteroid and station) were delivered
before the lead's input-driven mining-trip gate. The remaining assets were
created after the lead reported that gate passed. That report is integration
evidence owned by the lead/QA, not an independent art-agent gameplay test.

## Drawing contract

- Ships point up, with a central pivot. The renderer converts to existing
  heading coordinates. Exhaust and weapon effects are runtime draws.
- Ships, station and asteroids have genuine alpha. Generated transparent margins
  vary and occasionally contain faint edge pixels. The renderer fits useful
  alpha bounds; original images remain untouched.
- Portraits, dock and starfield are intentionally opaque. The dock is 3:1,
  the backdrop approximately16:9. Preserve aspect ratio in panels.
- Sprites/portraits are1254x1254, dock2172x724, backdrop1672x941. They are not
  native4K sources. Sprite source detail exceeds their current gameplay sizes;
  a full-screen4K backdrop is enlarged.
- Lighting is baked restrained overhead fill and local occlusion. It rotates
  with sprites; no dynamic3D relighting is claimed.
- The reference board informed style and silhouettes. Every supplied asset was
  generated independently; none is cut from that board. The dock's static ship
  is a related mining-craft illustration, not a pixel-identical view of the
  playable Prospector sprite.

## Asset review and validation

All thirteen originals were visually inspected for subject, silhouette, material,
composition and unwanted text. PNG decoding and dimensions were checked with
pygame2.5.8. Source/export SHA-256 equality was verified for every asset;
transparent-sprite alpha channels and all four corner alpha values were checked.
These checks establish usable artwork files, not native play or final fidelity
acceptance. The independent review and integrated screenshots own those claims.

## Usage and limitations

Generated with the available built-in service for the user-authorized game
project, under that service's applicable terms. No third-party asset pack was
imported. This provenance is not a claim of exclusive copyright or separate
legal clearance. Fonts, UI values and gameplay geometry remain application-owned.

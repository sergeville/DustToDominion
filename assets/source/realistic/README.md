# Realistic campaign artwork

The initial thirteen original raster assets were generated for this local game upgrade
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

## Artwork and lighting siblings — 2026-11-20

Six additional originals and byte-identical runtime copies are retained alongside
the initial assets: `asteroid_iron_c`, `asteroid_gold_b`, `asteroid_crystal_b`,
`prospector_v2`, `rival_v2` and `station_v2`. Their exact prompts and hashes are in
the same manifest. No initial original or export was overwritten. Ship/station
edits used the matching original PNG as the sole edit reference; the manifest
records that reference and its hash. The three rocks were independently generated.

The new rocks add a cleft angular iron chunk, a broken gold wedge, and a pointed
crystal host with large glassy faces. Ship and station edits retain recognizable
overhead silhouettes while separating large silver planes, dark recesses, glass,
and coloured enamel. All six sources are 1254×1254 with real alpha, centred by the
existing renderer's useful-alpha bounds and circle fit. The rival has alpha-1
residue at its two bottom corners; the existing alpha-8 fit threshold ignores it.
No source cleanup, upscaling, fabricated layers or 3D originals are claimed.

All six decode successfully and source/export SHA-256 hashes match. Fully
transparent pixels range from 325,964 (station) to 978,494 (rival). Visual review
of originals and `artwork-pass-comparison.png` checks shape/material separation;
the comparison is a diagnostic renderer-normalized preview, not gameplay evidence.
It shows hulls at 114/93 pixels and rocks at 132 pixels. The station pair is shown
at half of its 330-pixel comparison diameter to fit the sheet. Integrated gameplay,
performance, native controls/audio and human visual acceptance are separate gates.

Lighting is baked into these sprites and rotates with them. Runtime mining and
impact lighting may supplement it, but these files supply no normal maps or
physically correct relighting. These are incremental material improvements; they
do not establish that the full cinematic reference has been matched.

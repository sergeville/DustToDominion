# Dust to Dominion — realistic visual upgrade with a coordinated team

Attach this document and the generated image titled **DUST TO DOMINION — REALISTIC VISUAL TARGET** to your coding agent. Open the actual game repository in that agent's workspace. The original screenshots, `screenshots.zip`, `manifest.json`, `ship-designs.png`, and `2026-11-20-playable-game.md` are useful supporting evidence when available.

The instructions below are addressed to the implementation agent. They authorize local implementation and validation, not merely a proposal.

---

## Mission

Act as the lead engineer and integrator for Dust to Dominion. Coordinate a small team to turn the attached realistic visual reference into a working visual upgrade of the existing game. Complete the implementation through playable validation and a clear handoff.

The player should recognize the reference's detailed ships, rugged asteroids, industrial station, restrained lighting, readable interface and mining/combat effects while playing the existing campaign. Keep the game's current mechanics, economy, controls and save compatibility intact.

The image is an art-direction board. Its five panels depict different views and activities; implement them in their appropriate game screens. Build reusable assets and interactive UI. Keep text, numerical values, localization and controls rendered by the application. A flattened illustration cannot substitute for working gameplay.

Prefer a realistic 2D/2.5D presentation within the verified existing engine. Establish the practical asset pipeline before considering any engine migration. Visual realism does not require changing the arcade movement model.

## 1. Inspect the actual project and establish authority

Before editing:

1. Locate and read applicable `AGENTS.md` files, the README, manifests, launch instructions and active implementation plans. Inspect the working tree, current branch, worktrees and overlapping work. Preserve uncommitted changes, running sessions, user settings and saved games.
2. Identify the actual entry point, simulation model, screen classes, asset loading, drawing, input, localization and save code. The supplied review describes Python/pygame, but verify the current checkout rather than assuming its architecture.
3. Reuse the existing canonical plan or Story when it owns this outcome. Otherwise establish one concise visual-upgrade plan in the project's normal documentation location. Record the goal, accountable owner, affected files, dependencies, acceptance criteria and evidence. If BMAD is already used, maintain its existing Goal → Epic → Story → Task links; avoid a competing roadmap.
4. Scan active branches and tasks for duplicate or overlapping work. Reuse, merge or sequence it under one owner. Resolve routine implementation choices from repository evidence and this objective; do not stop for repeated approval of ordinary local edits.
5. Record the exact revision and working-tree state. Run the appropriate baseline checks and capture current runtime screenshots of the screens being changed. Discover real commands from the repository; do not invent filenames or test commands.

Classify important claims as verified, documented, historical, conflicting or unknown. Current code and observed runtime behavior govern mechanics; the attached concept governs the desired visual direction. When they appear to conflict, preserve the established behavior and adapt the presentation.

Context to verify, not fresh proof:

- The supplied review reports a finite offline campaign with three mining sectors, trading, upgrades, rival combat, two crew hires, passive support ships, recoverable defeat and station checkpoints.
- It reports **1,730 passing tests** for a prior local revision. That is not the current checkout's test result.
- The supplied ZIP was checked: 30 valid PNGs matching the supplied hashes, covering five scenes in English/German at 1280×720, 1920×1080 and 2560×1440. These establish static visual evidence, not native play acceptance.
- The review names `feature/complete-small-game`. Treat it as a historical location hint; inspect the actual branch before deciding where to work.
- The generated visual target is **1672×941 pixels**, not native 4K.

## 2. Use a real team with explicit ownership

If sub-agents are available, delegate bounded tasks and use their actual findings. Keep the lead responsible for integration and the final result. If delegation is unavailable, perform these roles sequentially and report that honestly.

| Role | Owns | Boundary |
| --- | --- | --- |
| Lead / integrator | Canonical plan, scope, asset/rendering contracts, shared screen wiring, integration | Sole coordinator of shared-file changes |
| Art / asset specialist | Ship, station, asteroid, ore, effect and portrait artwork; editable sources and exports | Declared asset directories; no simulation changes |
| Rendering engineer | Resource loading, transforms, animation, visual effects, caching and rendering performance | Declared rendering modules; coordinate screen integration with lead |
| UI / UX engineer | HUD, station, fleet, guidance, responsive layout, localization and input mapping | Declared UI files; no economy or save changes |
| Independent QA / reviewer | Baseline, regression coverage, visual comparisons, native play evidence and final review | Read-only review first; own agreed test/evidence files |

Combine roles when capacity is limited. Each assignment must state its parent goal/Story, owner, exact writable assets, dependencies, output and acceptance evidence. Parallel work is safe only where ownership does not overlap. Use isolated branches/worktrees if supported by the project; they do not replace coordination over shared files.

Each agent returns changed files, validation performed, unresolved issues and integration notes. The lead reviews and integrates each completed piece. Reviewers must distinguish independently observed results from the implementer's claims.

## 3. Establish the visual and asset contract

Settle this contract before parallel asset/UI/rendering implementation:

- Common near-overhead flight projection, ship forward direction, pivots, anchors, logical sizes, visual bounds, scale and file naming/location.
- Separate editable sources and runtime exports. Define transparent backgrounds, animation frames, asset metadata, loading, missing-asset behavior and bounded cache policy using the project's existing conventions.
- Shared material, lighting, color and typography rules. Account for ship rotation: rotating a strongly lit sprite also rotates its painted light. Choose restrained baked lighting, directional renders or a supported runtime-lighting approach and document the compromise.
- Preserve gameplay geometry independently of sprite size, shadows, thruster exhaust and decorative particles. Align visible hulls, beam origins, gun mounts, docking markers and safe-zone indicators with the actual model.
- Keep visual random effects separate from gameplay randomness. Drawing must not advance the simulation or change outcomes.
- Record provenance and usage rights for new assets, and retain reproducible source/export settings. For generated artwork, retain the original image, generation/edit instructions and export settings; keep layered art or 3D scene files when those formats were actually used. Do not invent unavailable source files or assume a 3D model is required. Use available authorized art-generation or rendering tools where helpful. Produce coherent reusable assets rather than cropping finished ships and UI out of the reference board.

Required visual families:

| Asset / surface | Target |
| --- | --- |
| Prospector | Recognizable forked mining-ship silhouette, detailed worn metal, cyan cockpit/navigation accents, readable engines and mining mount |
| Hauler | Robust cargo hull and side racks, visibly distinct from the Prospector |
| Refinery | Wider industrial hull with the recognizable circular processing element |
| Rival | Sharp hostile silhouette, distinct red identification and weapon effects |
| Kepler Station | Four-module circular industrial station, docking structure, service details and clear navigation lights |
| Asteroids / ore | Varied rocky silhouettes, craters and mineral detail; distinguish iron, gold and crystal without relying solely on color |
| Effects | Clear mining contact, chips, pickups, bounded exhaust, projectiles and impacts; restrained visual noise |
| Crew / station art | Consistent portraits and docking artwork placed in the existing appropriate screens |
| HUD / menus | Legible dynamic text, restrained cyan/amber emphasis, visible targets, clear buttons and actual interaction states |

The station interior panel can inform station-screen artwork; flight assets must retain a compatible flight camera. Keep space dark enough for navigation and combat readability. The player ship must remain easy to locate at the station and against asteroids.

If suitable final artwork cannot be produced with the available tools, implement the independent pipeline and interaction work, identify the exact missing assets and label provisional artwork explicitly. Placeholder art means the visual objective remains unfinished.

## 4. Preserve the gameplay contract

Verify these details against current code and preserve its established formulas:

- Launch → fly → mine → collect → return → dock → sell → upgrade progression, sector unlocks, combat rewards, defeat/recovery and reachable victory.
- The Prospector is the player's piloted ship. Support ships remain passive sale bonuses. The supplied fleet screen shows Hauler +10% and Refinery +20%; retain current code's stacking and rounding behavior.
- The supplied station UI shows a mining specialist providing 15% faster mining and an engineer providing 15% less damage. Keep current implementation semantics, prices and purchase conditions.
- The documented victory goal is three ships, both crew members and 1,200 banked credits. Preserve the verified campaign goal.
- Preserve the current versioned saves, atomic replacement and recovery behavior. A visual upgrade should not require a save migration. Use separate test checkpoints rather than the player's live save.
- Preserve movement, mining/docking ranges, hitboxes, projectile behavior, safe-zone weapon locks/shield protection and bounded simulation resources.
- Preserve keyboard/mouse controls, focus-loss pause, cleared held inputs, pause/resume, modal transitions, QUIT and fullscreen event handling.
- Investigate the screenshot showing `COLLECT ORE` while `CUT 33%` is active. Reproduce the state and decide whether existing fragments explain it. Make guidance accurately communicate the next useful action; do not declare a logic bug from a screenshot alone.

Keep feature additions such as active escorts, autonomous fleets, orbital physics, new economic systems or multiplayer outside this visual-upgrade scope. Record separately justified proposals without slipping them into implementation.

## 5. Implement in dependency order

| Stage | Work | Safe parallel work | Exit evidence |
| --- | --- | --- | --- |
| A — Baseline | Inspect repository, resolve overlaps, define owners and contracts | Read-only visual review and QA discovery | Current baseline and one canonical plan |
| B — First playable slice | Redesigned Prospector, one asteroid, ore, station, mining effect and HUD | Asset production and integration behind agreed contracts | Working launch → mine → collect → dock → sell, verified through available input-driven integration and actual runtime captures; native acceptance recorded separately |
| C — Expand the presentation | Remaining ships/materials, station/fleet/crew views, combat effects, progression UI | Separate asset, rendering and UI tasks with declared ownership | Integrated screens and functional controls |
| D — Display and performance | Resolution/DPI behavior, caching, effect bounds, readability | QA matrix and independent visual review | Measured runtime captures and performance results |
| E — Acceptance | Gameplay regression checks, native campaign checks, documentation and handoff | Independent review of the final integrated revision | Honest completion status and reproducible evidence |

Complete the first playable slice before spreading unfinished art or architecture across every screen. The lead assesses that slice against the reference and acceptance criteria, corrects material gaps, then proceeds. Perform native interaction when available. If the target desktop or native automation is unavailable, record native acceptance as pending and continue independent implementation after the functional slice passes; that pending acceptance remains an unresolved completion item. Continue through the remaining stages without treating the plan itself as completion.

## 6. Handle 4K, scaling and performance honestly

Support 1280×720, 1920×1080 and 2560×1440, and target **3840×2160 output** where the renderer and available display support it. Keep window dimensions, drawable framebuffer pixels and macOS display scaling distinct. Verify mouse aiming, UI hit targets and world/screen transforms after resizing and fullscreen transitions.

Render UI text at an appropriate output resolution and provide artwork with sufficient source detail. Enlarging the 1672×941 reference is not native 4K artwork. Record source-asset sizes, framebuffer dimensions and screenshot dimensions separately; label upscaled or offscreen-only evidence accurately.

Measure the actual target hardware and renderer. Aim for smooth 60 FPS where feasible; make this a measured target, not an assumed result. Record frame-time distribution, spikes and memory use for a repeatable normal and effect-heavy scene at each tested resolution. Compare against the baseline using the same scene and machine.

Load/decode assets outside the frame loop, bound rotated/scaled caches, cap visual particles and cull invisible effects. Preserve input responsiveness and gameplay under reduced visual quality if quality controls are needed. Offscreen draw timing alone does not establish native frame rate, presentation stability or audio behavior.

## 7. Acceptance and evidence

Use existing tests first and add targeted regression coverage for changed behavior. Tests should detect meaningful failures, such as incorrect coordinate mapping, missing asset handling, state/renderer coupling or broken transitions. Do not inflate test counts with checks that merely repeat the implementation.

Required acceptance:

1. **Visual fidelity:** compare actual runtime captures with the reference for ship identity, material depth, lighting, asteroid variety, station detail, effects and UI hierarchy. Have the independent reviewer report each as met, partial or missing, citing the relevant capture. Include matching before/after views.
2. **Gameplay:** exercise a fresh start, mining, collection, docking, sale, upgrades, fleet purchase and crew purchase, earned dangerous-sector combat, defeat/recovery and victory. Preserve existing simulation/integration coverage. Separate automated reachability from native play evidence.
3. **Persistence/input:** verify checkpoint save, title/Continue, corrupted/missing checkpoint handling already supported by the game, focus loss, pause/resume, fullscreen/resize, modal exit and quit behavior.
4. **Display matrix:** capture fresh flight, mining, cargo-full return, bottom edge and fleet in English and German at 720p, 1080p and 1440p. Add 2160p when available and document whether it is native or offscreen. Also inspect station services, dangerous-sector combat and victory, which the original ZIP does not cover. Ensure texts, controls and the ship remain visible.
5. **Native experience:** run the real application and check movement, aiming, mining, combat, docking, menus, saves and presentation on the available target system. Use available desktop capture/input tools. If automation cannot attach to the Python application, record the exact limitation and complete all independent work. Provide only the remaining short human acceptance sequence; do not claim headless tests are native playtesting.
6. **Regression and performance:** run the appropriate final integrated test suite and checks, fix regressions introduced by this work, and record exact commands, revision and results. Repeat only when subsequent changes invalidate the evidence.

Human judgments about fun, pacing and visual preference must remain attributed to actual play feedback. Do not invent user acceptance, performance numbers, successful checks or reviewer results.

## 8. Deliver and report

Keep implementation in the project's normal local branch workflow. Preserve unrelated work and avoid publishing or deploying as part of this local visual pass.

Deliver:

- The working upgrade, reusable runtime assets and their editable sources/provenance.
- Updated canonical plan/handoff with ownership, completed tasks, remaining issues, key decisions and a rollback path limited to this work.
- Before/after runtime screenshots, the visual-fidelity comparison, actual test results, performance measurements and native acceptance status.
- The exact launch command or launcher, current revision and a short route for the user to experience the upgrade.

In the final report, distinguish **implemented**, **visually reviewed**, **functionally verified**, and **awaiting native or user acceptance**. Name incomplete artwork or display limitations directly. Passing tests alone does not complete the visual goal; a polished reference image alone does not complete the implementation.

Start now with repository inspection, team assignments and the first playable slice. Continue until the authorized work is complete or a specific missing dependency prevents further progress.

# unity-skills

AI agent skills for Unity, mirrored from
[Unity-Technologies/skills](https://github.com/Unity-Technologies/skills) with
**`unity-` prefixed skill names**.

A skill whose name does not already contain `unity` gets a `unity-` prefix, so
`ui-uitk` becomes `unity-ui-uitk` and `localization` becomes `unity-localization`.
This keeps the names from colliding with skills from other collections and makes it
obvious to an agent which skills are Unity-specific.

## Install

```bash
npx skills add keijiro/unity-skills
```

Works with Claude Code, GitHub Copilot, Cursor, Cline and
[50+ other agents](https://skills.sh).

## Available skills

<!-- BEGIN SKILLS -->
| Skill | Description |
|---|---|
| `levelplay-unity-integration` | Integrates the LevelPlay Mediation SDK via the Ads Mediation UPM package. |
| `new-unity-project` | Use when starting a brand-new Unity game or project from scratch — "make/start/create a new game", "bootstrap a Unity project", "I want to build a [genre] game", "scaffo… |
| `unity-2d-pixel-perfect` | Sets up, diagnoses, and fixes pixel perfect 2D rendering in Unity projects. |
| `unity-asset-transformer-toolkit` | Imports 3D models and point clouds with Asset Transformer Toolkit (formerly Pixyz), and creates, edits, and runs RuleSets, Actions, and LODs. |
| `unity-audio-setup-mixers` | Scans the scene and audio assets to appropriately route Audio Sources into existing Audio Mixer Groups, classifying each source by what it plays. |
| `unity-build-live-game` | Build and operate a live game using Unity Services. |
| `unity-cli` | Use when interacting with Unity CLI from the terminal, or to control a running/connected Unity Editor from the command line — create or modify GameObjects, edit scenes a… |
| `unity-generate-editor-search-query` | Generates Unity Search / Quick Search queries and opens the Unity Search window for read-only Unity Editor asset or scene-object lookup requests. |
| `unity-implement-in-app-purchases` | Implement, configure, and debug Unity In-App Purchases (IAP) — store connection, product catalog, consumable/non-consumable/subscription purchases, two-step pending-conf… |
| `unity-initialize-ai-navigation` | Sets up and configures the Unity AI Navigation system — NavMesh surfaces, NavMesh agents, obstacles, links, modifiers, areas and costs. |
| `unity-localization` | Sets up and configures Unity Localization, including locales, String/Asset Tables, CJK font support, and Addressables workflows. |
| `unity-manage-sprite-atlas` | Manage SpriteAtlas using prebuild pipeline with IPreprocessBuildWithReport (DEFAULT approach). |
| `unity-migrate-birp-to-urp` | Plans, executes, and troubleshoots Unity projects moving from the Built-in Render Pipeline (BiRP/BIRP/Built-in RP) to the Universal Render Pipeline (URP). |
| `unity-optimize-audio` | Optimizes Unity 6 audio memory, CPU cost, and playback quality through correct import settings and mixer configuration. |
| `unity-optimize-text-mesh-pro` | Covers TextMeshPro font stacks, dynamic fallback atlases, padding and sampling ratios, SDF16, AutoSize discipline, worldspace vs UGUI, and Memory Profiler font-data capt… |
| `unity-optimize-web` | Optimizes Unity 6 WebGL and WebGPU builds for smaller download size, faster initial load, and efficient browser runtime performance. |
| `unity-package-management` | Use when adding, removing, upgrading, or discovering Unity (UPM) packages programmatically from outside the Editor — headless or CI package installs via the C# UnityEdit… |
| `unity-physics-3d-collision` | 3D PhysX collision and trigger diagnostics for MonoBehaviour-based Unity projects. |
| `unity-setup-multiplayer-services` | Guides the development of online multiplayer experiences where players connect, group, and interact in real-time using Unity Multiplayer Services. |
| `unity-setup-vivox-voice-chat` | Add and configure in-game voice chat and text chat for Unity multiplayer games using Unity Vivox. |
| `unity-shader-graph-create-custom-node` | Generates custom Shader Graph nodes from HLSL code. |
| `unity-sprite-editor` | Edits Unity sprite properties by generating C# editor scripts using ISpriteEditorDataProvider APIs. |
| `unity-sprite-segment-3x3grid` | Analyze Sprite textures and output a 3x3 grid representation based on color matching. |
| `unity-tilemap-palette-create` | Creates a Tile Palette asset. Use when the user wants to organize tiles for 2D level design or create a new Tile Palette from scratch. |
| `unity-tilemap-ruletile-createempty` | Creates an empty RuleTile asset without Sprite or Spritesheet inputs. |
| `unity-tilemap-ruletile-createfromsegment` | Use when the user wants tiles that auto-tile (autotile) as they paint, wants a RuleTile built from existing terrain or edge sprites, or asks to make sprites "tile correc… |
| `unity-ui` | Unity UI expert for menus, HUDs, screens, panels, buttons, labels, and all visual interface elements. |
| `unity-ui-imgui` | Unity IMGUI (Immediate Mode GUI) expert for legacy editor tools using OnGUI/immediate mode. |
| `unity-ui-ugui` | Unity uGUI (Canvas-based) UI expert. Understands, edits, and generates Canvas hierarchies, RectTransforms, Layout Groups, and prefab UI. |
| `unity-ui-uitk` | Unity UI Toolkit expert for Unity 6.0+. Understands, edits, and generates UXML and USS files with flex-based layouts. |
| `unity-urp-postprocessing` | Sets up, configures, and debugs URP post-processing effects using the Volume framework. |
| `unity-validate-urp-render-graph-renderer-feature` | Use when the user wants to review or validate a Unity 6+ URP ScriptableRendererFeature that uses the Render Graph API. |
<!-- END SKILLS -->

## How this repository works

`skills/`, `LICENSE.md` and `UPSTREAM.md` are **generated** by
`tools/sync_upstream.py`. Editing them here has no effect — the next sync
overwrites them. To change what a skill does, send a PR
[upstream](https://github.com/Unity-Technologies/skills).

A [GitHub Actions workflow](.github/workflows/sync-upstream.yml) checks upstream
once a day and pushes any difference straight to `main`. You can also run it
on demand from the Actions tab. The upstream commit currently mirrored is
recorded in [UPSTREAM.md](UPSTREAM.md).

### What the sync changes

Renaming a skill means more than renaming its folder. All three of these have to
agree, or agents end up chasing names that no longer exist:

1. **The folder name** — `skills/ui-uitk` → `skills/unity-ui-uitk`
2. **The `name:` field** in the skill's `SKILL.md` frontmatter
3. **Cross-references from other skills** — the routing table in `unity-ui` points
   at `unity-ui-uitk` / `unity-ui-ugui` / `unity-ui-imgui`, and
   `unity-tilemap-ruletile-createfromsegment` depends on
   `unity-sprite-segment-3x3grid`, named in its prose and in its C# comments

Names without a hyphen are handled more carefully. `ui` is indistinguishable from
the UXML namespace prefix in `<ui:UXML xmlns:ui="UnityEngine.UIElements">`, and
`localization` is just an English word, so those are only rewritten where the text
is unambiguously a skill reference: inside backticks, inside `**bold**`, inside
`(parentheses)`, in a `skills/`-prefixed path, or immediately before the word
`skill`/`skills`. If upstream adds a single-word skill name that is not on the
allowlist, the sync **fails** instead of guessing.

The sync also **quotes a `description:` that is not valid YAML**. Upstream writes
several as plain scalars containing `": "`, which is a YAML syntax error — for
example `Primary scope: OnCollisionEnter / OnTriggerEnter not firing`. Installers
silently skip those skills, so four of the 31 never install from upstream. Wrapping
the value in single quotes fixes it without changing a character of the text.

### Guardrails

Because the workflow pushes to `main` unattended, the sync refuses to write
anything — leaving CI red rather than committing something broken — if:

- a skill folder has no `SKILL.md`, or its `name:` disagrees with its folder name
- upstream adds a single-word skill name that is not on the allowlist
- two skills would end up with the same name after renaming
- upstream reports no skills at all

After generating, `--check` re-reads the result: it parses every frontmatter with a
real YAML parser and scans for any cross-reference still pointing at an
un-prefixed upstream name.

### Running it locally

```bash
python3 tools/sync_upstream.py --dry-run   # print the rename mapping, write nothing
python3 tools/sync_upstream.py             # regenerate
pip install pyyaml
python3 tools/sync_upstream.py --check     # validate the generated tree
```

> [!NOTE]
> GitHub disables `schedule` triggers on a public repository after 60 days with no
> activity, and emails the owner. Any commit, or one manual run from the Actions
> tab, re-enables it.

## License

Unity Companion License, inherited from upstream. See [LICENSE.md](LICENSE.md).

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
| `levelplay-unity-integration` | Integrates the LevelPlay ad mediation SDK via the Ads Mediation package. |
| `new-unity-project` | Guides creating a new Unity project, gathering concept, platforms, and monetization before setting up the project, source control, and packages. |
| `unity-2d-pixel-perfect` | Sets up, diagnoses, and fixes pixel perfect 2D rendering with PixelPerfectCamera in URP or Built-in. |
| `unity-asset-transformer-toolkit` | Imports 3D models and point clouds with Asset Transformer Toolkit (formerly Pixyz), and creates, edits, and runs RuleSets, Actions, and LODs. |
| `unity-audio-setup-mixers` | Routes Audio Sources into existing Audio Mixer Groups, classifying each source by what it plays. |
| `unity-build-live-game` | Builds and operates live games with Unity Services. |
| `unity-cli` | Controls the Unity Editor and projects from the command line, driving a running Editor to edit scenes and assets or run C#. |
| `unity-generate-editor-search-query` | Generates Unity Search queries and opens the Search window to find assets or scene objects. |
| `unity-implement-in-app-purchases` | Implements, configures, and debugs Unity In-App Purchases, including subscriptions, receipt validation, and direct-to-customer payments via Stripe or Coda. |
| `unity-initialize-ai-navigation` | Sets up and configures Unity AI Navigation, including NavMesh surfaces, agents, obstacles, and links. |
| `unity-localization` | Sets up and configures Unity Localization, including locales, String and Asset Tables, and CJK fonts. |
| `unity-manage-sprite-atlas` | Manages SpriteAtlas assets through a prebuild pipeline, covering master and variant atlases, packing settings, and platform overrides. |
| `unity-migrate-birp-to-urp` | Plans, executes, and troubleshoots migration from the Built-in Render Pipeline to URP. |
| `unity-optimize-audio` | Optimizes audio memory, CPU cost, and playback quality through import settings and mixer configuration. |
| `unity-optimize-text-mesh-pro` | Optimizes TextMeshPro rendering, memory, and font setup, including font asset stacks, fallback atlases, SDF quality, and worldspace text. |
| `unity-optimize-web` | Optimizes Unity WebGL and WebGPU builds for smaller downloads and faster load. |
| `unity-package-management` | Adds, removes, upgrades, and discovers Unity (UPM) packages from outside the Editor. |
| `unity-physics-3d-collision` | Diagnoses 3D PhysX collision and trigger problems. |
| `unity-project-auditor-fixes` | Instructions for how to use Project Auditor to find and fix a list of issues. |
| `unity-setup-multiplayer-services` | Guides real-time online multiplayer with Unity Multiplayer Services. |
| `unity-setup-vivox-voice-chat` | Adds and configures in-game voice and text chat with Unity Vivox. |
| `unity-shader-graph-create-custom-node` | Generates custom Shader Graph nodes from HLSL code. |
| `unity-sprite-editor` | Edits Unity sprite rectangles, borders, pivots, outlines, and slicing by generating C# scripts. |
| `unity-sprite-segment-3x3grid` | Segments a Sprite texture into a 3x3 grid and outputs a pattern of cells matching the center cell's color. |
| `unity-tilemap-palette-create` | Creates a Tile Palette asset with a rectangular, hexagonal, or isometric Grid layout. |
| `unity-tilemap-ruletile-createempty` | Creates an empty RuleTile, HexagonalRuleTile, or IsometricRuleTile asset. |
| `unity-tilemap-ruletile-createfromsegment` | Creates RuleTiles from existing terrain or edge sprites so tiles auto-tile while painting, and converts sprite-segment-3x3grid output patterns into TilingRules. |
| `unity-ui` | Routes Unity UI requests to the right framework skill (UI Toolkit, uGUI, or IMGUI) and answers UI comparison questions. |
| `unity-ui-imgui` | Generates and modifies Unity IMGUI editor code such as EditorWindows, custom Inspectors, PropertyDrawers, and OnGUI scripts. |
| `unity-ui-ugui` | Understands, edits, and generates Unity uGUI Canvas hierarchies, RectTransforms, Layout Groups, and prefab UI. |
| `unity-ui-uitk` | Understands, edits, and generates Unity UI Toolkit UXML and USS with flex layouts. |
| `unity-urp-postprocessing` | Sets up, configures, and debugs URP post-processing with the Volume framework. |
| `unity-validate-urp-render-graph-renderer-feature` | Reviews a Unity 6 URP ScriptableRendererFeature that uses the Render Graph API, checking resource wiring, material binding, execution structure, and best practices. |
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

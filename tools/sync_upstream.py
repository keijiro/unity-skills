#!/usr/bin/env python3
"""Regenerate this repository from the upstream Unity skills repo.

Every skill folder whose name does not already contain "unity" is renamed with a
"unity-" prefix, and every cross-reference to a renamed skill -- in folder names,
in the `name:` frontmatter field, and in the prose and code of every other skill --
is rewritten to match.

A `description:` that a strict YAML parser would reject -- upstream writes several
as plain scalars containing ": ", which is a syntax error -- is wrapped in single
quotes. Without that, the skills.sh installer silently skips those skills.

Everything under `skills/`, plus `LICENSE.md` and `UPSTREAM.md`, is generated and
wiped on each run. `README.md`, `tools/` and `.github/` are hand-written; only the
skill table between the BEGIN/END SKILLS markers in `README.md` is generated.

Usage:
    python tools/sync_upstream.py                 # regenerate in place
    python tools/sync_upstream.py --dry-run       # report what would change
    python tools/sync_upstream.py --check         # validate the generated tree
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

UPSTREAM_REPO = "Unity-Technologies/skills"
UPSTREAM_REF = "main"
PREFIX = "unity-"

# Skill names made of a single word (no hyphen) are also ordinary English words or
# code tokens -- `ui` collides with the UXML namespace prefix in `<ui:UXML>`, and
# `localization` is just a word. Those are rewritten only inside an explicit
# skill-reference context (see build_pattern). Any single-word skill name that is
# not listed here aborts the sync, so a new one gets looked at by a human instead
# of being rewritten by guesswork.
SINGLE_WORD_ALLOWLIST = {"ui", "localization"}

# Upstream root files that do not belong in the mirror: CODEOWNERS points at a Unity
# team, CONTRIBUTING.md describes the upstream PR flow, README.md is hand-written here.
EXCLUDE_ROOT = {".github", "CONTRIBUTING.md", "README.md"}

GENERATED = ("skills", "LICENSE.md", "UPSTREAM.md")

SKILLS_BEGIN = "<!-- BEGIN SKILLS -->"
SKILLS_END = "<!-- END SKILLS -->"


class SyncError(Exception):
    """A condition that must stop the sync before anything is committed."""


# --------------------------------------------------------------------------- git


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def clone_upstream(repo: str, ref: str, dest: Path) -> str:
    url = f"https://github.com/{repo}.git"
    subprocess.run(
        ["git", "clone", "--quiet", "--depth", "1", "--branch", ref, url, str(dest)],
        check=True,
    )
    return git("rev-parse", "HEAD", cwd=dest)


# -------------------------------------------------------------------- frontmatter


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        return inner.replace("''", "'") if value[0] == "'" else inner
    return value


def parse_frontmatter(text: str) -> dict[str, str]:
    """Minimal YAML frontmatter reader for the two fields we care about.

    Handles plain scalars, quoted scalars and `>`/`|` block scalars, and skips
    nested mappings and sequences (allowed-tools, required_packages).
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}

    body = lines[1:end]
    data: dict[str, str] = {}
    i = 0
    while i < len(body):
        match = re.match(r"^([A-Za-z0-9_-]+):[ \t]*(.*)$", body[i])
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).rstrip()
        i += 1
        if value in (">", ">-", ">+", "|", "|-", "|+") or value == "":
            block: list[str] = []
            while i < len(body) and (body[i][:1] in (" ", "\t") or not body[i].strip()):
                block.append(body[i].strip())
                i += 1
            # A block scalar folds into a value; a nested mapping or sequence does not.
            data[key] = " ".join(b for b in block if b) if value else ""
        else:
            data[key] = unquote(value)
    return data


def frontmatter_span(text: str) -> tuple[int, int] | None:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    return (1, end) if end is not None else None


def set_frontmatter_name(text: str, name: str) -> str:
    """Force the frontmatter `name:` field, which prose rewriting cannot reach."""
    span = frontmatter_span(text)
    if span is None:
        raise SyncError("SKILL.md has no YAML frontmatter")
    start, end = span
    lines = text.split("\n")
    for i in range(start, end):
        if re.match(r"^name:[ \t]*", lines[i]):
            lines[i] = f"name: {name}"
            return "\n".join(lines)
    raise SyncError("SKILL.md frontmatter has no `name:` field")


# A plain YAML scalar may not begin with an indicator character, contain ": " or
# " #", or end with ":". Upstream has four descriptions that break this rule.
YAML_INDICATORS = "-?:,[]{}#&*!|>'\"%@`"


def needs_quoting(value: str) -> bool:
    """Would a strict YAML parser reject this as a plain scalar?"""
    if not value:
        return False
    return (
        value[0] in YAML_INDICATORS
        or ": " in value
        or value.endswith(":")
        or " #" in value
    )


def quote_yaml(value: str) -> str:
    """Single-quoted YAML: no escape sequences are processed, only '' for a quote."""
    return "'" + value.replace("'", "''") + "'"


def quote_frontmatter_value(text: str, key: str) -> str:
    """Quote `key:`'s plain scalar if YAML would reject it, otherwise leave it alone.

    Block scalars (`>`, `|`) and already-quoted scalars are valid as they stand, so
    they are returned untouched -- which also makes this idempotent.
    """
    span = frontmatter_span(text)
    if span is None:
        return text
    start, end = span
    lines = text.split("\n")
    for i in range(start, end):
        match = re.match(rf"^{re.escape(key)}:[ \t]*(.*)$", lines[i])
        if not match:
            continue
        value = match.group(1).rstrip()
        if not value or value[0] in ">|\"'":
            return text
        if needs_quoting(value):
            lines[i] = f"{key}: {quote_yaml(value)}"
            return "\n".join(lines)
        return text
    return text


# ------------------------------------------------------------------- the renaming


def target_name(old: str) -> str:
    return old if "unity" in old.lower() else PREFIX + old


def build_pattern(mapping: dict[str, str]) -> re.Pattern[str]:
    """One alternation over every renamed skill, longest name first.

    The `(?<![\\w-])` / `(?![\\w-])` guards keep `ui` from matching inside
    `ui-uitk` and keep an already-prefixed `unity-ui` from being prefixed twice.
    Every branch matches the bare name only -- the surrounding context is all
    lookaround -- so the replacement is a plain mapping lookup on group 0.
    """
    parts: list[str] = []
    for old in sorted(mapping, key=lambda n: (-len(n), n)):
        name = re.escape(old)
        if "-" in old:
            parts.append(rf"(?<![\w-]){name}(?![\w-])")
        else:
            parts.append(
                "(?:"
                rf"(?<=`){name}(?=`)"                      # `ui`
                rf"|(?<=\*\*){name}(?=\*\*)"               # **ui**
                rf"|(?<=\(){name}(?=\))"                   # (ui)
                rf"|(?<=skills/){name}(?![\w-])"           # skills/ui
                rf"|(?<![\w-]){name}(?=/SKILL\.md)"        # ui/SKILL.md
                rf"|(?<![\w-]){name}(?= skills?(?![\w-]))" # the ui skill
                ")"
            )
    return re.compile("|".join(parts))


def rewrite(text: str, pattern: re.Pattern[str], mapping: dict[str, str]) -> str:
    return pattern.sub(lambda m: mapping[m.group(0)], text)


# ------------------------------------------------------------------- README table


def summarize(description: str, limit: int = 170) -> str:
    text = " ".join(description.split())
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = ""
    for sentence in sentences:
        candidate = f"{out} {sentence}".strip()
        if out and len(candidate) > limit:
            break
        out = candidate
        if len(out) >= 40:
            break
    if len(out) > limit:
        out = out[: limit - 1].rstrip() + "…"
    return out.replace("|", "\\|")


def render_table(rows: list[tuple[str, str]]) -> str:
    lines = ["| Skill | Description |", "|---|---|"]
    lines += [f"| `{name}` | {summarize(desc)} |" for name, desc in rows]
    return "\n".join(lines)


def update_readme(root: Path, rows: list[tuple[str, str]]) -> None:
    path = root / "README.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if SKILLS_BEGIN not in text or SKILLS_END not in text:
        return
    head, rest = text.split(SKILLS_BEGIN, 1)
    _, tail = rest.split(SKILLS_END, 1)
    path.write_text(
        f"{head}{SKILLS_BEGIN}\n{render_table(rows)}\n{SKILLS_END}{tail}",
        encoding="utf-8",
    )


# ----------------------------------------------------------------------- UPSTREAM


def render_upstream_doc(repo: str, ref: str, sha: str, mapping: dict[str, str], names: list[str]) -> str:
    rows = "\n".join(
        f"| `{old}` | `{target_name(old)}` |{' *(unchanged)*' if old == target_name(old) else ''}"
        for old in names
    )
    return f"""# Upstream

This repository is a generated mirror of
[{repo}](https://github.com/{repo}). Do not edit `skills/` here -- contribute
upstream and the next sync will pick it up.

- Upstream: `{repo}`
- Ref: `{ref}`
- Commit: `{sha}`

The only transformation is the skill name: a skill whose name does not already
contain `unity` gets a `unity-` prefix, in its folder name, in its `name:`
frontmatter field, and in every cross-reference to it from other skills.

The sync date is not recorded here on purpose -- it would produce a commit on
every run even when upstream has not moved. Use `git log` for that.

## Skill name mapping

| Upstream | This repository |
|---|---|
{rows}
"""


def read_previous_mapping(root: Path) -> dict[str, str]:
    path = root / "UPSTREAM.md"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    return {
        m.group(1): m.group(2)
        for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", text, re.M)
    }


# --------------------------------------------------------------------- validation


def collect_skills(skills_dir: Path) -> list[str]:
    if not skills_dir.is_dir():
        raise SyncError(f"no skills directory at {skills_dir}")
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir())


def validate_upstream(skills_dir: Path, names: list[str]) -> dict[str, str]:
    """Return {name: description}, raising on anything the rename cannot assume."""
    if not names:
        raise SyncError("upstream has no skills -- refusing to wipe the mirror")

    problems: list[str] = []
    descriptions: dict[str, str] = {}

    for name in names:
        skill_md = skills_dir / name / "SKILL.md"
        if not skill_md.is_file():
            problems.append(f"{name}: no SKILL.md")
            continue
        front = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if not front:
            problems.append(f"{name}: SKILL.md has no readable YAML frontmatter")
            continue
        if front.get("name") != name:
            problems.append(f"{name}: frontmatter name is {front.get('name')!r}, expected {name!r}")
        descriptions[name] = front.get("description", "")

    single_word = {n for n in names if "-" not in n and target_name(n) != n}
    unknown = sorted(single_word - SINGLE_WORD_ALLOWLIST)
    if unknown:
        problems.append(
            "new single-word skill name(s) "
            + ", ".join(repr(n) for n in unknown)
            + ": a bare word is ambiguous in prose and code, so rewriting its "
            "cross-references automatically is unsafe. Review the upstream usage, "
            "then add it to SINGLE_WORD_ALLOWLIST in tools/sync_upstream.py."
        )

    renamed: dict[str, str] = {}
    for name in names:
        new = target_name(name)
        if new != name:
            renamed[name] = new
    existing = set(names)
    for old, new in renamed.items():
        if new in existing:
            problems.append(f"{old}: renaming to {new} collides with an existing upstream skill")
    seen: dict[str, str] = {}
    for name in names:
        new = target_name(name)
        if new in seen:
            problems.append(f"{name} and {seen[new]} both map to {new}")
        seen[new] = name

    if problems:
        raise SyncError("upstream validation failed:\n  - " + "\n  - ".join(problems))
    return descriptions


# ----------------------------------------------------------------------- generate


def is_text(data: bytes) -> bool:
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return b"\0" not in data


def wipe_generated(root: Path) -> None:
    for entry in GENERATED:
        path = root / entry
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def copy_skills(src: Path, dst: Path, mapping: dict[str, str], pattern: re.Pattern[str] | None) -> None:
    for skill in sorted(p for p in src.iterdir() if p.is_dir()):
        new_name = target_name(skill.name)
        for path in sorted(skill.rglob("*")):
            if path.is_dir():
                continue
            out = dst / new_name / path.relative_to(skill)
            out.parent.mkdir(parents=True, exist_ok=True)
            data = path.read_bytes()
            if not is_text(data):
                out.write_bytes(data)
                continue
            text = data.decode("utf-8")
            if pattern is not None:
                text = rewrite(text, pattern, mapping)
            if path.name == "SKILL.md" and path.parent == skill:
                try:
                    text = set_frontmatter_name(text, new_name)
                except SyncError as exc:
                    raise SyncError(f"{skill.name}: {exc}") from exc
                text = quote_frontmatter_value(text, "description")
            out.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- check


def validate_yaml_strict(root: Path, names: list[str], require: bool) -> list[str]:
    """Parse every frontmatter with a real YAML parser.

    The hand-rolled reader above is deliberately lenient, so it cannot catch the
    thing that actually breaks installers: a plain scalar that is not valid YAML.
    """
    try:
        import yaml
    except ImportError:
        if require:
            return ["pyyaml is not installed, so strict YAML validation could not run"]
        print("note: pyyaml not installed, skipping strict YAML validation")
        return []

    problems: list[str] = []
    for name in names:
        path = root / "skills" / name / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        span = frontmatter_span(text)
        if span is None:
            problems.append(f"{name}: SKILL.md has no YAML frontmatter")
            continue
        start, end = span
        block = "\n".join(text.split("\n")[start:end])
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            detail = " ".join(str(exc).split())
            problems.append(f"{name}: SKILL.md frontmatter is not valid YAML: {detail}")
            continue
        if not isinstance(data, dict):
            problems.append(f"{name}: SKILL.md frontmatter is not a YAML mapping")
            continue
        if data.get("name") != name:
            problems.append(
                f"{name}: YAML name is {data.get('name')!r}, expected {name!r}"
            )
        if not str(data.get("description", "")).strip():
            problems.append(f"{name}: SKILL.md has no description")
    return problems


def check(root: Path, require_yaml: bool = False) -> int:
    problems: list[str] = []
    skills_dir = root / "skills"
    try:
        names = collect_skills(skills_dir)
    except SyncError as exc:
        print(f"check failed: {exc}", file=sys.stderr)
        return 1

    for name in names:
        if "unity" not in name.lower():
            problems.append(f"{name}: skill name does not contain 'unity'")
        skill_md = skills_dir / name / "SKILL.md"
        if not skill_md.is_file():
            problems.append(f"{name}: no SKILL.md")
            continue
        front = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if front.get("name") != name:
            problems.append(f"{name}: frontmatter name is {front.get('name')!r}, expected {name!r}")

    problems += validate_yaml_strict(root, names, require_yaml)

    mapping = read_previous_mapping(root)
    mapping = {old: new for old, new in mapping.items() if old != new}
    if not mapping:
        problems.append("UPSTREAM.md has no skill name mapping to check references against")
    else:
        pattern = build_pattern(mapping)
        for path in sorted(skills_dir.rglob("*")):
            if not path.is_file():
                continue
            data = path.read_bytes()
            if not is_text(data):
                continue
            text = data.decode("utf-8")
            for match in pattern.finditer(text):
                line = text[: match.start()].count("\n") + 1
                rel = path.relative_to(root)
                problems.append(
                    f"{rel}:{line}: stale reference to upstream name "
                    f"{match.group(0)!r} (should be {mapping[match.group(0)]!r})"
                )

    if problems:
        print("check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"check ok: {len(names)} skills, {len(mapping)} renamed, no stale references")
    return 0


# ---------------------------------------------------------------------------- main


def sync(root: Path, repo: str, ref: str, dry_run: bool, message_file: Path | None) -> int:
    previous = set(read_previous_mapping(root).values())

    with tempfile.TemporaryDirectory(prefix="unity-skills-upstream-") as tmp:
        upstream = Path(tmp) / "upstream"
        sha = clone_upstream(repo, ref, upstream)
        names = collect_skills(upstream / "skills")
        descriptions = validate_upstream(upstream / "skills", names)

        mapping = {n: target_name(n) for n in names if target_name(n) != n}
        pattern = build_pattern(mapping) if mapping else None

        print(f"upstream {repo}@{sha[:10]} ({ref}): {len(names)} skills, {len(mapping)} renamed")
        for old in sorted(mapping):
            print(f"  {old} -> {mapping[old]}")
        for name in sorted(n for n in names if n not in mapping):
            print(f"  {name} (unchanged)")

        if dry_run:
            print("\ndry run: nothing written")
            return 0

        wipe_generated(root)
        copy_skills(upstream / "skills", root / "skills", mapping, pattern)

        license_src = upstream / "LICENSE.md"
        if not license_src.is_file():
            raise SyncError("upstream LICENSE.md is missing")
        shutil.copyfile(license_src, root / "LICENSE.md")

        (root / "UPSTREAM.md").write_text(
            render_upstream_doc(repo, ref, sha, mapping, names), encoding="utf-8"
        )
        rows = sorted(
            (target_name(n), descriptions.get(n, "")) for n in names
        )
        update_readme(root, rows)

    current = {target_name(n) for n in names}
    added = sorted(current - previous) if previous else []
    removed = sorted(previous - current) if previous else []

    if message_file is not None:
        lines = [f"sync: {repo}@{sha[:10]}", ""]
        if added:
            lines += ["Added:"] + [f"- {n}" for n in added] + [""]
        if removed:
            lines += ["Removed:"] + [f"- {n}" for n in removed] + [""]
        lines += [f"https://github.com/{repo}/commits/{sha}", ""]
        message_file.write_text("\n".join(lines), encoding="utf-8")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"upstream_sha={sha}\n")

    print(f"\nwrote {len(names)} skills to {root / 'skills'}")
    if added:
        print("added:   " + ", ".join(added))
    if removed:
        print("removed: " + ", ".join(removed))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--upstream", default=UPSTREAM_REPO, help=f"upstream repo (default: {UPSTREAM_REPO})")
    parser.add_argument("--ref", default=UPSTREAM_REF, help=f"upstream branch (default: {UPSTREAM_REF})")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="repository root")
    parser.add_argument("--dry-run", action="store_true", help="report the rename mapping without writing")
    parser.add_argument("--check", action="store_true", help="validate the generated tree instead of syncing")
    parser.add_argument("--require-yaml", action="store_true", help="with --check, fail if pyyaml is unavailable")
    parser.add_argument("--commit-message-file", type=Path, help="write a commit message to this path")
    args = parser.parse_args(argv)

    try:
        if args.check:
            return check(args.root, args.require_yaml)
        return sync(args.root, args.upstream, args.ref, args.dry_run, args.commit_message_file)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"error: {' '.join(exc.cmd)} failed: {exc.stderr or exc.stdout}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

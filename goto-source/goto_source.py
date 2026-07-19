import re
import subprocess
import sys
from pathlib import Path

import click


def parse_path(selector: str) -> list[dict]:
    segments = []
    for part in selector.split(" > "):
        part = part.strip()
        # Each segment may optionally start with [Component] followed by element.class
        comp_match = re.match(r'^\[([^\]]+)\]\s+(.+)$', part)
        if comp_match:
            segments.append({"type": "component", "name": comp_match.group(1)})
            element_part = comp_match.group(2)
        elif part.startswith("[") and part.endswith("]"):
            segments.append({"type": "component", "name": part[1:-1]})
            continue
        else:
            element_part = part
        dot_parts = element_part.split(".")
        segments.append({"type": "element", "tag": dot_parts[0], "classes": dot_parts[1:]})
    return segments


def find_component_definition(project_root: Path, component_name: str) -> list[str]:
    """Return ['file:line', ...] for each place the component is defined."""
    pattern = rf"(?:function|const|class)\s+{re.escape(component_name)}[\s(<]"
    result = subprocess.run(
        [
            "rg", "-n", "--no-heading", "--with-filename", pattern,
            "--glob", "*.tsx", "--glob", "*.jsx", "--glob", "*.ts", "--glob", "*.js",
            "--glob", "!node_modules", "--glob", "!dist", "--glob", "!build", "--glob", "!.git",
            str(project_root),
        ],
        capture_output=True, text=True,
    )
    results = []
    for line in result.stdout.strip().splitlines():
        parts = line.split(":", 2)
        if len(parts) >= 2:
            results.append(f"{parts[0]}:{parts[1]}")
    return results


def find_component_files(project_root: Path, component_name: str) -> list[str]:
    return list({entry.rsplit(":", 1)[0] for entry in find_component_definition(project_root, component_name)})


def all_jsx_files(project_root: Path) -> list[str]:
    result = subprocess.run(
        [
            "rg", "--files",
            "--glob", "*.tsx", "--glob", "*.jsx",
            "--glob", "!node_modules", "--glob", "!dist", "--glob", "!build", "--glob", "!.git",
            str(project_root),
        ],
        capture_output=True, text=True,
    )
    return result.stdout.strip().splitlines() if result.stdout.strip() else []


def find_opening_tag(file_path: str, from_line: int, tag: str, max_lookback: int = 30) -> int | None:
    """Scan backwards from from_line to find the nearest opening <tag line."""
    try:
        with open(file_path) as f:
            lines = f.readlines()
        for i in range(from_line - 1, max(0, from_line - 1 - max_lookback) - 1, -1):
            if f"<{tag}" in lines[i]:
                return i + 1  # 1-indexed
    except OSError:
        pass
    return None


def find_element_in_files(files: list[str], tag: str, classes: list[str], project_root: Path) -> list[str]:
    if not files:
        return []

    results = set()

    for class_name in classes:
        # Match inline string: className="... segment ..." (word boundary to avoid segmentActive)
        inline_pattern = rf'className=["\'\`][^"\'\`]*\b{re.escape(class_name)}\b'
        # Match CSS modules / template expressions: .segment (property access)
        modules_pattern = rf'\.{re.escape(class_name)}\b'

        for pattern in [inline_pattern, modules_pattern]:
            cmd = ["rg", "-n", "--no-heading", "--with-filename", pattern] + files
            result = subprocess.run(cmd, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split(":", 2)
                if len(parts) < 3:
                    continue
                file_path, line_no_str, content = parts
                line_no = int(line_no_str)

                if f"<{tag}" in content:
                    tag_line = line_no
                else:
                    tag_line = find_opening_tag(file_path, line_no, tag)

                if tag_line is not None:
                    results.add(f"{file_path}:{tag_line}")

    return sorted(results)


@click.command()
@click.argument("selector")
@click.argument("project_root", default=".", type=click.Path(exists=True, file_okay=False))
def main(selector: str, project_root: str):
    """Find the source location of a JSX element from a chrome-copy-dom selector path."""
    root = Path(project_root).resolve()
    selector = selector.strip("`")
    segments = parse_path(selector)

    if not segments or segments[-1]["type"] != "element":
        click.echo("Error: selector must end with an HTML element (e.g. p.taskSummary)", err=True)
        sys.exit(1)

    target = segments[-1]
    tag = target["tag"]
    classes = target["classes"]

    component_name = None
    for seg in reversed(segments[:-1]):
        if seg["type"] == "component":
            component_name = seg["name"]
            break

    if component_name:
        files = find_component_files(root, component_name)
        if not files:
            click.echo(
                f"No files found for component '{component_name}', searching all JSX/TSX files...",
                err=True,
            )
            files = all_jsx_files(root)
    else:
        files = all_jsx_files(root)

    if not files:
        click.echo("No JSX/TSX files found in project.", err=True)
        sys.exit(1)

    element_segments = [s for s in segments if s["type"] == "element"]
    matches = []
    for seg in reversed(element_segments):
        matches = find_element_in_files(files, seg["tag"], seg["classes"], root)
        if matches:
            break

    if not matches and component_name:
        matches = find_component_definition(root, component_name)

    if not matches:
        desc = f"<{tag}> with class(es) {classes}"
        click.echo(f"No matches found for {desc}", err=True)
        sys.exit(1)

    for match in matches:
        click.echo(match)

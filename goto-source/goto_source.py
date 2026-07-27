import re
import subprocess
import sys
from pathlib import Path

import click

EXCLUDE_GLOBS = [
    "--glob",
    "!node_modules",
    "--glob",
    "!dist",
    "--glob",
    "!build",
    "--glob",
    "!.git",
]
SOURCE_GLOBS = [
    "--glob",
    "*.tsx",
    "--glob",
    "*.jsx",
    "--glob",
    "*.ts",
    "--glob",
    "*.js",
]
JSX_GLOBS = ["--glob", "*.tsx", "--glob", "*.jsx"]


def rg(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["rg", "--no-heading", *args], capture_output=True, text=True
    )
    return result.stdout.splitlines()


def parse_path(selector: str) -> list[dict]:
    """Parse a selector into element levels, each paired with its nearest component ancestor.

    Segments look like `div.classA` optionally prefixed with `[Component]`.
    """
    levels = []
    component = None
    for part in selector.split(" > "):
        part = part.strip()
        if part.startswith("["):
            component, _, part = part[1:].partition("]")
            part = part.strip()
        if part:
            tag, *classes = part.split(".")
            levels.append({"tag": tag, "classes": classes, "component": component})
    return levels


def find_component_definition(project_root: Path, component_name: str) -> list[str]:
    """Return ['file:line', ...] for each place the component is defined."""
    pattern = rf"(?:function|const|class)\s+{re.escape(component_name)}[\s(<]"
    lines = rg(
        [
            "-n",
            "--with-filename",
            pattern,
            *SOURCE_GLOBS,
            *EXCLUDE_GLOBS,
            str(project_root),
        ]
    )
    return [":".join(line.split(":")[:2]) for line in lines]


def find_component_files(project_root: Path, component_name: str) -> list[str]:
    return sorted(
        {
            entry.rsplit(":", 1)[0]
            for entry in find_component_definition(project_root, component_name)
        }
    )


def find_opening_tag(
    file_path: str, from_line: int, tag: str, max_lookback: int = 30
) -> int | None:
    """Scan backwards from from_line to find the nearest opening <tag line."""
    try:
        with open(file_path) as f:
            lines = f.readlines()
    except OSError:
        return None
    for i in range(from_line - 1, max(0, from_line - 1 - max_lookback) - 1, -1):
        if f"<{tag}" in lines[i]:
            return i + 1  # 1-indexed
    return None


def find_element_in_files(
    files: list[str], tag: str, classes: list[str], project_root: Path
) -> list[str]:
    targets = files or [*JSX_GLOBS, *EXCLUDE_GLOBS, str(project_root)]
    results = set()
    for class_name in classes:
        patterns = [
            # Inline string: className="... segment ..." (word boundary to avoid segmentActive)
            rf'className=["\'`][^"\'`]*\b{re.escape(class_name)}\b',
            # CSS modules / template expressions: .segment (property access)
            rf"\.{re.escape(class_name)}\b",
        ]
        for pattern in patterns:
            for line in rg(["-n", "--with-filename", pattern, *targets]):
                file_path, line_no, content = line.split(":", 2)
                tag_line = (
                    int(line_no)
                    if f"<{tag}" in content
                    else find_opening_tag(file_path, int(line_no), tag)
                )
                if tag_line is not None:
                    results.add((file_path, tag_line))
    return [f"{file_path}:{line_no}" for file_path, line_no in sorted(results)]


@click.command()
@click.argument("selector")
@click.argument(
    "project_root", default=".", type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "--all",
    "all_levels",
    is_flag=True,
    help="Return matches at every level of the path, deepest first.",
)
def main(selector: str, project_root: str, all_levels: bool):
    """Find the source location of a JSX element from a chrome-copy-dom selector path."""
    root = Path(project_root).resolve()
    levels = parse_path(selector.strip("`"))

    if not levels:
        click.echo(
            "Error: selector must contain an HTML element (e.g. p.taskSummary)",
            err=True,
        )
        sys.exit(1)

    # Cache files per component to avoid redundant rg calls.
    files_cache: dict[str | None, list[str]] = {}

    def files_for(component: str | None) -> list[str]:
        if component not in files_cache:
            files = find_component_files(root, component) if component else []
            if component and not files:
                click.echo(
                    f"No files found for component '{component}', searching all JSX/TSX files...",
                    err=True,
                )
            files_cache[component] = files
        return files_cache[component]

    matches: list[str] = []
    for level in reversed(levels):
        found = find_element_in_files(
            files_for(level["component"]), level["tag"], level["classes"], root
        )
        matches += [m for m in found if m not in matches]
        if matches and not all_levels:
            break

    # Fall back to the target's nearest component definition.
    if not matches and levels[-1]["component"]:
        matches = find_component_definition(root, levels[-1]["component"])

    if not matches:
        click.echo("No matches found.", err=True)
        sys.exit(1)

    click.echo("\n".join(matches))


if __name__ == "__main__":
    main()

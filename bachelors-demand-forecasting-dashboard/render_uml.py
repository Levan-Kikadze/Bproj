#!/usr/bin/env python3
"""Render Mermaid UML sources into SVG and PNG assets.

Usage:
    python render_uml.py
"""

from __future__ import annotations

import base64
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MERMAID_HOST = "https://mermaid.ink"
UML_DIR = Path(__file__).parent / "docs" / "assets" / "uml_diagrams"
DIAGRAMS = [
    "component_diagram",
    "deployment_diagram",
    "sequence_diagram",
]


def encode_mermaid(source_text: str) -> str:
    raw = source_text.encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii")
    return encoded.rstrip("=")


def fetch(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
            "Accept": "image/svg+xml,image/png,*/*",
        },
    )
    with urlopen(request) as response:  # nosec B310: trusted read-only fetch
        return response.read()


def render_one(diagram_name: str) -> None:
    source_path = UML_DIR / f"{diagram_name}.mmd"
    if not source_path.exists():
        raise FileNotFoundError(f"Missing source file: {source_path}")

    source_text = source_path.read_text(encoding="utf-8")
    encoded = encode_mermaid(source_text)

    svg_url = f"{MERMAID_HOST}/svg/{encoded}"
    png_url = f"{MERMAID_HOST}/img/{encoded}"

    svg_target = UML_DIR / f"{diagram_name}.svg"
    png_target = UML_DIR / f"{diagram_name}.png"

    svg_target.write_bytes(fetch(svg_url))
    png_target.write_bytes(fetch(png_url))

    print(f"Rendered {diagram_name} -> {svg_target.name}, {png_target.name}")


def main() -> int:
    UML_DIR.mkdir(parents=True, exist_ok=True)

    try:
        for diagram_name in DIAGRAMS:
            render_one(diagram_name)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1
    except (HTTPError, URLError, OSError) as exc:
        print(f"Rendering failed: {exc}")
        return 2

    print("All UML diagrams rendered successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

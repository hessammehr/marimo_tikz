"""Render TikZ pictures as SVG images in marimo notebooks.

Pipeline: LuaTeX -> PDF -> dvisvgm -> SVG, embedded as an ``<img>``.
"""

from __future__ import annotations

import base64
import functools
import hashlib
import pathlib
import re
import subprocess
import tempfile

import marimo as mo

__all__ = ["TikzError", "tikz", "tikz_svg"]
__version__ = "0.2.0"

_MISSING = {
    "lualatex": "texlive-latex-base texlive-latex-extra texlive-luatex texlive-pictures",
    "dvisvgm": "dvisvgm",
}


class TikzError(RuntimeError):
    """LaTeX or dvisvgm failed - the message holds the relevant log lines."""


def _run(cmd: list[str], cwd: pathlib.Path, timeout: int) -> subprocess.CompletedProcess:
    """Run a toolchain command, reporting a missing binary as a TikzError."""
    try:
        return subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise TikzError(
            f"{cmd[0]} not found on PATH; install it "
            f"(Debian/Ubuntu: apt install {_MISSING[cmd[0]]})"
        ) from exc


@functools.lru_cache(maxsize=256)
def tikz_svg(
    code: str,
    libraries: tuple[str, ...] = (),
    preamble: str = "",
    border: str = "4pt",
    timeout: int = 60,
) -> str:
    r"""Compile a TikZ picture to an SVG string (LuaTeX -> PDF -> dvisvgm).

    Results are cached, so re-rendering an unchanged picture is free.

    Args:
        code: the picture, e.g. ``r"\begin{tikzpicture}...\end{tikzpicture}"``.
        libraries: TikZ libraries to load, e.g. ``("arrows.meta", "calc")``.
        preamble: extra preamble lines, e.g. ``r"\usepackage{tikz-cd}"``.
        border: whitespace added around the tight bounding box.
        timeout: per-subprocess timeout in seconds.

    Raises:
        TikzError: if a tool is missing from PATH, or LaTeX or dvisvgm fails.
    """
    libs = f"\\usetikzlibrary{{{','.join(libraries)}}}\n" if libraries else ""
    doc = (
        f"\\documentclass[border={border}]{{standalone}}\n"
        f"\\usepackage{{tikz}}\n{preamble}\n{libs}"
        f"\\begin{{document}}\n{code}\n\\end{{document}}\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        (d / "doc.tex").write_text(doc)
        tex = _run(
            ["lualatex", "-interaction=nonstopmode", "-halt-on-error",
             "-no-shell-escape", "doc.tex"],
            d, timeout,
        )
        if tex.returncode != 0 or not (d / "doc.pdf").exists():
            log = (d / "doc.log").read_text(errors="replace")
            hits = "\n".join(ln for ln in log.splitlines() if ln.startswith("!"))
            raise TikzError(hits or log[-1200:])
        conv = _run(
            ["dvisvgm", "--pdf", "--no-fonts", "--optimize",
             "-o", "doc.svg", "doc.pdf"],
            d, timeout,
        )
        if not (d / "doc.svg").exists():
            raise TikzError(conv.stderr[-1200:])
        svg = (d / "doc.svg").read_text()

    # dvisvgm reuses ids like "g0-72" across documents; namespace them so that several
    # diagrams can share a page when the SVG is embedded inline rather than as an <img>.
    tag = "tz" + hashlib.sha1(doc.encode()).hexdigest()[:8]
    for name in sorted(set(re.findall(r"id='([^']+)'", svg)), key=len, reverse=True):
        svg = (svg.replace(f"id='{name}'", f"id='{tag}-{name}'")
                  .replace(f"href='#{name}'", f"href='#{tag}-{name}'")
                  .replace(f"url(#{name})", f"url(#{tag}-{name})"))
    return svg


def tikz(
    code: str,
    *,
    libraries: tuple[str, ...] = (),
    preamble: str = "",
    border: str = "4pt",
    scale: float = 1.0,
    center: bool = True,
    caption: str | None = None,
    alt: str = "TikZ figure",
) -> mo.Html:
    r"""Render a TikZ picture as an SVG image.

    The SVG is handed to :func:`marimo.image` as a ``data:`` URI so that it lands in the
    DOM as a real ``<img>``: marimo's right-click menu only offers "Copy image" /
    "Download image" when the event target is an ``HTMLImageElement``, which an inline
    ``<svg>`` is not. This works because ``dvisvgm --no-fonts`` traces glyphs into
    paths, leaving a self-contained document - a ``data:`` URI cannot fetch external
    fonts.

    Args:
        code: the picture, e.g. ``r"\begin{tikzpicture}...\end{tikzpicture}"``.
        libraries: TikZ libraries to load, e.g. ``("arrows.meta", "calc")``.
        preamble: extra preamble lines, e.g. ``r"\usepackage{tikz-cd}"``.
        border: whitespace added around the tight bounding box.
        scale: display scale factor (the SVG stays vector, nothing is resampled).
        center: center the figure in the output area.
        caption: optional caption rendered under the figure.
        alt: alt text for the image.
    """
    svg = tikz_svg(code, tuple(libraries), preamble, border)

    if scale != 1.0:
        svg = re.sub(
            r"(width|height)='([0-9.]+)pt'",
            lambda m: f"{m.group(1)}='{float(m.group(2)) * scale:.6g}pt'",
            svg,
            count=2,
        )

    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    # SVG ink is black; flip it (hue-preserving) when marimo is in dark mode.
    style = (
        {"filter": "invert(1) hue-rotate(180deg)"}
        if mo.app_meta().theme == "dark"
        else None
    )
    img = mo.image(uri, alt=alt, caption=caption, style=style)
    return mo.center(img) if center else img

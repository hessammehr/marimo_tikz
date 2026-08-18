# marimo_tikz

TikZ pictures as SVG images in [marimo](https://marimo.io) notebooks.
Needs `lualatex` and `dvisvgm` on `PATH` (Debian/Ubuntu:
`apt install texlive-latex-base texlive-latex-extra texlive-luatex texlive-pictures dvisvgm`).

```python
from marimo_tikz import tikz

tikz(
    r"""
\begin{tikzpicture}[>={Stealth[round]}]
  \node[draw,rounded corners,fill=blue!10] (a) {TikZ};
  \node[draw,rounded corners,fill=green!10,right=2cm of a] (b) {marimo};
  \draw[->,thick] (a) -- (b) node[midway,above,font=\small] {svg};
\end{tikzpicture}
""",
    libraries=("arrows.meta", "positioning"),
    scale=1.4,
)
```

Extra packages go through `preamble`:

```python
tikz(
    r"""
\begin{tikzcd}
  A \arrow[r, "f"] \arrow[d, "g"'] & B \arrow[d, "h"] \\
  C \arrow[r, "k"'] & D
\end{tikzcd}
""",
    preamble=r"\usepackage{tikz-cd}",
)
```

`tikz(...)` also shows Download SVG / PDF / TikZ / preamble buttons; pass
`downloads=False` to hide them. `tikz_svg(...)` returns the raw SVG string instead.
Both are LRU-cached.

## Example notebook

```sh
uvx marimo edit --sandbox examples/notebook.py
```

A microscope light path, the same picture driven by sliders, and `tikz-cd` / `pgfplots`
via `preamble`.

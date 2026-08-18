# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.23.16",
#     "marimo-tikz",
# ]
#
# [tool.uv.sources]
# marimo-tikz = { git = "https://github.com/hessammehr/marimo_tikz" }
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    from marimo_tikz import tikz

    return mo, tikz


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # TikZ &rarr; SVG in marimo

    `tikz(...)` comes from [marimo_tikz](https://github.com/hessammehr/marimo_tikz),
    declared as a PEP 723 dependency in this notebook's script header. It compiles a
    TikZ picture with **LuaTeX** into a **PDF**, converts it to **SVG** with `dvisvgm`,
    and embeds it as an `<img>`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A widefield microscope, drawn to scale
    """)
    return


@app.cell(hide_code=True)
def _(tikz):
    _picture = r"""
    \begin{tikzpicture}[>={Stealth[round]},font=\small,
      lens/.style={draw=cyan!55!black,fill=cyan!12,thick},
      ray/.style={red!70!black,line width=0.5pt,opacity=0.85}]
      \def\xobj{1.0}\def\hobj{0.5}\def\xa{3.4}\def\ha{1.2}
      \def\xb{6.4}\def\hb{1.85}\def\xc{9.0}\def\him{0.5417}
      \draw[gray!60,dashed] (0.2,0) -- (10.0,0);
      \foreach \y in {1.0,0.0,-1.0}{
        \draw[ray] (\xobj,\hobj) -- (\xa,\y);
        \draw[ray] (\xa,\y) -- (\xb,{\y-0.625});
        \draw[ray] (\xb,{\y-0.625}) -- (\xc,-\him);
      }
      \draw[lens] (\xa,0) ellipse [x radius=0.17, y radius=\ha];
      \draw[lens] (\xb,0) ellipse [x radius=0.17, y radius=\hb];
      \draw[->,very thick] (\xobj,0) -- (\xobj,\hobj);
      \draw[->,very thick] (\xc,0) -- (\xc,-\him);
      \draw[gray!70] (\xobj,-0.9) -- (\xobj,0.9);
      \fill[gray!25,draw=gray!70] (\xc-0.09,-1.2) rectangle (\xc+0.09,1.2);
      \node[below=2pt,align=center] at (\xobj,-0.95) {Sample\\[-3pt]\tiny front focal plane};
      \node[below=2pt,align=center] at (\xa,-\ha) {Objective\\[-3pt]\tiny$f_{\mathrm{obj}}$};
      \node[below=2pt,align=center] at (\xb,-\hb) {Tube lens\\[-3pt]\tiny$f_{\mathrm{tube}}$};
      \node[below=2pt,align=center] at (\xc,-1.25) {Camera\\[-3pt]\tiny image plane};
      \draw[decorate,decoration={brace,amplitude=4pt},gray!80]
        (\xb,2.15) -- (\xa,2.15) node[midway,above=4pt,gray!50!black] {infinity space};
    \end{tikzpicture}
    """

    tikz(_picture, libraries=("arrows.meta", "decorations.pathreplacing"), scale=1.4)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reactive TikZ

    The picture is just a string, so anything that builds strings can drive it. Move a
    slider and marimo recompiles the figure; identical parameter sets hit the LRU cache.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    f_tube = mo.ui.slider(
        1.6, 5.0, step=0.2, value=2.6, label="tube lens $f_{tube}$ (cm)", debounce=True
    )
    n_rays = mo.ui.slider(2, 9, step=1, value=3, label="rays traced", debounce=True)

    mo.hstack([f_tube, n_rays], justify="start", gap=2)
    return f_tube, n_rays


@app.cell(hide_code=True)
def _(f_tube, n_rays, tikz):
    def scope_picture(f_tube: float, n_rays: int, f_obj: float = 2.4, h_obj: float = 0.5) -> str:
        """Build an infinity-corrected two-lens light path for the given parameters."""
        x_obj, x_a, gap, h_a = 1.0, 3.4, 3.0, 1.2
        x_b = x_a + gap
        drop = -h_obj / f_obj * gap           # collimated bundle tilt across infinity space
        x_c = x_b + f_tube                    # image forms at the tube lens' back focal plane
        h_im = f_tube * h_obj / f_obj         # magnified, inverted image height
        ys = [h_a * (1 - 2 * i / (n_rays - 1)) for i in range(n_rays)] if n_rays > 1 else [0.0]
        h_b = max(abs(y + drop) for y in ys) + 0.25
        h_cam = max(1.2, h_im + 0.35)
        h_top = max(h_b, h_a) + 0.3

        defs = (
            rf"\def\xobj{{{x_obj}}}\def\hobj{{{h_obj}}}\def\xa{{{x_a}}}\def\ha{{{h_a}}}"
            rf"\def\xb{{{x_b}}}\def\hb{{{h_b:.3f}}}\def\xc{{{x_c:.3f}}}\def\him{{{h_im:.3f}}}"
            rf"\def\drop{{{drop:.3f}}}\def\hcam{{{h_cam:.3f}}}\def\htop{{{h_top:.3f}}}"
            rf"\def\fobj{{{f_obj:.1f}}}\def\ftube{{{f_tube:.1f}}}\def\mag{{{f_tube / f_obj:.2f}}}"
            rf"\def\rays{{{','.join(f'{y:.3f}' for y in ys)}}}"
        )
        return defs + r"""
    \begin{tikzpicture}[>={Stealth[round]},font=\small,
      lens/.style={draw=cyan!55!black,fill=cyan!12,thick},
      ray/.style={red!70!black,line width=0.5pt,opacity=0.85}]
      \draw[gray!60,dashed] (0.2,0) -- ({\xc+1.0},0);
      \foreach \y in \rays {
        \draw[ray] (\xobj,\hobj) -- (\xa,\y);
        \draw[ray] (\xa,\y) -- (\xb,{\y+\drop});
        \draw[ray] (\xb,{\y+\drop}) -- (\xc,-\him);
      }
      \draw[lens] (\xa,0) ellipse [x radius=0.17, y radius=\ha];
      \draw[lens] (\xb,0) ellipse [x radius=0.17, y radius=\hb];
      \draw[->,very thick] (\xobj,0) -- (\xobj,\hobj);
      \draw[->,very thick] (\xc,0) -- (\xc,-\him);
      \draw[gray!70] (\xobj,-0.9) -- (\xobj,0.9);
      \fill[gray!25,draw=gray!70] ({\xc-0.09},-\hcam) rectangle ({\xc+0.09},\hcam);
      \node[below=2pt,align=center] at (\xobj,-0.95) {Sample};
      \node[below=2pt,align=center] at (\xa,-\ha) {Objective\\[-3pt]\tiny$f_{\mathrm{obj}}=\fobj$};
      \node[below=2pt,align=center] at (\xb,-\hb) {Tube lens\\[-3pt]\tiny$f_{\mathrm{tube}}=\ftube$};
      \node[below=2pt,align=center] at (\xc,{-\hcam-0.05}) {Camera};
      \draw[decorate,decoration={brace,amplitude=4pt},gray!80]
        (\xb,\htop) -- (\xa,\htop) node[midway,above=4pt,gray!50!black] {infinity space};
      \node[anchor=west,gray!40!black] at (0.2,{\htop+0.6})
        {$M=f_{\mathrm{tube}}/f_{\mathrm{obj}}=\mag\times$};
    \end{tikzpicture}
    """


    tikz(
        scope_picture(f_tube.value, n_rays.value),
        libraries=("arrows.meta", "decorations.pathreplacing"),
        scale=1.4,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Extra packages via `preamble`
    """)
    return


@app.cell(hide_code=True)
def _(mo, tikz):
    mo.hstack(
        [
            tikz(
                r"""
    \begin{tikzcd}[row sep=large, column sep=large]
      \mathcal{O} \arrow[r, "\mathrm{PSF}*"] \arrow[d, "\mathcal{F}"'] & I
        \arrow[d, "\mathcal{F}"] \\
      \tilde{\mathcal{O}} \arrow[r, "\cdot\,\mathrm{OTF}"'] & \tilde{I}
    \end{tikzcd}""",
                preamble=r"\usepackage{tikz-cd}",
                scale=1.3,
            ),
            tikz(
                r"""
    \begin{tikzpicture}
      \begin{axis}[width=6.4cm,height=4.6cm,domain=-4:4,samples=120,
          xlabel={$x$ (\textmu m)},ylabel={intensity},axis lines=left,
          legend style={font=\tiny,draw=none},tick label style={font=\tiny},
          label style={font=\small}]
        \addplot[thick,blue!70!black]{exp(-x^2/(2*0.6^2))};
        \addlegendentry{$\mathrm{NA}=1.4$}
        \addplot[thick,red!70!black,dashed]{exp(-x^2/(2*1.3^2))};
        \addlegendentry{$\mathrm{NA}=0.65$}
      \end{axis}
    \end{tikzpicture}""",
                preamble=r"\usepackage{pgfplots}\pgfplotsset{compat=1.18}",
                scale=1.1,
            ),
        ],
        justify="center",
        gap=2,
        wrap=True,
    )
    return


if __name__ == "__main__":
    app.run()

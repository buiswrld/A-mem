"""Paper figures, generated from the frozen analyses and the judged rows.

    uv run python -m scripts.make_figures --all
    uv run python -m scripts.make_figures --fig contrasts

Read-only. Parses `analysis/frozen/*.txt` and `results/*.judged.jsonl`; never
writes into `analysis/frozen/` and never re-runs generation, judging, or the
bootstrap. Output is vector PDF in `paper/figures/`.

Every figure must trace to a frozen file or to `analysis/sensitivity/`. A figure
whose numbers cannot be pointed at a file in `results/frozen_manifest.json` does
not go in the paper.

Sizing targets GenAI4Health @ NeurIPS 2026: single column, `textwidth=5.5in`.
Include full-width figures with `\\includegraphics[width=\\textwidth]{...}` and do
not scale -- the figure is authored at final print size so the font sizes set in
RC below are the font sizes the reviewer sees.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
FROZEN_DIR = ROOT / "analysis/frozen"
SENSITIVITY_DIR = ROOT / "analysis/sensitivity"
RESULTS_DIR = ROOT / "results"
OUTPUT_DIR = ROOT / "paper/figures"

# --------------------------------------------------------------------------
# house style -- one block, every figure, so the set reads as one system
# --------------------------------------------------------------------------

TEXTWIDTH_IN = 5.5   # neurips_2026.sty geometry
HALFWIDTH_IN = 2.65  # side-by-side pair with a gutter

RC = {
    # Times-ish, to sit inside NeurIPS body text without looking pasted in.
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    # Nothing below 7pt at final size. Caption text is 9pt; stay under it.
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    # Recessive chrome. The data is the only thing with weight.
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#c3c2b7",
    "axes.linewidth": 0.6,
    "xtick.color": "#898781",
    "ytick.color": "#898781",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "axes.labelcolor": "#0b0b0b",
    "text.color": "#0b0b0b",
    "grid.color": "#e1e0d9",
    "grid.linewidth": 0.5,
    "legend.frameon": False,
    "lines.linewidth": 1.2,
    "figure.dpi": 200,
    # Type 42 = embedded TrueType. Type 3 fails NeurIPS font-embedding checks.
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.01,
    "savefig.transparent": False,
}

# Validated with the dataviz palette validator (light surface, --pairs all):
# CVD separation PASS (worst 8.7 deutan), normal-vision PASS (worst 16.3).
# Two standing obligations from that run:
#   - C2's amber is 2.11:1 against the surface -> WARN. Relief is direct value
#     labels on every marked bar plus the corresponding table in the paper.
#     Do not drop the labels to reduce clutter.
#   - C5's gray is below the chroma floor. That is deliberate: the placebo arm
#     should read as absence-of-treatment. It carries a hatch as its secondary
#     encoding so identity never rests on the gray alone.
PALETTE = {
    "C1": "#e34948",  # broken organism, untreated
    "C2": "#eda100",  # corrective system prompt
    "C3": "#2a78d6",  # corrective retrieval -- the focal condition
    "C5": "#898781",  # placebo retrieval (deliberately desaturated)
    "C6": "#4a3aa7",  # healthy base model
}
HATCH = {"C5": "///"}
LABELS = {
    "C1": "C1 broken",
    "C2": "C2 prompt",
    "C3": "C3 retrieval",
    "C5": "C5 placebo",
    "C6": "C6 healthy",
}
# C4 is omitted from every figure on purpose: its generations are byte-identical
# to C3's across all 5,640 rows, so a C4 bar is a duplicate C3 bar wearing a
# different label. Say this in the caption of the first figure that omits it.
PLOT_ORDER = ("C1", "C2", "C3", "C5", "C6")

INK = "#0b0b0b"
MUTED = "#898781"
RULE = "#c3c2b7"

# --------------------------------------------------------------------------
# readers -- the frozen .txt files are the numerical source of truth
# --------------------------------------------------------------------------

Estimate = collections.namedtuple("Estimate", "point lo hi")

_RATE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z0-9-]+)\s+(?P<point>-?[\d.]+)%\s+"
    r"pct \[\s*(?P<plo>-?[\d.]+)%,\s*(?P<phi>-?[\d.]+)%\]\s+"
    r"BCa \[\s*(?P<lo>-?[\d.]+)%,\s*(?P<hi>-?[\d.]+)%\]"
)

# Section header -> the name this module uses for that endpoint.
_SECTIONS = {
    "Harm rate": "harm",
    "Recovery": "recovery",
    "Refusal rate": "refusal",
    "Low-coherence/off-topic": "derailed",
    "Paired rate differences": "contrasts",
}


def _section_name(line: str) -> str | None:
    for prefix, name in _SECTIONS.items():
        if line.startswith(prefix):
            return name
    return None


def read_frozen(group: str) -> dict[str, dict[str, Estimate]]:
    """Parse one `analysis/frozen/<group>.txt` into {endpoint: {key: Estimate}}.

    Condition rates land under 'harm'/'recovery'/'refusal'/'derailed' keyed by
    condition ('C3'). Paired differences land under 'harm_diff'/'refusal_diff'/
    'derailed_diff' keyed by contrast ('C3-C1'). BCa bounds are used throughout;
    the percentile columns are parsed but discarded so a caller cannot mix them.
    """
    path = FROZEN_DIR / f"{group}.txt"
    out: dict[str, dict[str, Estimate]] = collections.defaultdict(dict)
    section, in_contrasts, sub = None, False, None

    for line in path.read_text().splitlines():
        name = _section_name(line.strip())
        if name == "contrasts":
            in_contrasts, section = True, None
            continue
        if name:
            section, sub = name, None
            continue
        if in_contrasts:
            stripped = line.strip()
            for prefix, endpoint in (
                ("Harm", "harm"), ("Refusal", "refusal"),
                ("Low-coherence/off-topic", "derailed"),
            ):
                if stripped.startswith(prefix) and "contrast" not in stripped:
                    sub = f"{endpoint}_diff"
        m = _RATE_RE.match(line)
        if not m:
            continue
        target = sub if in_contrasts else section
        if target is None or m.group("key") in {"cond", "contrast"}:
            continue
        out[target][m.group("key")] = Estimate(
            float(m.group("point")), float(m.group("lo")), float(m.group("hi"))
        )
    return dict(out)


def read_judged(pattern: str) -> list[dict]:
    """Judged rows for every run matching a glob, e.g. 'C1-msb_test_180-*'."""
    rows: list[dict] = []
    for path in sorted(RESULTS_DIR.glob(f"{pattern}.judged.jsonl")):
        with path.open() as fh:
            rows.extend(json.loads(line) for line in fh if line.strip())
    return rows


def save(fig, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.pdf"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------

TIERS = (("tier_c_episodic", "Tier C\nnon-clinical"),
         ("tier_d_episodic", "Tier D\nharmful clinical"),
         ("tier_o_episodic", "Tier O\nbenign clinical"))


def fig_headline() -> None:
    """Figure 2: the harm result across conditions and tiers.

    TODO -- yours. This is the figure a reviewer looks at before reading a word,
    and the encoding decision is not cosmetic.

    Data is already loaded below: `data[group]['harm'][cond]` is an Estimate with
    .point/.lo/.hi in percentage points, BCa 95%.

    The decision -- levels or contrasts?

      a) Grouped bars, three tier panels, five conditions per panel, BCa whiskers.
         Shows absolute harm, so a reader sees that C3 at 15.1% on Tier D is still
         far above C6 at 0.1%. Costs: fifteen bars, and the eye compares bar
         heights across panels whose stories differ.

      b) Dot-and-interval (one row per condition, three panels). Same information,
         far less ink, intervals become the primary object rather than a whisker
         stuck on a bar. Reads as a statistics figure rather than a benchmark
         table. Weaker as a "look how much it drops" visual.

      c) Bars for the three treatments only (C2/C3/C5), with C1 and C6 drawn as
         horizontal dashed reference rules labelled at the right edge. This says
         what the study actually claims -- treatments live between a floor and a
         ceiling -- and drops the categorical load from five to three. Costs: two
         conditions stop being directly comparable as marks.

    (c) is the strongest argument and the least conventional; (a) is what a
    reviewer expects. Whichever you pick, the constraints are fixed:
      - order conditions PLOT_ORDER, never by value -- color follows the entity;
      - C5 gets HATCH['C5'] as its secondary encoding;
      - direct value labels on the marks (this discharges the contrast WARN);
      - y axis is 0-100 on all three panels, or say in the caption that it is not;
      - one shared legend for the figure, not one per panel.
    """
    data = {group: read_frozen(group) for group, _ in TIERS}
    raise NotImplementedError("see the TODO above")


def fig_contrasts() -> None:
    """Figure 3: paired differences against C3, as a forest plot.

    Worked example -- pattern-match `fig_headline` off this one. Paired contrasts
    with intervals are exactly what a forest plot is for: one row per comparison,
    a zero rule, and the reader's whole job is 'does this interval cross zero'.
    """
    contrasts = ("C3-C1", "C3-C2", "C3-C5", "C3-C6")
    fig, axes = plt.subplots(
        1, 3, figsize=(TEXTWIDTH_IN, 1.9), sharex=True, sharey=True
    )

    for ax, (group, tier_label) in zip(axes, TIERS):
        est = read_frozen(group)["harm_diff"]
        for row, contrast in enumerate(contrasts):
            e = est[contrast]
            y = len(contrasts) - row - 1
            # The comparison condition carries the color; C3 is the constant.
            color = PALETTE[contrast.split("-")[1]]
            crosses_zero = e.lo <= 0 <= e.hi
            ax.plot([e.lo, e.hi], [y, y], color=color, lw=1.4,
                    solid_capstyle="round", zorder=2)
            ax.plot([e.point], [y], "o", ms=4.5, color=color,
                    markerfacecolor="#fcfcfb" if crosses_zero else color,
                    markeredgewidth=1.2, zorder=3)

        ax.axvline(0, color=RULE, lw=0.7, zorder=1)
        ax.set_title(tier_label.replace("\n", " "), color=INK, pad=4)
        ax.set_yticks(range(len(contrasts)))
        ax.set_yticklabels([f"C3 − {c.split('-')[1]}" for c in reversed(contrasts)])
        ax.set_xlabel("harm difference (pp)")
        ax.tick_params(length=2.5)

    axes[0].set_ylim(-0.6, len(contrasts) - 0.4)
    fig.text(0.5, -0.16,
             "Hollow markers denote intervals covering zero. "
             "BCa 95%, 2,000 shared paired draws, seed 0.",
             ha="center", color=MUTED, fontsize=7)
    fig.tight_layout(w_pad=1.2)
    save(fig, "fig3_contrasts")


def fig_coherence_masspoint() -> None:
    """Figure 4: the judge's coherence distribution, and the floor sitting on it.

    TODO -- yours, and it is the most persuasive panel available. The claim in
    results.md §3.7 is that 98-99% of `derailed` rows sit at coherence == 50, so
    the endpoint turns on `<=` versus `<` applied to a mass point. A histogram
    makes that undeniable in a way the sentence does not.

    `rows` below has every judged row for one tier with .coherence and .condition.

    What has to be true of the drawing:
      - the spike at exactly 50 must not be swallowed by binning. Equal-width bins
        across 0-100 will hide it; either bin at width 1, or draw the continuous
        part as a histogram and the mass point as its own annotated bar;
      - show at least C1 and C3 -- the argument is that the floor removes
        *different amounts* from each condition's denominator;
      - mark the floor, and label which side each operator keeps;
      - annotate the count at 50 numerically. This is a figure making a
        quantitative claim, so the quantity belongs on it.

    Consider whether one tier or all three: Tier O carries the strongest version
    (1,054/1,078) and Tier C the weakest (39/56), and the weak one is the tier
    whose claim you are withdrawing. Showing only Tier O is the cleaner figure;
    showing C and O together is the more honest one.
    """
    rows = read_judged("C[13]-medmcqa_180-*")
    raise NotImplementedError("see the TODO above")


def fig_session_displacement() -> None:
    """Figure 5: harm against the number of retrieval slots taken by session turns.

    The dose-response from adversarial_review.md item 3. Two series (C3, C5), x is
    0-3 occupied slots, y is harm rate; annotate n per point, because the cells
    run from 9 probes to 141 and a reader must see that.

    Needs `retrieved_note_ids` and the session-note id set. Left unimplemented
    until sensitivity_analysis.py exposes the per-probe tally rather than
    recomputing it here -- two sources for one number is how they drift apart.
    """
    raise NotImplementedError("blocked on scripts/sensitivity_analysis.py")


FIGURES = {
    "headline": fig_headline,
    "contrasts": fig_contrasts,
    "coherence": fig_coherence_masspoint,
    "session": fig_session_displacement,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fig", choices=sorted(FIGURES), action="append")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    names = sorted(FIGURES) if args.all else (args.fig or ["contrasts"])
    with plt.rc_context(RC):
        for name in names:
            FIGURES[name]()


if __name__ == "__main__":
    main()

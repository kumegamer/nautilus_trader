"""Render saved evidence only; does not execute, select, or rank strategies."""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent


def render():
    selection = json.loads((ROOT / "results/selection.json").read_text())
    final = json.loads((ROOT / "results/final.json").read_text())
    fig = make_subplots(
        rows=2,
        cols=2,
        shared_xaxes="columns",
        subplot_titles=(
            "Sequential validation + walk-forward · 2024–2025",
            "Frozen representatives · January–June 2026",
            "Daily equity drawdown · preholdout OOS",
            "Daily equity drawdown · holdout",
        ),
    )
    colors = ["#1b6ca8", "#b74b31", "#007f65", "#7355a6"]
    for (family, result), color in zip(final.items(), colors, strict=True):
        for column, scenarios in (
            (
                1,
                {
                    "base": selection[family]["oos"],
                    "cost2x": selection[family]["stresses"]["cost2x"],
                },
            ),
            (2, result["scenarios"]),
        ):
            for scenario, m in scenarios.items():
                series = pd.Series({pd.Timestamp(t, tz="UTC"): e for t, e in m["daily_equity"]})
                visibility = True if scenario == "base" else "legendonly"
                label = family.replace("_", " ") + " · " + scenario
                returns = (series / m["initial_capital"] - 1) * 100
                dd = (series / series.cummax() - 1) * 100
                for row, values in ((1, returns), (2, dd)):
                    fig.add_trace(
                        go.Scatter(
                            x=series.index,
                            y=values,
                            name=label,
                            legendgroup=label,
                            showlegend=row == 1 and column == 2,
                            visible=visibility,
                            mode="lines",
                            line={
                                "color": color,
                                "width": 1.6,
                                "dash": "solid" if scenario == "base" else "dot",
                            },
                            hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}%<extra>" + label + "</extra>",
                        ),
                        row=row,
                        col=column,
                    )
    fig.update_layout(
        title="NautilusTrader edge discovery · chronological evidence",
        template="plotly_white",
        height=850,
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.15},
        margin={"b": 200},
    )
    fig.update_yaxes(title_text="Return (%)", row=1)
    fig.update_yaxes(title_text="Drawdown (%)", row=2)
    plot = fig.to_html(full_html=False, include_plotlyjs=True, config={"displaylogo": False})
    labels = "".join(
        f"<li>{family.replace('_', ' ')}: <b>{r['classification']}</b></li>"
        for family, r in final.items()
    )
    html = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>NautilusTrader edge discovery</title><style>"
        "body{max-width:1400px;margin:30px auto;padding:0 24px;color:#172b3a;"
        "font:16px/1.6 system-ui}h1{line-height:1.2}aside{background:#eef3f7;padding:16px}"
        "</style><h1>Historical edge discovery evidence</h1><aside>"
        "The left panels use candidates selected before each OOS period. The right panels use "
        "the four representatives frozen before the holdout opened. Curves do not choose a winner. "
        "Click legend entries to inspect cost stress. Returns use three equal 10,000 USDT sleeves. "
        "Daily drawdown omits intraday extremes. See REPORT.md for all metrics and limitations."
        "</aside><ul>"
        + labels
        + "</ul>"
        + plot
        + "<p>No live trading. Historical results do not establish future profitability.</p></html>"
    )
    (ROOT / "CHARTS.html").write_text(html)


if __name__ == "__main__":
    render()

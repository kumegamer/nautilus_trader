"""Standalone offline charts of native outcomes, with exposure shown alongside returns."""

import json

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .common import ROOT, config
from .metrics import portfolio_daily
from .profiles import BASE, POLICIES
from .report import END, EVALUATION, bundle, period_metrics


def generate():
    selection = json.loads((ROOT / "results/static_selection.json").read_text())[
        "profile"
    ]
    systems = {
        "2024-selected static": selection,
        "Adaptive": "ADAPTIVE",
        "NO_TRADE": "NO_TRADE",
        "Risk-budgeted passive": "PASSIVE",
    }
    colors = ["#ad6419", "#087f8c", "#64748b", "#7653a8"]
    output = ROOT / "results/charts"
    output.mkdir(parents=True, exist_ok=True)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=(
            "Cumulative marked PnL / initial allocated capital",
            "Actual average marked notional / allocated capital",
        ),
    )
    data = []
    for (name, profile), color in zip(systems.items(), colors, strict=True):
        runs = bundle(profile)
        daily = portfolio_daily(runs, EVALUATION, END)
        capital = 3 * config()["capital_per_symbol"]
        fig.add_trace(
            go.Scatter(
                x=[pd.Timestamp(t, unit="ns", tz="UTC") for t, e in daily],
                y=[(e - daily[0][1]) / capital * 100 for t, e in daily],
                name=name,
                legendgroup=name,
                line={"color": color},
            ),
            row=1,
            col=1,
        )
        exposure = (
            pd.concat(
                [pd.Series({o[0]: o[1] for o in r["exposure_daily"]}) for r in runs],
                axis=1,
            ).sum(axis=1)
            / capital
            * 100
        )
        exposure = exposure[(exposure.index > EVALUATION) & (exposure.index <= END)]
        fig.add_trace(
            go.Scatter(
                x=[pd.Timestamp(t, unit="ns", tz="UTC") for t in exposure.index],
                y=exposure.to_numpy(),
                name=name,
                legendgroup=name,
                showlegend=False,
                line={"color": color},
            ),
            row=2,
            col=1,
        )
        data.extend(
            {
                "system": name,
                "timestamp_ns": t,
                "native_portfolio_equity": e,
                "allocated_capital_return": (e - daily[0][1]) / capital,
            }
            for t, e in daily
        )
    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(
        title="Adaptive Trading v2: consumed-history retrospective evaluation",
        template="plotly_white",
        height=800,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.10},
        margin={"l": 80, "r": 35, "t": 120, "b": 90},
    )
    fig.add_annotation(
        text="January 2025–September 2026 UTC. Different exposures remain visible. Flat cash has undefined Sharpe. No prospective edge claim.",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.13,
        showarrow=False,
        align="left",
    )
    fig.write_html(
        output / "equity_and_exposure.html",
        include_plotlyjs=True,
        div_id="v2_equity_exposure",
    )
    pd.DataFrame(data).to_csv(output / "native_daily_equity.csv", index=False)
    z, custom = [], []
    for p in BASE:
        values = [
            period_metrics(bundle(p.id, policy), EVALUATION, END) for policy in POLICIES
        ]
        z.append([m["net_pnl"] for m in values])
        custom.append(
            [
                [m["trades"], m["sharpe"], m["maximum_drawdown"], m["average_exposure"]]
                for m in values
            ]
        )
    heatmap = go.Figure(
        go.Heatmap(
            x=POLICIES,
            y=[p.id for p in BASE],
            z=z,
            customdata=custom,
            colorscale="RdBu",
            zmid=0,
            colorbar={"title": "Net USDT"},
            hovertemplate="%{y} / %{x}<br>Net %{z:.2f} USDT<br>Trades %{customdata[0]}<br>Sharpe %{customdata[1]:.3f}<br>Drawdown %{customdata[2]:.3%}<br>Exposure %{customdata[3]:.3%}<extra></extra>",
        )
    )
    heatmap.update_layout(
        title="Four predeclared exit policies: complete native counterfactuals",
        template="plotly_white",
        height=550,
        margin={"l": 110, "r": 60, "t": 90, "b": 90},
    )
    heatmap.add_annotation(
        text="Base costs; consumed January 2025–September 2026. ENTRY_ONLY remains primary; this chart never selects a replacement.",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.22,
        showarrow=False,
        align="left",
    )
    heatmap.write_html(
        output / "exit_policy_comparison.html",
        include_plotlyjs=True,
        div_id="v2_exit_policies",
    )
    print(
        f"Saved offline native-equity, exposure and exit-policy charts under {output}"
    )


if __name__ == "__main__":
    generate()

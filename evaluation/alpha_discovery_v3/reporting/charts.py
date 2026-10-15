import importlib.metadata
from collections import defaultdict

import pandas as pd
import plotly.graph_objects as go
from alpha.common import ROOT, write_json
from alpha.evaluate import END, START, pick
from alpha.metrics import portfolio_daily
from alpha.profiles import BASE
from alpha.workflow import load_runs
from plotly.subplots import make_subplots

write_json(
    ROOT / "results/reporting_runtime.json",
    {p: importlib.metadata.version(p) for p in ("plotly", "kaleido")},
)
runs = load_runs()
families = defaultdict(list)
for p in BASE:
    families[p.family].append(p.id)
families["Raw breakout controls"] = ["RAW_LONG", "RAW_SHORT"]
families["Logistic controls"] = ["ML_LONG", "ML_SHORT"]
fig = make_subplots(
    rows=4, cols=2, subplot_titles=list(families), vertical_spacing=0.07
)
for i, (family, ids) in enumerate(families.items()):
    for pid in ids:
        d = portfolio_daily(pick(runs, pid), START, END)
        dates = [pd.Timestamp(t, unit="ns", tz="UTC") for t, _ in d]
        pnls = [v - d[0][1] for _, v in d]
        color = "#16856b" if pid.endswith("LONG") else "#bf4f46"
        fig.add_trace(
            go.Scatter(x=dates, y=pnls, name=pid, line={"color": color, "width": 1.8}),
            row=i // 2 + 1,
            col=i % 2 + 1,
        )
fig.update_layout(
    template="plotly_white",
    height=1400,
    width=1250,
    title="Alpha Discovery v3 — consumed-history OOS marked PnL (base costs)",
    margin={"t": 100},
    legend={"orientation": "h", "y": -0.07},
)
fig.update_yaxes(title_text="PnL (USDT)")
fig.add_annotation(
    xref="paper",
    yref="paper",
    x=0,
    y=1.055,
    showarrow=False,
    text="Fixed 30,000 USDT per path · independent research paths · not a combined portfolio · no prospective claim",
    font={"size": 12},
)
fig.write_html(ROOT / "results/equity_diagnostics.html", include_plotlyjs=True)

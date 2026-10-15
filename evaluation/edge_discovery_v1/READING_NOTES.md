# Reading the evidence

These clarifications describe the implementation used in every saved run; they do not
change signals, parameters, costs, ranking, or promotion rules.

- Research is one continuous 2022–2023 run. Capital resets only at declared period boundaries.
- Multi-period return statistics chain-link normalized native period equity. Native USDT PnL
  is summed nominally across independent period runs, so compounded return and nominal PnL
  divided by initial capital differ. All single-period statistics reconcile directly.
- `expectancy_r` in JSON means expectancy divided by the 25 USDT initial risk **budget**.
  Lot, notional and participation caps can make actual initial stop risk smaller. It is
  not expectancy divided by each trade's actual stop risk. The requested headline metric
  is `expectancy_per_trade` in USDT.
- Maximum drawdown is measured on daily close-marked equity; intraday extremes can be
  worse. Monthly concentration groups round trips by realized exit month.
- `render_charts.py` only renders saved summaries. It does not participate in signals,
  execution, ranking, candidate selection, or holdout admission.

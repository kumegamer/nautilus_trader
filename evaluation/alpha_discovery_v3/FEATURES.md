# Causal feature dictionary

Bars are UTC-aligned, complete groups of public Binance USD-M 5m klines. A bar
starting t is available at t+duration-1ms; features join backward on that timestamp.
No partial higher-timeframe candles. Quantiles/ranks use trailing windows including
the completed observation. No whole-history normalization. Warmup is not scored.
Prices are quote USDT; volume/taker_buy are base units; quote_volume is USDT.
Returns are natural-log fractions, volatility per bar unless annualized explicitly.
Every row below is known at the latest included completed close unless stated.

| Features | Definition and lookback | Economic rationale / availability |
|---|---|---|
| ret_5, ret_15, ret_1h | log close ratio over 1x5m, 1x15m, 4x15m | Short entry direction; latest closed 5m/15m only |
| mom_60, mom_240 | log return over 12 completed 1h / 6 completed 4h bars | Slow information diffusion; backward as-of join |
| slope_60, slope_240 | price change / (12 or 6 x mean14 high-low) | Trend scale; diagnostic only |
| mom_24h | log return over 96x15m | Common-factor and relative momentum |
| atr | mean14 true range, including previous close gaps | Risk/stop distance; not a target predictor |
| rv, annual_vol | std96 log returns; rv x sqrt(96x365) | Risk reduction in volatile markets |
| vol_ratio | rv / trailing1920 rv median | Volatility clustering; 20 days, current completed rv included |
| vol_percentile | trailing2880 rank of rv / 2880 | Avoid unusually quiet/extreme breakouts; 30 days |
| vol_of_vol | std96 rv / mean96 rv | Instability diagnostic, no tuned gate |
| efficiency | absolute 96-bar change / sum96 absolute changes | Directional persistence versus two-sided movement |
| persistence | mean96 signs of 15m returns | Diagnostic directional consistency |
| choppiness | log10(sum96 TR / range96) / log10(96) | Diagnostic range intensity |
| pullback | prior close minus mean8 prior closes, divided by prior ATR | Retracement before current resumption; no current entry bar in pullback |
| volume_ratio | current volume / median96 previous volumes | Participation in completed candle |
| volume_percentile | trailing1920 volume rank | Diagnostic participation distribution |
| taker_ratio | sum taker-buy base volume / sum base volume within 15m | Aggressor imbalance, public kline field, close-time availability |
| range_ratio | high-low / median96 previous high-low | Range expansion, not future volatility |
| high_prev, low_prev | max/min96 prior highs/lows | Prior 24h structure; excludes signal bar |
| high_12h, low_12h | max/min48 prior highs/lows | Shorter expansion structure |
| exit_high, exit_low | max/min16 prior highs/lows | Four-hour structural invalidation |
| distance_high, distance_low | close minus prior24h extreme / ATR | Diagnostic structure distance |
| false_frequency | mean48 confirmed one-bar failures: previous close outside its prior channel, current close back inside that same channel | Uses failure only after confirming bar closes; no future false-breakout label |
| compression_recent | minimum16 prior vol_ratio | Compression precedes current expansion |
| shock_prev | previous return / std96 returns strictly before that return | Temporary liquidity shock, normalized without its own impact |
| equilibrium, deviation | volume-weighted mean96 closes; (close-equilibrium)/ATR | Range recovery target and distance |
| funding, funding_change | last settled published rate and difference from preceding rate | Crowding/carry persistence; original publication timestamp +1 second, backward join |
| funding_age_hours | elapsed hours since funding availability | Reject stale funding observations |
| btc_mom, relative_strength | synchronized BTC24h momentum; own24h minus BTC24h | Common factor and leader/laggard hypotheses; exact availability match |
| btc_correlation | rolling672 (7-day) own/BTC15m return correlation | Require meaningful shared factor; contemporaneous completed closes only |
| cross_rank | three-symbol rank of completed24h momentum | Diagnostic cross-sectional leadership |
| regime | STRESS if ratio>2.5, COMPRESSION if <.7, TREND if efficiency>.3, else RANGE; append HIGH_VOL if ratio>1.3 | Causal descriptive entry attribution; not hindsight labels or mandatory exit |
| ml_1, ml_-1 | separate quarterly expanding logistic probabilities | Past-only scaler/labels, 24h embargo, deterministic fits; uncalibrated scores |

No time-of-day/day-of-week hypothesis was tested: there was no prior economic
justification sufficient to spend the finite budget. No spread, depth, liquidation,
future funding forecast or unavailable microstructure field is imputed.

# Research interpretation

All observations below are retrospective on consumed history. No next-version proposal
is executed, and no additional strategy is admitted by this diagnostic script.

## MHT_LONG: WEAK_SIGNAL

OOS marked PnL 42.49 USDT; 2x-cost PnL -223.80; 138 purged trades; 6/7 positive quarters.
Purged reference-price gross 322.30, fees plus slippage 266.92, signed funding -12.89 USDT. Positive aggregate economics still need the failed gates listed below.
Unpassed gates: economics, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## MHT_SHORT: REJECTED

OOS marked PnL -299.30 USDT; 2x-cost PnL -449.36; 88 purged trades; 1/7 positive quarters.
Purged reference-price gross -147.78, fees plus slippage 150.40, signed funding -1.12 USDT. The price mechanism itself lost before execution friction.
Unpassed gates: economics, sample, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## BQ_LONG: WEAK_SIGNAL

OOS marked PnL 954.68 USDT; 2x-cost PnL 153.69; 464 purged trades; 2/7 positive quarters.
Purged reference-price gross 1828.24, fees plus slippage 831.48, signed funding -42.09 USDT. Positive aggregate economics still need the failed gates listed below.
Unpassed gates: chronology, resampling, multiple_testing.

## BQ_SHORT: REJECTED

OOS marked PnL -262.25 USDT; 2x-cost PnL -947.15; 438 purged trades; 3/7 positive quarters.
Purged reference-price gross 422.67, fees plus slippage 693.77, signed funding 8.86 USDT. Execution friction exceeded the positive price mechanism.
Unpassed gates: economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## CROSS_LONG: WEAK_SIGNAL

OOS marked PnL 265.19 USDT; 2x-cost PnL -163.94; 328 purged trades; 2/7 positive quarters.
Purged reference-price gross 724.66, fees plus slippage 433.16, signed funding -26.32 USDT. Positive aggregate economics still need the failed gates listed below.
Unpassed gates: economics, chronology, cost, resampling, multiple_testing, symbol_transfer.

## CROSS_SHORT: REJECTED

OOS marked PnL -32.45 USDT; 2x-cost PnL -414.06; 314 purged trades; 3/7 positive quarters.
Purged reference-price gross 360.66, fees plus slippage 384.08, signed funding -9.04 USDT. Execution friction exceeded the positive price mechanism.
Unpassed gates: economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## FUND_LONG: REJECTED

OOS marked PnL -977.88 USDT; 2x-cost PnL -1329.26; 244 purged trades; 0/7 positive quarters.
Purged reference-price gross -678.17, fees plus slippage 314.42, signed funding 14.71 USDT. The price mechanism itself lost before execution friction.
Unpassed gates: economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## FUND_SHORT: REJECTED

OOS marked PnL 0.00 USDT; 2x-cost PnL 0.00; 0 purged trades; 0/7 positive quarters.
Purged reference-price gross 0.00, fees plus slippage 0.00, signed funding 0.00 USDT. Insufficient activity to assess a repeatable edge; zero exposure is not a loss estimate.
Unpassed gates: economics, sample, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## VOL_LONG: REJECTED

OOS marked PnL -514.48 USDT; 2x-cost PnL -1483.80; 262 purged trades; 3/7 positive quarters.
Purged reference-price gross 561.41, fees plus slippage 1032.45, signed funding -43.44 USDT. Execution friction exceeded the positive price mechanism.
Unpassed gates: economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## VOL_SHORT: REJECTED

OOS marked PnL -27.68 USDT; 2x-cost PnL -33.65; 13 purged trades; 1/7 positive quarters.
Purged reference-price gross -21.86, fees plus slippage 5.99, signed funding 0.17 USDT. Insufficient activity to assess a repeatable edge; zero exposure is not a loss estimate.
Unpassed gates: economics, sample, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## RANGE_LONG: REJECTED

OOS marked PnL -1268.09 USDT; 2x-cost PnL -2711.57; 642 purged trades; 0/7 positive quarters.
Purged reference-price gross 194.64, fees plus slippage 1451.92, signed funding -10.81 USDT. Execution friction exceeded the positive price mechanism.
Unpassed gates: economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## RANGE_SHORT: REJECTED

OOS marked PnL -1150.75 USDT; 2x-cost PnL -2112.37; 397 purged trades; 0/7 positive quarters.
Purged reference-price gross -181.17, fees plus slippage 981.45, signed funding 11.87 USDT. The price mechanism itself lost before execution friction.
Unpassed gates: economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer.

## Stability and diversity

primary_daily_correlations.csv compares every central economic profile on synchronized
daily marked PnL. Different family names alone do not establish different payoff sources.
neighbor_path_changes.csv reports when a changed threshold leaves the entire eligible
symbol fill path unchanged. Such a plateau is not independent confirmation. No neighbor
is substituted for a central hypothesis. Repeated cost runs are the same market sample.

## Next experiment proposals, currently inert

For sparse funding and high-volatility hypotheses, collect unchanged forward observations
rather than relax sample gates. For negative gross mechanisms, reconsider the economic
entry hypothesis in a new version; exit optimization cannot establish missing entry alpha.
For positive gross but negative net outcomes, a new version should test an economically
justified lower-turnover mechanism or actual executable spread/depth evidence, without
assuming maker fills. For unstable temporal or symbol transfer, request a new independent
period before choosing a specialized cell. Every such change needs a new finite protocol.

Only the frozen validated library may be handed to future adaptive research. Neither these
proposals nor attractive hindsight slices activate trading or modify frozen rules.

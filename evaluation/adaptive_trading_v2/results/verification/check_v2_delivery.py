import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from ats.common import ROOT, config, write_json
from ats.workflow import jobs_static, run_path

required = ['ARCHITECTURE.md','DELIVERABLES.md','PROTOCOL.md','GATES.md','REPORT.md','SHADOW.md','README.md','config.json','results/eligibility.json','results/profile_results.csv','results/exit_policy_results.csv','results/per_symbol_results.csv','results/long_short_regime_decomposition.csv','results/profile_switches.jsonl','results/profile_decisions.jsonl','results/regime_switches.csv','results/regime_statistics.json','results/research_proposals.json','results/edge_decay.jsonl','results/research_triggers.jsonl','results/system_comparisons.csv','results/walk_forward_monthly.csv','results/post_exit_excursions.csv','results/native_integrity.json','results/reference_audit.json','results/shadow_validation_prefix_audit.json','results/public_market_smoke.json','results/charts/equity_and_exposure.html','results/charts/exit_policy_comparison.html','ats/shadow.py','ats/shadow_validation.py','ats/research.py','deployment/shadow.service','deployment/shadow.timer','deployment/validation.service','deployment/validation.timer','data/historical_manifest.json','data/feature_cache_manifest.json']
assert all((ROOT/p).is_file() for p in required)
expected = {run_path(*job).name for job in jobs_static()}
expected |= {run_path(p,'ENTRY_ONLY',scenario,s).name for p in ('ADAPTIVE','PASSIVE','NO_TRADE') for scenario in config()['scenarios'] for s in config()['symbols']}
assert len(expected) == 351
assert {p.name for p in (ROOT/'results/runs').glob('*.json.gz')} == expected
with (ROOT/'results/walk_forward_monthly.csv').open() as f:
    monthly = list(csv.DictReader(f))
sums = defaultdict(float)
counts = defaultdict(int)
for row in monthly:
    k = (row['system'], row['scenario'])
    sums[k] += float(row['net_pnl'])
    counts[k] += 1
assert all(n == 21 for n in counts.values())
comparisons = json.loads((ROOT/'results/system_comparisons.json').read_text())
worst = 0
for row in comparisons:
    if row['period'] == 'evaluation_2025_to_2026_09':
        difference = abs(sums[(row['system'],row['scenario'])] - row['net_pnl'])
        worst = max(worst, difference)
        assert difference < 1e-7
        assert row['regime_switches'] > 0
conclusions = json.loads((ROOT/'results/conclusions.json').read_text())
eligibility = json.loads((ROOT/'results/eligibility.json').read_text())
assert not any(e['eligible'] for e in eligibility)
assert not conclusions['adaptive_exercised']
assert conclusions['classification'] == 'V2_RETROSPECTIVE_NO_EDGE'
assert not conclusions['prospective_shadow_eligible_profiles']
assert not (ROOT/'results/profile_switches.jsonl').read_text()
assert subprocess.check_output(['git','branch','--show-current'], text=True).strip() == 'evaluation/adaptive-trading-v2'
assert not subprocess.check_output(['git','diff','HEAD','--name-only'], text=True).strip()
write_json(ROOT/'results/delivery_audit.json', {
    'status':'PASS', 'required_existing_artifacts_checked':len(required),
    'matrix_paths':len(expected), 'monthly_system_scenario_series':len(sums),
    'monthly_folds_per_series':21, 'maximum_monthly_pnl_sum_error':worst,
    'eligibility_records':len(eligibility), 'eligible_records':0,
    'source_branch':'evaluation/adaptive-trading-v2',
    'tracked_core_edits':0, 'commit_or_push_performed':False,
    'freeze_verification':'Separate ats.freeze verify required after one-time freeze',
    'unresolved':['No eligible trading profile; adaptive economic benefit untested','Public Binance forward smoke blocked HTTP451','No independent prospective economic evidence','Alternative exit treatments have no policy-specific promotion pipeline'],
})
print('PASS delivery coverage, complete matrix, monthly PnL attribution and conservative conclusions')

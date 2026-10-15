import json
from unittest.mock import patch
from ats import shadow_validation as sv
from ats.common import ROOT, config, ns, write_json
from ats.profiles import BASE, library
from ats.shadow import Journal
from ats.workflow import read_run

observed = {}
original_run = sv.run
cutoff = ns('2026-09-24')
expected = read_run('TB_SHORT', 'ENTRY_ONLY', 'base', 'BTCUSDT')
def capture(*args, **kwargs):
    assert kwargs['start_ns'] == ns('2024-01-01')
    assert kwargs['end_ns'] == cutoff
    assert args[0]['liquidate'] is False
    result = original_run(*args, **kwargs)
    for key, timestamp in [('trades', 'exit_ns'), ('fills', 'ts_ns'), ('funding_events', 'timestamp')]:
        prior = [e for e in expected[key] if e[timestamp] < cutoff]
        assert result[key] == prior, (key, len(result[key]), len(prior))
        observed[key] = len(prior)
    return result

cfg = dict(config(), symbols=['BTCUSDT'], scenarios={'base':config()['scenarios']['base']})
real_digest = sv.digest
def digest(path):
    return 'engineering-fixture' if path.name == 'prospective_freeze.json' else real_digest(path)
def evaluate(profile, timestamp, store):
    return {'profile':profile, 'timestamp':timestamp, 'end_ns':cutoff, 'eligible':False}

journal = Journal('work/shadow_validation_prefix_state')
journal.set_once('prospective_start_ns', ns('2026-10-15'))
with patch.object(sv, 'assert_freeze', dict), patch.object(sv, 'config', lambda: cfg), patch.object(sv, 'library', lambda: {'TB_SHORT':library()['TB_SHORT']}), patch.object(sv, 'BASE', [BASE[0]]), patch.object(sv, 'run', capture), patch.object(sv, 'evaluate', evaluate), patch.object(sv, 'digest', digest):
    records = sv.validate_month(journal, '2026-10-01')
assert records[0]['timestamp'] >= ns('2026-10-15')
journal.close()
write_json(ROOT / 'results/shadow_validation_prefix_audit.json', {
    'status':'PASS', 'classification':'ENGINEERING_EVIDENCE_ONLY',
    'actual_month_boundary':'2026-10-01', 'matured_cutoff':'2026-09-24',
    'midmonth_initialization':True, 'continuous_path_from':'2024-01-01',
    'terminal_liquidation':False, 'exact_historical_prefix_matches':observed,
    'live_public_market_access':False, 'future_profitability_claim':False,
})
print('PASS exact full-history prefix and mid-month initialization', observed)

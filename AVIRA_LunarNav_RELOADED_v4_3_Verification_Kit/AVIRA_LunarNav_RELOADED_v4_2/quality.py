"""Fail-closed evidence quality gate for science demonstrations."""

def evidence_status(mode, a_horizon, b_horizon, a_citation='', b_citation='', live_verified=False):
    if mode.startswith('SYNTHETIC'):
        return {'label':'DEMO ONLY','reasons':['Synthetic angles are not NASA measurements'], 'eligible_for_scientific_claim':False}
    reasons=[]
    if not live_verified:
        reasons.append('Live Horizons result not independently cross-checked against reference output')
    if (a_horizon and not a_citation.strip()) or (b_horizon and not b_citation.strip()):
        reasons.append('Uploaded terrain mask missing source attribution')
    if not a_horizon or not b_horizon:
        reasons.append('At least one site uses a geometric rather than measured terrain horizon')
    return {'label':'SCREENING WITH LIMITATIONS' if reasons else 'SCREENING / DATA ATTRIBUTED',
        'reasons':reasons or ['Input origins stated; not flight qualified'],
        'eligible_for_scientific_claim':not any('Live Horizons result' in r for r in reasons)}


def verdict(base, quality, power=None):
    if quality['label']=='DEMO ONLY':
        return 'DEMO — NOT A SCIENTIFIC PASS', ['Synthetic samples cannot qualify a mission']
    errors=list(base['failed'])
    if power is not None and power['reserve_breached']:
        errors.append('Battery reserve breached (assumed power model)')
    if errors:
        return 'CONSTRAINTS NOT MET',errors
    return 'SCREENING CONSTRAINTS MET — NOT LANDING APPROVAL', []

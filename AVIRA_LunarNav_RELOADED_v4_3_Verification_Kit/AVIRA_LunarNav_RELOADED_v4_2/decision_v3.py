"""Decision support for a non-flight-qualified NASA Space Apps demonstrator.
No trained mission-success classifier: decisions are constraint first and auditable.
"""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd


def event_forecast(df, column):
    """Sample-bounded next transition and run lengths.
    This is a discrete event estimate, not a guarantee of true rise/set time.
    """
    if column not in ('sun_visible','earth_visible','joint'):
        raise ValueError('Unknown visibility channel')
    if len(df) < 2:
        raise ValueError('Two or more time samples required')
    times=pd.to_datetime(df.time,utc=True)
    if any(times[i] >= times[i+1] for i in range(len(times)-1)):
        raise ValueError('Timestamps must increase')
    values=df[column].to_numpy(dtype=bool)
    dur=np.diff(times.astype('int64').to_numpy())/3.6e12
    max_on=max_off=cur_on=cur_off=0.
    for val,h in zip(values[:-1],dur):
        if val:
            cur_on+=float(h);cur_off=0.;max_on=max(max_on,cur_on)
        else:
            cur_off+=float(h);cur_on=0.;max_off=max(max_off,cur_off)
    events=[]
    for i in range(1,len(values)):
        if values[i]!=values[i-1]:
            events.append((times[i], 'rises above threshold' if values[i] else 'sets below threshold'))
    if events:
        at,kind=events[0]
        msg=f'{kind} by sample {at.strftime("%Y-%m-%d %H:%M UTC")} (actual crossing bracketed by prior sample)'
    else:
        msg='no threshold crossing within sampled period'
    return {'next_event':msg,'longest_visible_h':max_on,'longest_blackout_h':max_off,
            'event_count':len(events)}


def rank_scenarios(candidates):
    """Only rank candidates that pass every configured constraint."""
    passed=[(name,metric,evaluation) for name,metric,evaluation in candidates if not evaluation['failed']]
    if not passed:
        failed='; '.join(f'{name}: {", ".join(evaluation["failed"])}' for name,_,evaluation in candidates)
        return {'winner':None,'reason':'Neither candidate passes all configured screening constraints. '+failed}
    # lexicographic ranking; robust zero-throughput handled without arbitrary weighting
    winning=max(passed,key=lambda x:(x[1]['joint_hours'],-x[2]['max_earth_blackout_h'],x[1]['earth_hours']))
    return {'winner':winning[0], 'reason':f'Scenario {winning[0]} is preferred among {len(passed)} feasible candidate(s), based on sampled joint hours, then shorter communication blackout. Screening result only.'}


def recommend_schedule(schedule):
    """Return an explainable preferred delay only when constraints are met."""
    if schedule.empty or not {'Screening','Joint visibility %','Longest Earth blackout h','Shift days'}.issubset(schedule.columns):
        raise ValueError('Incomplete schedule comparison')
    ok=schedule[schedule['Screening']=='CONSTRAINTS MET']
    if ok.empty:
        return 'No evaluated date shift meets all constraints; do not claim a viable alternative.'
    best=ok.sort_values(['Joint visibility %','Longest Earth blackout h','Shift days'],ascending=[False,True,True]).iloc[0]
    return f'Best among tested feasible offsets: {int(best["Shift days"]):+d} days, joint visibility {best["Joint visibility %"]:.1f}%; this is a sampled, constraint-based recommendation, not a prediction of landing safety.'


def solar_incidence_proxy(df, panel_tilt_deg=0.):
    """Idealized horizontal-panel cos(zenith) proxy (tilt=0).
    Nonzero tilt has no azimuth orientation, so intentionally fail closed.
    """
    if not (0 <= panel_tilt_deg <= 90):
        raise ValueError('Tilt outside range')
    if panel_tilt_deg != 0:
        # Tilt without azimuth orientation is scientifically ambiguous. Do not fabricate a power model.
        return float('nan')
    angles=np.asarray(df.sun_el,dtype=float)[:-1]
    if not np.isfinite(angles).all():
        raise ValueError('Invalid solar elevation')
    times=pd.to_datetime(df.time,utc=True)
    durations=np.diff(times.astype('int64').to_numpy())/3.6e12
    if len(durations)==0 or (durations<=0).any():
        raise ValueError('Invalid intervals')
    incidence=np.maximum(0.,np.sin(np.radians(angles)))
    incidence=np.where(df.sun_visible.to_numpy(dtype=bool)[:-1],incidence,0.)
    return float(np.average(incidence,weights=durations))


def build_evidence(data_mode, scenarios, step_h, threshold_deg, terrains):
    """Machine-readable provenance, reproducibility and limitations. Never fake successful NASA acquisition."""
    source='NASA JPL Horizons API' if data_mode.startswith('NASA') else 'SYNTHETIC DEMO (NOT NASA DATA)'
    data=[]
    for i, ((lat,lon,start,df,metrics),(mask,sourcelink)) in enumerate(zip(scenarios,terrains)):
        data.append({'candidate':'AB'[i],'lat_deg':lat,'lon_east_deg':lon,'start_date_utc':start.isoformat(),
            'sample_count':int(len(df)),'first_sample_utc':pd.Timestamp(df.time.iloc[0]).isoformat(),
            'last_sample_utc':pd.Timestamp(df.time.iloc[-1]).isoformat(),
            'horizon_mask_uploaded':mask,'horizon_mask_source':sourcelink or 'not provided',
            'joint_hours_left_edge_estimate':metrics['joint_hours']})
    manifest={'project':'AVIRA LunarNav RELOADED v4','data_mode':source,'source_url':'https://ssd.jpl.nasa.gov/api/horizons.api',
        'ephemeris_targets':{'Sun':'10','Earth':'399'},'observer_center':'coord@301','quantities':'4',
        'time_system':'UTC','sample_step_hours':step_h,'extra_clearance_deg':threshold_deg,
        'scenarios':data,'scientific_limitations':['Discrete sampling and event brackets; no flight certification',
         'Topographic horizon requires verified independent mask per landing site',
         'No RF link budget, solar electrical output, hazard map or thermal analysis',
         'Procedural 3D surface is artistic, NOT a NASA terrain elevation model'],
        'ai_disclosure':'AI-assisted programming and documentation; optional IsolationForest numerical outlier detection. Physics and decisions are deterministic.'}
    return json.dumps(manifest,indent=2,ensure_ascii=False)

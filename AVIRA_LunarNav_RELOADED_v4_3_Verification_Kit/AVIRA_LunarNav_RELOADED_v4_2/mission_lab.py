"""Deterministic mission decision support, not autonomous mission certification."""
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class MissionConstraints:
    min_joint_pct: float = 30.0
    max_blackout_hours: float = 12.0
    min_sun_hours: float = 24.0
    min_earth_hours: float = 24.0

def longest_run(df: pd.DataFrame, column: str, is_true: bool = True) -> float:
    """Duration of longest sampled left-edge run. Last row has no duration."""
    if len(df) < 2:
        raise ValueError('At least two observations required')
    vals = df[column].to_numpy(dtype=bool)[:-1]
    times = pd.to_datetime(df.time, utc=True)
    durations = np.diff(times.astype('int64').to_numpy()) / 3.6e12
    if (durations <= 0).any():
        raise ValueError('Time samples must increase strictly')
    longest = current = 0.0
    for value, duration in zip(vals, durations):
        if bool(value) == is_true:
            current += float(duration)
            longest = max(longest, current)
        else:
            current = 0.0
    return longest

def assess(df: pd.DataFrame, metrics: dict, limits: MissionConstraints):
    checks = {
        'Joint visibility %': (metrics['joint_pct'] >= limits.min_joint_pct, metrics['joint_pct'], limits.min_joint_pct, '% minimum'),
        'Sunlight hours': (metrics['sun_hours'] >= limits.min_sun_hours, metrics['sun_hours'], limits.min_sun_hours, 'h minimum'),
        'Earth-link hours': (metrics['earth_hours'] >= limits.min_earth_hours, metrics['earth_hours'], limits.min_earth_hours, 'h minimum'),
        'Maximum Earth blackout': (longest_run(df,'earth_visible',False) <= limits.max_blackout_hours, longest_run(df,'earth_visible',False), limits.max_blackout_hours, 'h maximum'),
    }
    failed=[name for name,(ok,*_) in checks.items() if not ok]
    status='CONSTRAINTS MET' if not failed else 'CONSTRAINTS NOT MET'
    reasons=([f'{k}: {x:.2f} vs {y:g} {unit}' for k,(ok,x,y,unit) in checks.items() if not ok]
             if failed else ['All configured geometry-screening constraints met'])
    return {'status':status,'failed':failed,'reasons':reasons,'checks':checks,
            'max_earth_blackout_h':longest_run(df,'earth_visible',False),
            'max_sun_gap_h':longest_run(df,'sun_visible',False),
            'max_joint_window_h':longest_run(df,'joint',True)}

def scenario_stress(sun, earth, analyze_fn, base_clearance: float, limits: MissionConstraints,
                    uncertainty_deg: float=2.0):
    """Sensitivity analysis; margin is an assumption, not a measured uncertainty."""
    if not 0 <= uncertainty_deg <= 20 or base_clearance < 0:
        raise ValueError('Invalid clearance or sensitivity margin')
    results=[]
    for label,clearance in [('Optimistic (lower clearance)',max(0.,base_clearance-uncertainty_deg)),
                            ('Nominal',base_clearance),
                            ('Conservative (+margin)',base_clearance+uncertainty_deg)]:
        df,metrics=analyze_fn(sun,earth,threshold=clearance)
        evaluation=assess(df,metrics,limits)
        results.append({'Case':label,'Clearance deg':clearance,'Sun h':metrics['sun_hours'],
                        'Earth h':metrics['earth_hours'],'Joint %':metrics['joint_pct'],
                        'Max Earth blackout h':evaluation['max_earth_blackout_h'],
                        'Screening':evaluation['status']})
    return pd.DataFrame(results)

def fault_injection(sun, earth, analyze_fn, limits, outage_start_h=12, outage_duration_h=8):
    """Simulate an antenna/ground-segment outage independent of celestial geometry.
    Demonstration only; uses input time samples and assumes no real communication link budget.
    """
    df,metrics=analyze_fn(sun,earth)
    if not 0 <= outage_start_h or outage_duration_h <= 0:
        raise ValueError('Invalid fault injection window')
    t0=pd.Timestamp(df.time.iloc[0])
    block=(pd.to_datetime(df.time,utc=True)>=t0+pd.Timedelta(hours=outage_start_h)) & (pd.to_datetime(df.time,utc=True)<t0+pd.Timedelta(hours=outage_start_h+outage_duration_h))
    damaged=df.copy()
    damaged['earth_visible']=damaged['earth_visible'] & ~block
    damaged['joint']=damaged['sun_visible'] & damaged['earth_visible']
    dt=np.diff(pd.to_datetime(damaged.time,utc=True).astype('int64').to_numpy())/3.6e12
    total=float(dt.sum())
    bad_m={**metrics, 'earth_hours':float(np.dot(damaged.earth_visible.iloc[:-1].astype(float),dt)),
           'joint_hours':float(np.dot(damaged.joint.iloc[:-1].astype(float),dt))}
    bad_m['earth_pct']=100*bad_m['earth_hours']/total
    bad_m['joint_pct']=100*bad_m['joint_hours']/total
    return damaged,bad_m,assess(damaged,bad_m,limits)

def explain(metrics_a,metrics_b,assessment_a,assessment_b):
    """Auditable rules-based AI-assistive explanation; no LLM or training claims."""
    lines=[]
    for tag,metrics,assessment in [('A',metrics_a,assessment_a),('B',metrics_b,assessment_b)]:
        lines.append(f'Scenario {tag}: {assessment["status"]}; Sun {metrics["sun_hours"]:.1f} h, '
                     f'Earth {metrics["earth_hours"]:.1f} h, joint {metrics["joint_pct"]:.1f}%, '
                     f'longest Earth blackout {assessment["max_earth_blackout_h"]:.1f} h.')
        lines += [f'  Constraint alert: {reason}' for reason in assessment['reasons'] if 'vs' in reason]
    qualified=[(t,m) for t,m,a in [('A',metrics_a,assessment_a),('B',metrics_b,assessment_b)] if not a['failed']]
    if qualified:
        best=max(qualified,key=lambda item:(item[1]['joint_hours'],item[1]['earth_hours']))
        lines.append(f'Among candidates meeting all CONFIGURED screening constraints, scenario {best[0]} has the largest sampled joint window.')
    else:
        lines.append('Neither scenario meets all configured constraints; relax constraints only with an engineering justification or inspect other sites/dates.')
    lines.append('Not a safety certification: landing hazards, thermal limits, terrain unless supplied, and true RF link margin require further analysis.')
    return lines

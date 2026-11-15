"""Uncertainty-aware but non-flight-qualified mission window analysis."""
from datetime import datetime, timedelta, timezone
import math
import numpy as np
import pandas as pd

SITES = {
    'South Pole (90°S, 0°E)': (-90.0, 0.0),
    'South-pole Candidate A (89.5°S, 0°E)': (-89.5, 0.0),
    'South-pole Candidate B (89.5°S, 90°E)': (-89.5, 90.0),
    'South-pole Candidate C (88.5°S, 180°E)': (-88.5, 180.0),
}

def demo_data(lat, lon, start, days=5, step_hours=2):
    """Synthetic geometry, for interface demonstration ONLY; NEVER NASA data."""
    base = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    n = days*24//step_hours + 1
    t = np.arange(n) * step_hours
    sun_az = (t * 360/(29.53*24) + lon + 90) % 360
    sun_el = 1.8 + 6*np.sin(2*np.pi*t/(29.53*24) + np.radians(lon)) + (lat+90)*0.4
    earth_az = (25 + lon + 30*np.sin(2*np.pi*t/(27.32*24))) % 360
    earth_el = 2.0 + 6*np.sin(2*np.pi*t/(27.32*24) + .3 + np.radians(lon))
    times = [base + timedelta(hours=int(i)*step_hours) for i in range(n)]
    return ([{'time':x,'az':float(a),'el':float(e)} for x,a,e in zip(times,sun_az,sun_el)],
            [{'time':x,'az':float(a),'el':float(e)} for x,a,e in zip(times,earth_az,earth_el)])

def analyze(sun, earth, threshold=0, min_sun=0, min_earth=0, horizon=None):
    """Interpolate only on matching sample timestamps; positive-angle horizon test.
    Returns sampled fractions, NOT guaranteed continuous visibility windows.
    """
    sunmap = {p['time']:p for p in sun}
    earthmap = {p['time']:p for p in earth}
    if len(sunmap) != len(sun) or len(earthmap) != len(earth):
        raise ValueError('Duplicate timestamps detected in ephemeris')
    if any(getattr(t, "tzinfo", None) is None for t in sunmap):
        raise ValueError("Ephemeris timestamps must be timezone-aware UTC instants")
    if set(sunmap) != set(earthmap):
        raise ValueError('Sun/Earth ephemeris timestamps must match; no silent sample loss')
    times = sorted(sunmap)
    if len(times) < 2:
        raise ValueError('At least two matching Sun/Earth time samples required')
    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError('Clearance must be finite and nonnegative')
    rows=[]
    for t in times:
        s,e=sunmap[t],earthmap[t]
        if not all(np.isfinite(float(p[v])) for p in (s,e) for v in ('az','el')):
            raise ValueError('NaN or infinite ephemeris angle detected')
        if any(not (0 <= float(p['az']) <= 360 and -90 <= float(p['el']) <= 90) for p in (s,e)):
            raise ValueError('Ephemeris angle outside physical range')
        h_s = float(horizon(s['az'])) if horizon else 0.
        h_e = float(horizon(e['az'])) if horizon else 0.
        if not np.isfinite(h_s) or not np.isfinite(h_e):
            raise ValueError('Invalid terrain horizon value')
        s_visible = s['el'] > max(h_s, threshold)
        e_visible = e['el'] > max(h_e, threshold)
        rows.append({'time':t,'sun_az':s['az'],'sun_el':s['el'],'earth_az':e['az'],
                     'earth_el':e['el'],'horizon_s':h_s,'horizon_e':h_e,
                     'sun_visible':s_visible,'earth_visible':e_visible,
                     'joint':s_visible and e_visible})
    df=pd.DataFrame(rows)
    # Hour-level weighting over sample intervals; exclude last point from duration.
    dth=(df.time.iloc[-1]-df.time.iloc[0]).total_seconds()/3600
    durations=np.diff(df.time.astype('int64').to_numpy())/3.6e12
    if (durations <= 0).any():
        raise ValueError('Ephemeris sample intervals must be positive')
    sun_hours=float(np.dot(df.sun_visible.to_numpy()[:-1],durations))
    earth_hours=float(np.dot(df.earth_visible.to_numpy()[:-1],durations))
    joint_hours=float(np.dot(df.joint.to_numpy()[:-1],durations))
    return df, {'duration_hours':dth,'sun_hours':sun_hours,'earth_hours':earth_hours,
                'joint_hours':joint_hours,'sun_pct':100*sun_hours/dth,
                'earth_pct':100*earth_hours/dth,'joint_pct':100*joint_hours/dth}

def window_intervals(df, column):
    """Sampled left-edge intervals only, not interpolated rise/set times."""
    records=[]; onset=None
    for i in range(len(df)-1):
        yes=bool(df.iloc[i][column])
        if yes and onset is None: onset=df.time.iloc[i]
        if not yes and onset is not None:
            records.append((onset,df.time.iloc[i]));onset=None
    if onset is not None: records.append((onset,df.time.iloc[-1]))
    return records

def advisory(metrics, minimum_joint_pct=30):
    if metrics['joint_pct'] >= minimum_joint_pct:
        return 'Meets configured joint-visibility threshold (geometric screening only).'
    return 'Below configured joint-visibility threshold; inspect outage windows or another site/date.'

def anomaly_flags(df):
    """Exploratory AI/ML outlier detection: NOT a physical anomaly or safety verdict."""
    try:
        from sklearn.ensemble import IsolationForest
        if len(df) < 12: return None
        x=df[['sun_el','earth_el']].to_numpy()
        labels=IsolationForest(n_estimators=75,contamination=.10,random_state=42).fit_predict(x)
        return labels == -1
    except ImportError:
        return None

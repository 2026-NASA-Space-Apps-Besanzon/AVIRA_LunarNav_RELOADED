from datetime import date, datetime, timezone, timedelta
from science import demo_data, analyze, window_intervals, anomaly_flags
from horizons import get_observer_ephemeris

def test_demo_samples_and_bounds():
    sun, earth = demo_data(-89.5,0,date(2026,11,15),2,2)
    assert len(sun) == 25
    assert all(0 <= p['az'] < 360 and -90 <= p['el'] <= 90 for p in sun)
    d,m=analyze(sun,earth)
    assert len(d)==25
    assert m['duration_hours']==48
    assert 0<=m['joint_hours']<=48
    assert m['joint_hours']<=min(m['sun_hours'],m['earth_hours'])

def test_known_visibility_samples():
    base=datetime(2026,11,15,tzinfo=timezone.utc)
    ss=[{'time':base+timedelta(hours=i),'az':0.,'el':x} for i,x in enumerate([1,-1,1])]
    ee=[{'time':base+timedelta(hours=i),'az':90.,'el':1.} for i in range(3)]
    d,m=analyze(ss,ee)
    assert m['sun_hours']==1 and m['earth_hours']==2 and m['joint_hours']==1
    assert len(window_intervals(d,'joint'))==1  # last endpoint has no following interval

def test_invalid_site_rejected_without_remote_request():
    try: get_observer_ephemeris('10',-92,0,date(2026,11,15))
    except ValueError: return
    assert False

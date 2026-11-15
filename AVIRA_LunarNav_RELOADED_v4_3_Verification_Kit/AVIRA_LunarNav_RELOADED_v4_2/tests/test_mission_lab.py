from datetime import date, datetime, timezone, timedelta
import io
import numpy as np
import pytest
from science import analyze, demo_data
from mission_lab import MissionConstraints, assess, scenario_stress, longest_run, fault_injection, explain
from terrain import read_horizon_csv, TerrainError

BASE=datetime(2026,11,15,tzinfo=timezone.utc)
def ephemeris(sun_vals,earth_vals,dt_h=1):
    s=[{'time':BASE+timedelta(hours=i*dt_h),'az':10.,'el':v} for i,v in enumerate(sun_vals)]
    e=[{'time':BASE+timedelta(hours=i*dt_h),'az':90.,'el':v} for i,v in enumerate(earth_vals)]
    return s,e

def test_best_case_all_visible():
    s,e=ephemeris([12]*7,[20]*7)
    df,m=analyze(s,e)
    assert m['joint_pct']==100 and m['joint_hours']==6
    assert longest_run(df,'earth_visible',False)==0

def test_worst_case_all_dark_and_out_of_contact():
    s,e=ephemeris([-5]*7,[-8]*7)
    df,m=analyze(s,e)
    a=assess(df,m,MissionConstraints(30,4,1,1))
    assert m['joint_pct']==0 and a['max_earth_blackout_h']==6
    assert a['status']=='CONSTRAINTS NOT MET'

def test_mixed_case_blackout_and_reason():
    s,e=ephemeris([5]*7,[2,2,-1,-1,-1,2,2])
    df,m=analyze(s,e)
    a=assess(df,m,MissionConstraints(30,2,1,1))
    assert a['max_earth_blackout_h']==3
    assert 'Maximum Earth blackout' in a['failed']

def test_terrain_obstruction_azimuth_specific():
    s,e=ephemeris([5]*3,[5]*3)
    df,m=analyze(s,e,horizon=lambda az: 6. if az<50 else 0.)
    assert m['sun_hours']==0 and m['earth_hours']==2 and m['joint_hours']==0

def test_stress_is_monotonic():
    s,e=ephemeris([1,3,5,6,2,0],[1,3,5,6,2,0])
    out=scenario_stress(s,e,analyze,3.,MissionConstraints(),2.)
    assert out['Joint %'].iloc[0]>=out['Joint %'].iloc[1]>=out['Joint %'].iloc[2]

def test_fault_injection_reduces_contact():
    s,e=ephemeris([10]*25,[10]*25)
    df,m,a=fault_injection(s,e,analyze,MissionConstraints(),12,8)
    assert m['earth_hours']==16 and m['joint_hours']==16
    assert a['max_earth_blackout_h']==8

def test_incomplete_timestamp_fails_closed():
    s,e=ephemeris([1,2,3],[1,2,3])
    with pytest.raises(ValueError,match='timestamps must match'):analyze(s,e[:-1])

def test_duplicate_timestamp_fails_closed():
    s,e=ephemeris([1,2,3],[1,2,3])
    with pytest.raises(ValueError,match='Duplicate'):analyze(s+[s[0]],e)

def test_nonfinite_fails_closed():
    s,e=ephemeris([1,float('nan'),3],[1,2,3])
    with pytest.raises(ValueError,match='NaN'):analyze(s,e)

def test_negative_clearance_fails():
    s,e=ephemeris([1,2,3],[1,2,3])
    with pytest.raises(ValueError):analyze(s,e,threshold=-.1)

def test_horizon_profile_cyclic_and_validation():
    src='azimuth_deg,elevation_deg\n'+'\n'.join(f'{az},{4 if az==0 else 2}' for az in range(0,360,30))
    fn,df=read_horizon_csv(src.encode())
    assert abs(fn(360)-4)<1e-10
    assert fn(15)==3 and fn(345)==3
    with pytest.raises(TerrainError):read_horizon_csv(b'wrong,cols\n1,2')

def test_explanation_transparency():
    s,e=ephemeris([1]*4,[-1]*4)
    df,m=analyze(s,e)
    a=assess(df,m,MissionConstraints())
    out=explain(m,m,a,a)
    assert any('Neither scenario' in line for line in out)
    assert any('Not a safety certification' in line for line in out)

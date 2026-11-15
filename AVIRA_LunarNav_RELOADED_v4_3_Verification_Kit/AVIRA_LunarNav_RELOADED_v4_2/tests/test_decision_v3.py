from datetime import datetime,timezone,date,timedelta
import json
import pytest
import pandas as pd
from decision_v3 import event_forecast,rank_scenarios,recommend_schedule,solar_incidence_proxy,build_evidence
from science import analyze

def samples(sun_angles,earth_angles,step=2):
    t=datetime(2026,11,15,tzinfo=timezone.utc)
    ss=[{'time':t+timedelta(hours=i*step),'az':0.,'el':float(el)} for i,el in enumerate(sun_angles)]
    ee=[{'time':t+timedelta(hours=i*step),'az':0.,'el':float(el)} for i,el in enumerate(earth_angles)]
    return analyze(ss,ee)

def test_event_bracketing():
    d,_=samples([-3,-1,1,3],[2,2,2,2]);x=event_forecast(d,'sun_visible')
    assert x['event_count']==1 and 'rises' in x['next_event']
    assert x['longest_visible_h']==2 and x['longest_blackout_h']==4

def test_best_case_no_events():
    d,_=samples([4]*5,[9]*5);x=event_forecast(d,'earth_visible')
    assert x['event_count']==0 and x['longest_visible_h']==8

def test_worst_case_permanent_blackout():
    d,_=samples([4]*5,[-9]*5);x=event_forecast(d,'earth_visible')
    assert x['longest_blackout_h']==8 and x['longest_visible_h']==0

def test_rank_eligible_over_high_percentage_ineligible():
    a={'joint_hours':100,'earth_hours':100};b={'joint_hours':80,'earth_hours':90}
    result=rank_scenarios([('A',a,{'failed':['blackout'],'max_earth_blackout_h':1}),('B',b,{'failed':[],'max_earth_blackout_h':2})])
    assert result['winner']=='B'

def test_rank_no_eligible_fails_closed():
    v=rank_scenarios([('A',{'joint_hours':1},{'failed':['sunlight'],'max_earth_blackout_h':9})])
    assert v['winner'] is None

def test_schedule_no_feasible():
    d=pd.DataFrame([{'Screening':'CONSTRAINTS NOT MET','Joint visibility %':99,'Longest Earth blackout h':20,'Shift days':1}])
    assert 'No evaluated date shift' in recommend_schedule(d)

def test_schedule_picks_feasible_not_highest_failed():
    d=pd.DataFrame([{'Screening':'CONSTRAINTS NOT MET','Joint visibility %':99,'Longest Earth blackout h':20,'Shift days':1},
                    {'Screening':'CONSTRAINTS MET','Joint visibility %':60,'Longest Earth blackout h':2,'Shift days':3}])
    assert '+3 days' in recommend_schedule(d)

def test_solar_proxy_night_and_zenith():
    d,_=samples([-2,-2,-2],[3,3,3]);assert solar_incidence_proxy(d)==0
    d,_=samples([90,90,90],[3,3,3]);assert solar_incidence_proxy(d)==pytest.approx(1)

def test_solar_tilt_not_faked():
    d,_=samples([30,30,30],[3,3,3])
    assert pd.isna(solar_incidence_proxy(d,panel_tilt_deg=30))

def test_evidence_explicitly_synthetic():
    d,m=samples([4]*3,[5]*3)
    raw=build_evidence('SYNTHETIC DEMO (OFFLINE)',[(-89,0,date(2026,11,15),d,m),(-89,90,date(2026,11,15),d,m)],2,0,[(False,''),(True,'user provided')])
    j=json.loads(raw)
    assert 'NOT NASA' in j['data_mode']
    assert j['scenarios'][0]['horizon_mask_uploaded'] is False
    assert j['scenarios'][1]['horizon_mask_source']=='user provided'

def test_evidence_live_label():
    d,m=samples([4]*3,[5]*3)
    j=json.loads(build_evidence('NASA JPL Horizons (LIVE)',[(-89,0,date(2026,11,15),d,m),(-89,90,date(2026,11,15),d,m)],2,0,[(False,''),(False,'')]))
    assert j['data_mode']=='NASA JPL Horizons API' and j['source_url'].startswith('https:')

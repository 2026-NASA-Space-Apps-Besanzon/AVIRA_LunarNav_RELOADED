from datetime import date
import pandas as pd
import pytest
from science import demo_data,analyze
from energy import PowerConfig,simulate_battery
from quality import evidence_status,verdict
from mission_lab import MissionConstraints, assess


def sample(hours=24,sun_el=10,earth_el=10):
    times=pd.date_range('2026-11-15',periods=hours+1,freq='h',tz='UTC')
    return pd.DataFrame({'time':times,'sun_el':[sun_el]*(hours+1),'sun_visible':[sun_el>0]*(hours+1), 'earth_visible':[earth_el>0]*(hours+1)})

def test_darkness_battery_drains():
    out,m=simulate_battery(sample(sun_el=-4),PowerConfig(battery_capacity_wh=1000,constant_load_w=100,min_reserve_pct=10))
    assert m['reserve_breached'] and m['minimum_battery_pct']==0

def test_abundant_light_can_charge():
    out,m=simulate_battery(sample(sun_el=75),PowerConfig(battery_capacity_wh=1000,initial_charge_pct=30,constant_load_w=10))
    assert m['final_battery_pct']>=90 and not m['reserve_breached']

def test_zero_load_does_not_drain():
    out,m=simulate_battery(sample(sun_el=-10),PowerConfig(constant_load_w=0))
    assert m['minimum_battery_pct']==100

def test_full_battery_does_not_overflow():
    out,m=simulate_battery(sample(sun_el=80),PowerConfig(constant_load_w=0))
    assert m['final_battery_pct']==100 and m['saturated_wh']>0

@pytest.mark.parametrize('kw',[{'battery_capacity_wh':-1},{'panel_area_m2':0},{'panel_efficiency':1.4},{'initial_charge_pct':101},{'charge_efficiency':0},{'min_reserve_pct':-2},{'constant_load_w':-1}])
def test_invalid_power_input(kw):
    with pytest.raises(ValueError): simulate_battery(sample(),PowerConfig(**kw))

def test_bad_time_axis_rejected():
    d=sample();d.loc[1,'time']=d.loc[0,'time']
    with pytest.raises(ValueError):simulate_battery(d)

def test_synthetic_mode_never_validated_pass():
    q=evidence_status('SYNTHETIC DEMO (OFFLINE)',False,False)
    assert q['label']=='DEMO ONLY'
    status,errors=verdict({'failed':[]},q,{'reserve_breached':False})
    assert status.startswith('DEMO')

def test_live_needs_reference_validation():
    q=evidence_status('NASA JPL Horizons (LIVE)',False,False)
    assert not q['eligible_for_scientific_claim']

def test_energy_constraint_cannot_pass():
    q=evidence_status('NASA JPL Horizons (LIVE)',True,True,'LOLA A','LOLA B',live_verified=True)
    status,errors=verdict({'failed':[]},q,{'reserve_breached':True})
    assert 'NOT MET' in status and len(errors)==1

def test_site_attribution_independent():
    q=evidence_status('NASA JPL Horizons (LIVE)',True,True,'source-A','',live_verified=True)
    assert any('attribution' in s for s in q['reasons'])

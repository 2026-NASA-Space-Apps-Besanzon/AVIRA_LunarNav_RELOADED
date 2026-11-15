"""Sampled energy simulation for a fixed horizontal solar panel.
Engineering what-if model, NOT a validated lunar surface power system.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class PowerConfig:
    panel_area_m2: float = 2.0
    panel_efficiency: float = 0.28
    solar_irradiance_w_m2: float = 1361.0
    constant_load_w: float = 60.0
    battery_capacity_wh: float = 2200.0
    initial_charge_pct: float = 100.0
    min_reserve_pct: float = 15.0
    charge_efficiency: float = 0.92
    discharge_efficiency: float = 0.95


def simulate_battery(df, p=PowerConfig()):
    """Euler integration over left-sample intervals. All electrical inputs are assumed.
    Returns data-frame and explicit reserve breach; no terrain/thermal/RF model.
    """
    if len(df) < 2 or not {'time','sun_el','sun_visible'}.issubset(df.columns):
        raise ValueError('Missing solar geometry samples')
    for key in p.__dataclass_fields__:
        if not np.isfinite(getattr(p,key)):
            raise ValueError(f'Invalid nonfinite power assumption: {key}')
    if not (p.panel_area_m2 > 0 and 0 < p.panel_efficiency <= 1
       and p.solar_irradiance_w_m2 > 0 and p.constant_load_w >= 0
       and p.battery_capacity_wh > 0 and 0 <= p.initial_charge_pct <= 100
       and 0 <= p.min_reserve_pct <= 100 and 0 < p.charge_efficiency <= 1
       and 0 < p.discharge_efficiency <= 1):
        raise ValueError('Power inputs outside physical/defined bounds')
    ts=pd.to_datetime(df.time,utc=True)
    dts=np.diff(ts.astype('int64').to_numpy())/3.6e12
    if (dts<=0).any(): raise ValueError('Non-increasing power timeline')
    initial=p.battery_capacity_wh*p.initial_charge_pct/100.
    minimum=p.battery_capacity_wh*p.min_reserve_pct/100.
    current=initial; values=[current]; generated=consumed=spill=0.
    for i,hours in enumerate(dts):
        el=float(df.sun_el.iloc[i])
        if not -90 <= el <= 90 or not np.isfinite(el):
            raise ValueError('Invalid solar elevation')
        flux=max(0.,np.sin(np.deg2rad(el))) if bool(df.sun_visible.iloc[i]) else 0.
        solar_w=p.solar_irradiance_w_m2*p.panel_area_m2*p.panel_efficiency*flux
        direct_use=min(solar_w,p.constant_load_w)
        charge_wh=max(0.,solar_w-p.constant_load_w)*p.charge_efficiency*hours
        battery_draw_wh=max(0.,p.constant_load_w-solar_w)/p.discharge_efficiency*hours
        current_unclamped=current+charge_wh-battery_draw_wh
        spill+=max(0.,current_unclamped-p.battery_capacity_wh)
        current=min(p.battery_capacity_wh,max(0.,current_unclamped))
        values.append(current)
        generated+=solar_w*hours
        consumed+=p.constant_load_w*hours
    out=df[['time','sun_el','sun_visible']].copy()
    out['battery_wh']=values
    out['battery_pct']=100*out.battery_wh/p.battery_capacity_wh
    min_charge=float(out.battery_pct.min())
    breach=min_charge < p.min_reserve_pct - 1e-9
    return out,{'minimum_battery_pct':min_charge,'final_battery_pct':float(out.battery_pct.iloc[-1]),
        'reserve_breached':bool(breach),'generated_wh':float(generated),'load_wh':float(consumed),
        'battery_floor_wh':minimum,'saturated_wh':float(spill),'power_model':'ASSUMPTION-BASED HORIZONTAL-PANEL PROXY'}

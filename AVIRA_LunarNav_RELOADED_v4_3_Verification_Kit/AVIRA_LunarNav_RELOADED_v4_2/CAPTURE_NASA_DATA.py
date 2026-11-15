"""Retrieve actual NASA/JPL Horizons samples for two south-pole candidate coordinates.
No synthetic fallback. Saves raw response, URL, CSV, graph and audit summary.
Usage: python CAPTURE_NASA_DATA.py --date 2026-11-15 --days 2 --step-hours 2
"""
import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
import pandas as pd
from horizons import get_observer_ephemeris, HorizonsError
from science import analyze

SITES = {'A_89p5S_0E': (-89.5, 0.0), 'B_89p5S_90E': (-89.5, 90.0)}

def generate(output, start, days=2, step_hours=2):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    summary={'status':'INCOMPLETE','source':'NASA/JPL Horizons','endpoint':'https://ssd.jpl.nasa.gov/api/horizons.api','retrieved_utc':datetime.now(timezone.utc).isoformat(),'date_utc':start.isoformat(),'days':days,'step_hours':step_hours,'terrain':'NONE: geometric horizon, not NASA LOLA','sites':{}}
    for label, (lat,lon) in SITES.items():
        raw = output/label
        raw.mkdir(exist_ok=True)
        sun = get_observer_ephemeris('10',lat,lon,start,days,f'{step_hours}h',capture_dir=raw)
        earth = get_observer_ephemeris('399',lat,lon,start,days,f'{step_hours}h',capture_dir=raw)
        df, metrics=analyze(sun, earth)
        df.to_csv(output / f'{label}_NASA_ephemeris_analysis.csv',index=False)
        import plotly.graph_objects as go
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=df.time,y=df.sun_el,name='Sun elevation',mode='lines+markers'))
        fig.add_trace(go.Scatter(x=df.time,y=df.earth_el,name='Earth elevation',mode='lines+markers'))
        fig.add_hline(y=0,line_dash='dash',annotation_text='Geometric horizon 0°')
        fig.update_layout(title=f'{label}: NASA/JPL Horizons, geocentric Moon site (airless), {start} UTC',xaxis_title='UTC',yaxis_title='Elevation (degrees)',template='plotly_white')
        fig.write_html(output/f'{label}_NASA_visibility.html', include_plotlyjs=True)
        summary['sites'][label]={'coordinates_lat_lon_deg':[lat,lon],'rows':len(df),'metrics':metrics,'csv':f'{label}_NASA_ephemeris_analysis.csv','chart':f'{label}_NASA_visibility.html','raw_dir':label}
    summary['status']='LIVE_NASA_RESPONSES_CAPTURED__GEOMETRIC_HORIZON_ONLY'
    (output/'NASA_DATA_MANIFEST.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--date',default='2026-11-15');p.add_argument('--days',type=int,default=2);p.add_argument('--step-hours',type=int,default=2);p.add_argument('--output',default='NASA_EVIDENCE')
    args=p.parse_args()
    try:
        result=generate(args.output,date.fromisoformat(args.date),args.days,args.step_hours)
        print('SUCCESS: NASA data captured and CSV/HTML charts saved in',args.output)
        for k,v in result['sites'].items():print(k,'samples',v['rows'],'sun visible %',round(v['metrics']['sun_pct'],2),'Earth visible %',round(v['metrics']['earth_pct'],2))
    except Exception as exc:
        print('FAILED: real NASA data was NOT verified:',type(exc).__name__,str(exc))
        raise SystemExit(1)

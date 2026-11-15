"""Generate self-contained NASA-data-only 3D animation from CAPTURE_NASA_DATA evidence.
No synthetic fallback. Geometric-horizon only; decorative lander and terrain are schematic.
Usage: python BUILD_NASA_3D_RESULTS.py --evidence NASA_EVIDENCE
"""
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def check_source(folder):
    folder = Path(folder)
    p = folder / 'NASA_DATA_MANIFEST.json'
    if not p.is_file():
        raise ValueError('No NASA evidence manifest. Run CAPTURE_NASA_DATA.py successfully first.')
    meta=json.loads(p.read_text(encoding='utf-8'))
    if meta.get('status')!='LIVE_NASA_RESPONSES_CAPTURED__GEOMETRIC_HORIZON_ONLY':
        raise ValueError('This visualization requires captured LIVE NASA responses, not synthetic data.')
    sites=meta.get('sites',{})
    if len(sites)<2:
        raise ValueError('Two site results are required')
    for name,site in sites.items():
        if not (folder / site['csv']).is_file():
            raise ValueError(f'Missing NASA-derived CSV for {name}')
        rawdir=folder/site['raw_dir']
        for target in ('sun','earth'):
            raws=list(rawdir.glob(f'{target}_*.raw.txt'))
            requests=list(rawdir.glob(f'{target}_*.request.json'))
            if len(raws)!=1 or len(requests)!=1:
                raise ValueError(f'NASA raw evidence not found uniquely for {name}: {target}')
            raw=raws[0].read_text(encoding='utf-8')
            if '$$SOE' not in raw or '$$EOE' not in raw:
                raise ValueError('Raw ephemeris markers absent')
            req=json.loads(requests[0].read_text(encoding='utf-8'))
            if req.get('source')!='https://ssd.jpl.nasa.gov/api/horizons.api':
                raise ValueError('Unexpected API provenance')
    return meta


def unit(az,el):
    az=np.radians(float(az)); el=np.radians(float(el)); r=np.cos(el)
    # East / North / Up; azimuth is measured clockwise from north.
    return [float(r*np.sin(az)), float(r*np.cos(az)), float(np.sin(el))]


def visualize(folder, output=None):
    folder=Path(folder)
    meta=check_source(folder)
    frames=[]; traces=[]; layout_title=''
    labels=list(meta['sites'])
    allsites=[]
    for label in labels:
        s=meta['sites'][label]
        df=pd.read_csv(folder/s['csv'])
        need=['time','sun_az','sun_el','earth_az','earth_el','sun_visible','earth_visible']
        if not set(need).issubset(df): raise ValueError(f'CSV missing fields: {label}')
        if df[need].isnull().any().any() or len(df)<2: raise ValueError('Missing ephemeris samples')
        ts=pd.to_datetime(df.time,utc=True,errors='raise')
        if not ts.is_monotonic_increasing or ts.duplicated().any(): raise ValueError('Bad time order')
        for col in ('sun_az','earth_az'):
            if not df[col].between(0,360).all():raise ValueError('Invalid azimuth')
        for col in ('sun_el','earth_el'):
            if not df[col].between(-90,90).all():raise ValueError('Invalid elevation')
        allsites.append(df)
    fig=make_subplots(rows=2,cols=2,specs=[[{'type':'scene'},{'type':'scene'}],[{'type':'xy'},{'type':'xy'}]],subplot_titles=[f'{label}: local ENU directions' for label in labels]+[f'{label}: sampled horizon visibility' for label in labels],row_heights=[.65,.35],vertical_spacing=.08)
    n=min(len(df) for df in allsites)
    # Scene: reference horizon as schematic flat surface, a simple schematic lander, and direction rays.
    indices=[]
    for idx,df in enumerate(allsites):
        col=idx+1
        xx=np.linspace(-1.4,1.4,12); yy=np.linspace(-1.4,1.4,12)
        grid=np.zeros((12,12))
        fig.add_trace(go.Surface(x=xx,y=yy,z=grid,colorscale=[[0,'#777d84'],[1,'#a0a5aa']],showscale=False,opacity=.9,hoverinfo='skip',name='Schematic flat horizon'),row=1,col=col)
        # schematic landing craft
        for dx,dy in [(-.14,-.14),(.14,-.14),(-.14,.14),(.14,.14)]:
            fig.add_trace(go.Scatter3d(x=[0,dx*2],y=[0,dy*2],z=[.26,.02],mode='lines',line=dict(color='#f5d27c',width=5),showlegend=False,hoverinfo='skip'),row=1,col=col)
        fig.add_trace(go.Scatter3d(x=[0],y=[0],z=[.28],mode='markers',marker=dict(size=10,color='#e6e9ec',symbol='square'),name='Schematic lander',showlegend=(idx==0)),row=1,col=col)
        for target,color in [('sun','#f7b840'),('earth','#56b9ff')]:
            xyz=unit(df.iloc[0][f'{target}_az'],df.iloc[0][f'{target}_el'])
            lineindex=len(fig.data)
            fig.add_trace(go.Scatter3d(x=[0,xyz[0]],y=[0,xyz[1]],z=[.3,xyz[2]],mode='lines+markers',line=dict(color=color,width=8),marker=dict(color=color,size=5),name=target.title(),showlegend=(idx==0),hovertemplate=target.title()+' direction<extra></extra>'),row=1,col=col)
            indices.append((lineindex,idx,target))
        fig.add_trace(go.Scatter(x=df.time,y=df.sun_el,name='Sun elevation',line=dict(color='#d99b2b',width=2),legendgroup='sun',showlegend=(idx==0)),row=2,col=col)
        fig.add_trace(go.Scatter(x=df.time,y=df.earth_el,name='Earth elevation',line=dict(color='#378ac7',width=2),legendgroup='earth',showlegend=(idx==0)),row=2,col=col)
        fig.add_trace(go.Scatter(x=[df.time.iloc[0],df.time.iloc[-1]],y=[0,0],mode='lines',line=dict(color='#828b94',dash='dash',width=1),showlegend=False,hoverinfo='skip'),row=2,col=col)
    for k in range(n):
        updates=[]
        for _,idx,target in indices:
            df=allsites[idx]
            xyz=unit(df.iloc[k][f'{target}_az'],df.iloc[k][f'{target}_el'])
            updates.append(go.Scatter3d(x=[0,xyz[0]],y=[0,xyz[1]],z=[.3,xyz[2]]))
        frames.append(go.Frame(data=updates,traces=[i for i,_,_ in indices],name=str(k)))
    fig.frames=frames
    buttons=[dict(label='Play',method='animate',args=[None,{'frame':{'duration':250,'redraw':True},'transition':{'duration':0},'fromcurrent':True}]),dict(label='Pause',method='animate',args=[[None],{'frame':{'duration':0,'redraw':False},'mode':'immediate'}])]
    steps=[dict(label=str(i),method='animate',args=[[str(i)],{'mode':'immediate','frame':{'duration':0,'redraw':True},'transition':{'duration':0}}]) for i in range(n)]
    fig.update_layout(title=dict(text='AVIRA LunarNav | Captured NASA/JPL Horizons geometry — terrain & lander schematic<br><sup>Geometric horizon only. NOT terrain-aware, flight-qualified, or an actual landing simulation.</sup>',font=dict(size=18)),height=850,template='plotly_white',margin=dict(l=24,r=24,t=115,b=40),updatemenus=[dict(type='buttons',buttons=buttons,x=.03,y=-.04,direction='left')],sliders=[dict(active=0,steps=steps,x=.27,len=.70,y=-.045,currentvalue=dict(prefix='Sample: '))])
    for idx in range(2):
        fig.update_scenes(xaxis=dict(title='East',range=[-1.45,1.45]),yaxis=dict(title='North',range=[-1.45,1.45]),zaxis=dict(title='Up',range=[-1,1.1]),aspectmode='cube',row=1,col=idx+1)
        fig.update_yaxes(title_text='Elevation (°)',range=[-90,90],row=2,col=idx+1)
    output=Path(output) if output else folder/'NASA_LIVE_3D_COMPARISON.html'
    fig.write_html(output,include_plotlyjs=True,full_html=True)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',default='NASA_EVIDENCE');p.add_argument('--output');a=p.parse_args()
    try: print('WROTE:',visualize(a.evidence,a.output))
    except Exception as e: print('CANNOT BUILD NASA 3D RESULT:',str(e));raise SystemExit(1)

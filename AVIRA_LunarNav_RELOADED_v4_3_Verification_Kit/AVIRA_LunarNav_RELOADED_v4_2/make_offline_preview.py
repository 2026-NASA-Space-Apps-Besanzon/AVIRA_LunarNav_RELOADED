"""Produce a standalone interactive, OFFLINE synthetic demonstration HTML.
No NASA data are used or claimed here. Plotly JS is embedded into the HTML.
"""
from datetime import date
from pathlib import Path
from html import escape
import numpy as np
import plotly.graph_objects as go
from plotly.io import to_html
from science import demo_data, analyze
from energy import simulate_battery, PowerConfig
from mission_lab import assess, MissionConstraints


def make_preview(path='OFFLINE_SYNTHETIC_3D_PREVIEW.html'):
    day=date(2026,11,15)
    s_a,e_a=demo_data(-89.5,0,day,days=5,step_hours=2)
    s_b,e_b=demo_data(-89.5,90,day,days=5,step_hours=2)
    a,ma=analyze(s_a,e_a); b,mb=analyze(s_b,e_b)
    pa,ea=simulate_battery(a,PowerConfig());pb,eb=simulate_battery(b,PowerConfig())
    lim=MissionConstraints(); xa=assess(a,ma,lim); xb=assess(b,mb,lim)
    sky=go.Figure()
    # Animated 3D radial directions with a geometric horizon, not a terrain DEM.
    r=np.linspace(0,2*np.pi,100)
    sky.add_trace(go.Scatter3d(x=np.cos(r)*2.6,y=np.sin(r)*2.6,z=np.zeros_like(r),mode='lines',line=dict(color='#4b6580',width=4),name='Local geometric horizon'))
    sky.add_trace(go.Scatter3d(x=[0],y=[0],z=[0],mode='markers+text',text=['LANDER'],textposition='top center',marker=dict(size=9,color='#fafbff'),name='Site'))
    def ray(az,el,col,label):
        x=2.5*np.sin(np.deg2rad(az))*np.cos(np.deg2rad(el))
        y=2.5*np.cos(np.deg2rad(az))*np.cos(np.deg2rad(el))
        z=2.5*np.sin(np.deg2rad(el))
        return go.Scatter3d(x=[0,x],y=[0,y],z=[0,z],mode='lines+markers+text',text=['',label],line=dict(color=col,width=12),marker=dict(size=[2,10],color=col),textposition='top center',name=label)
    sky.add_trace(ray(a.sun_az.iloc[0],a.sun_el.iloc[0],'#f9c46a','SUN'))
    sky.add_trace(ray(a.earth_az.iloc[0],a.earth_el.iloc[0],'#6bc8ff','EARTH'))
    frames=[]
    for i in range(0,len(a),2):
        f=a.iloc[i]
        frames.append(go.Frame(name=str(i),data=[ray(f.sun_az,f.sun_el,'#f9c46a','SUN'),ray(f.earth_az,f.earth_el,'#6bc8ff','EARTH')],traces=[2,3]))
    sky.frames=frames
    sky.update_layout(template='plotly_dark',paper_bgcolor='#101e31',height=510,margin=dict(l=0,r=0,t=15,b=0),scene=dict(bgcolor='#101e31',aspectmode='cube',xaxis_title='East',yaxis_title='North',zaxis_title='Up',xaxis_range=[-3,3],yaxis_range=[-3,3],zaxis_range=[-3,3]),
        updatemenus=[dict(type='buttons',buttons=[dict(label='▶ Animate',method='animate',args=[None,dict(frame=dict(duration=160,redraw=True),fromcurrent=True,transition=dict(duration=0))]),dict(label='⏸ Pause',method='animate',args=[[None],dict(frame=dict(duration=0,redraw=False),mode='immediate')])],x=0,y=1.05)],showlegend=True)
    timeline=go.Figure()
    for d,tag,dash in [(a,'A','solid'),(b,'B','dash')]:
        timeline.add_trace(go.Scatter(x=d.time,y=d.sun_el,mode='lines',name=f'{tag} Sun',line=dict(color='#ffc56e',dash=dash,width=2)))
        timeline.add_trace(go.Scatter(x=d.time,y=d.earth_el,mode='lines',name=f'{tag} Earth',line=dict(color='#6bc8ff',dash=dash,width=2)))
    timeline.add_hline(y=0,line_dash='dot',line_color='#f7f7f7')
    timeline.update_layout(template='plotly_dark',paper_bgcolor='#101e31',plot_bgcolor='#101e31',height=360,margin=dict(l=45,r=15,t=15,b=45),yaxis_title='Geometric elevation (°)',xaxis_title='UTC',legend=dict(orientation='h',y=1.2))
    bat=go.Figure()
    for d,tag,c in [(pa,'A','#7ce7b2'),(pb,'B','#e0a7ff')]:
        bat.add_trace(go.Scatter(x=d.time,y=d.battery_pct,mode='lines',name=f'{tag} battery',line=dict(color=c,width=3)))
    bat.add_hline(y=15,line_dash='dash',line_color='#ff8c9e',annotation_text='15% assumed reserve')
    bat.update_layout(template='plotly_dark',paper_bgcolor='#101e31',plot_bgcolor='#101e31',height=350,margin=dict(l=45,r=15,t=15,b=45),yaxis_title='Assumed battery state (%)',xaxis_title='UTC')
    def metric(name,v):return f'<div class="metric"><small>{escape(name)}</small><b>{escape(v)}</b></div>'
    cards=''.join([metric('A sunlight',f'{ma["sun_hours"]:.1f} h'),metric('A Earth link',f'{ma["earth_hours"]:.1f} h'),metric('A joint visibility',f'{ma["joint_pct"]:.1f}%'),metric('A min battery',f'{ea["minimum_battery_pct"]:.1f}%'),metric('B sunlight',f'{mb["sun_hours"]:.1f} h'),metric('B Earth link',f'{mb["earth_hours"]:.1f} h'),metric('B joint visibility',f'{mb["joint_pct"]:.1f}%'),metric('B min battery',f'{eb["minimum_battery_pct"]:.1f}%')])
    skydiv=to_html(sky,full_html=False,include_plotlyjs=True,config={'responsive':True,'displaylogo':False})
    timediv=to_html(timeline,full_html=False,include_plotlyjs=False,config={'responsive':True,'displaylogo':False})
    batdiv=to_html(bat,full_html=False,include_plotlyjs=False,config={'responsive':True,'displaylogo':False})
    html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AVIRA LunarNav — offline demonstration</title><style>body{{background:#081220;color:#e8f1ff;font:16px system-ui,-apple-system,sans-serif;margin:0}}main{{max-width:1250px;margin:auto;padding:25px}}header{{background:linear-gradient(110deg,#18344d,#0d1b33);padding:27px;border-radius:18px;border:1px solid #355675}}h1{{margin:0;font-size:2.1rem}}p{{color:#b7cde2}}.warning{{background:#563321;color:#ffe2b8;border:1px solid #9f6031;padding:15px;border-radius:10px;margin:18px 0;font-weight:650}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:18px 0}}.metric{{background:#13243a;border:1px solid #29415b;padding:18px;border-radius:12px}}small{{color:#b7cde2;display:block}}.metric b{{font-size:1.65rem;display:block;margin-top:6px}}section{{background:#101e31;border:1px solid #2a425a;border-radius:15px;margin-top:20px;padding:13px}}h2{{padding-left:12px}}footer{{color:#adbfce;padding:25px 0}}</style></head><body><main><header><h1>🌙 AVIRA LunarNav RELOADED</h1><p>Lunar Mission Resilience & Recovery Navigator • Interactive technical preview</p></header><div class="warning">⚠ SYNTHETIC OFFLINE DEMONSTRATION — NOT NASA DATA. All positions and numerical results on this page are generated for software testing. Scientific claims require live JPL Horizons validation and real terrain masks.</div><div class="metrics">{cards}</div><section><h2>Animated lunar sky geometry</h2><p>Play or rotate the 3D view. Ray vectors represent generated Sun/Earth angles and the ring is a mathematical flat horizon. No real terrain is shown.</p>{skydiv}</section><section><h2>Sun & Earth elevation comparison</h2>{timediv}</section><section><h2>Assumption-based power-reserve test</h2><p>Fixed horizontal panel: 2 m², assumed 28% efficiency, 60 W constant load, 2.2 kWh battery initially full. Not a mission-rated power model.</p>{batdiv}</section><footer>AVIRA LunarNav RELOADED v4 • Independent NASA Space Apps Challenge project • AI-assisted software development disclosed • Not affiliated with or endorsed by NASA.</footer></main></body></html>'''
    Path(path).write_text(html,encoding='utf-8')
    return Path(path)

if __name__=='__main__':
    p=make_preview()
    print(f'Created {p} ({p.stat().st_size:,} bytes)')

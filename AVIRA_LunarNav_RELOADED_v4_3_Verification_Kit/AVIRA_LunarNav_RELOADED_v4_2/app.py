"""AVIRA LunarNav RELOADED | NASA Space Apps Challenge 2026.
Run: streamlit run app.py
"""
from datetime import date, timedelta
import json
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from science import SITES, demo_data, analyze, window_intervals, advisory, anomaly_flags
from horizons import get_observer_ephemeris, HorizonsError
from mission_lab import MissionConstraints, assess, scenario_stress, fault_injection, explain
from terrain import read_horizon_csv, TerrainError
from decision_v3 import event_forecast, rank_scenarios, build_evidence, solar_incidence_proxy, recommend_schedule
from energy import PowerConfig, simulate_battery
from quality import evidence_status, verdict

st.set_page_config(page_title='AVIRA LunarNav RELOADED', page_icon='🌙', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.stApp { background: radial-gradient(ellipse at top, #182745 0%, #08101f 48%, #060c17 100%); color: #e6efff; }
[data-testid="stSidebar"] {background:#0a172a;} h1,h2,h3 {color:#eaf2ff!important;}
[data-testid="stMetric"] {background:#101f36;border:1px solid #253c5d;border-radius:14px;padding:14px;}
.small {font-size:12px;color:#92abc6;} .hero {background:linear-gradient(110deg,#152946,#101c34); padding:20px 24px;border:1px solid #2c476b;border-radius:18px;margin-bottom:16px;}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🌙 AVIRA LunarNav RELOADED</h1><b>Lunar Landing Site Navigator · NASA Space Apps Challenge 2026</b><p>Explore · Compare · Validate — Sunlight, direct-to-Earth geometry, mission schedule resilience</p></div>',unsafe_allow_html=True)

with st.sidebar:
    st.header('⚙️ Mission controls')
    data_mode=st.radio('Scientific data source', ['NASA JPL Horizons (LIVE)', 'SYNTHETIC DEMO (OFFLINE)'], help='Offline values are illustrative and are not NASA measurements.')
    st.markdown('#### Scenario A')
    name_a=st.selectbox('Candidate site',list(SITES),index=1)
    manual_a=st.checkbox('Custom coordinates A')
    lat_a, lon_a = SITES[name_a]
    if manual_a:
        lat_a=st.number_input('Latitude A (deg)',-90.,90.,float(lat_a),step=.1)
        lon_a=st.number_input('Longitude A east (deg)',0.,360.,float(lon_a),step=1.)
    start_a=st.date_input('Date A (UTC)',value=date(2026,11,15),min_value=date(1950,1,1),max_value=date(2099,1,1))
    st.markdown('#### Scenario B')
    name_b=st.selectbox('Comparison site',list(SITES),index=2)
    manual_b=st.checkbox('Custom coordinates B')
    lat_b,lon_b=SITES[name_b]
    if manual_b:
        lat_b=st.number_input('Latitude B (deg)',-90.,90.,float(lat_b),step=.1)
        lon_b=st.number_input('Longitude B east (deg)',0.,360.,float(lon_b),step=1.)
    offset=st.slider('Schedule shift B (days)',-14,14,0)
    start_b=start_a+timedelta(days=offset)
    days=st.slider('Analysis horizon (days)',1,14,5)
    step=st.select_slider('Sampling interval',options=[1,2,3,6],value=2,format_func=lambda h:f'{h} hours')
    threshold=st.slider('Visibility clearance above horizon (°)',0.,10.,0.,.5)
    minimum_joint=st.slider('Minimum joint visibility (%)',0,100,30,5)
    st.markdown('#### Surface & fault-tolerance lab')
    horizon_upload_a=st.file_uploader('Site A horizon mask CSV (optional)',type=['csv'],key='terrain_a',help='Site A only; azimuth_deg,elevation_deg. Supply a documented mask derived from a lunar DEM.')
    horizon_upload_b=st.file_uploader('Site B horizon mask CSV (optional)',type=['csv'],key='terrain_b',help='Site B only; never silently reuse Site A terrain.')
    terrain_source_a=st.text_input('Site A terrain citation / source (if provided)',value='')
    terrain_source_b=st.text_input('Site B terrain citation / source (if provided)',value='')
    array_tilt=0.0  # Horizontal panel only: tilt needs azimuth orientation and a full model.
    uncertainty=st.slider('Horizon clearance sensitivity ±°',0.,10.,2.,.5)
    max_blackout=st.slider('Maximum allowed Earth-link blackout (h)',1.,72.,12.,1.)
    min_sun=st.slider('Minimum geometric sunlight hours',0.,336.,24.,2.)
    min_earth=st.slider('Minimum geometric Earth-link hours',0.,336.,24.,2.)
    inject_fault=st.checkbox('Inject 8h communication fault (what-if)',value=False)
    ai_flag=st.checkbox('Exploratory ML outlier detection',value=True)
    st.markdown('#### ⚡ Power survival what-if (assumptions)')
    panel_area=st.slider('Horizontal array area (m²)',0.5,20.0,2.0,0.5)
    load_w=st.slider('Constant load (W)',0,500,60,5)
    capacity_wh=st.slider('Usable battery capacity (Wh)',100,10000,2200,100)
    reserve_pct=st.slider('Minimum battery reserve (%)',0,80,15,5)
    initial_pct=st.slider('Initial battery charge (%)',0,100,100,5)
    st.caption('Assumed 28% panel conversion, 1361 W/m² incident flux, constant load, no lunar thermal derating or variable panel attitude.')
    st.caption('Each site uses its OWN horizon mask or an explicitly geometric 0° horizon. Solar model is a directional proxy, not power in watts.')

@st.cache_data(ttl=3600,show_spinner=False)
def load_data(mode,lat,lon,start,days,step):
    if mode.startswith('SYNTHETIC'):
        return demo_data(lat,lon,start,days,step)
    return (get_observer_ephemeris('10',lat,lon,start,days,f'{step}h'),
            get_observer_ephemeris('399',lat,lon,start,days,f'{step}h'))

def parse_site_mask(upload, label):
    if upload is None:
        return None, None
    try:
        horizon,profile=read_horizon_csv(upload.getvalue())
        st.success(f'{label}: separate terrain mask enabled; provenance must be checked.')
        return horizon,profile
    except TerrainError as exc:
        st.error(f'{label} invalid horizon: {exc}')
        st.stop()

horizon_a,profile_a=parse_site_mask(horizon_upload_a,'Site A')
horizon_b,profile_b=parse_site_mask(horizon_upload_b,'Site B')
if horizon_upload_a is not None and not terrain_source_a.strip():
    st.warning('Site A mask has no provenance citation; do not claim it is NASA-derived.')
if horizon_upload_b is not None and not terrain_source_b.strip():
    st.warning('Site B mask has no provenance citation; do not claim it is NASA-derived.')
limits=MissionConstraints(min_joint_pct=minimum_joint,max_blackout_hours=max_blackout,min_sun_hours=min_sun,min_earth_hours=min_earth)
if data_mode.startswith('SYNTHETIC'):
    st.error('⚠ SYNTHETIC DEMO MODE — generated mathematical test signals, NOT NASA data or scientifically validated predictions.')
else:
    st.info('NASA JPL Horizons live mode — actual observer ephemerides. Requires internet access; output is geometric-horizon only and not terrain-qualified.')
try:
    with st.spinner('Computing scenario ephemerides and joint visibility...'):
        s_a,e_a=load_data(data_mode,lat_a,lon_a,start_a,days,step)
        s_b,e_b=load_data(data_mode,lat_b,lon_b,start_b,days,step)
        df_a,m_a=analyze(s_a,e_a,threshold=threshold,horizon=horizon_a)
        df_b,m_b=analyze(s_b,e_b,threshold=threshold,horizon=horizon_b)
except (HorizonsError,ValueError,TerrainError) as exc:
    st.error(str(exc))
    st.warning('If offline, switch to SYNTHETIC DEMO mode. Do not cite offline measurements in your NASA submission.')
    st.stop()

power_cfg=PowerConfig(panel_area_m2=panel_area,constant_load_w=float(load_w),battery_capacity_wh=float(capacity_wh),min_reserve_pct=float(reserve_pct),initial_charge_pct=float(initial_pct))
power_a,energy_a=simulate_battery(df_a,power_cfg)
power_b,energy_b=simulate_battery(df_b,power_cfg)
quality=evidence_status(data_mode,horizon_upload_a is not None,horizon_upload_b is not None,terrain_source_a,terrain_source_b,live_verified=False)
st.info(f'**Evidence quality: {quality["label"]}** — ' + '; '.join(quality['reasons']))
metric_cols=st.columns(4)
for c,(title,v,delta) in zip(metric_cols,[('A sunlight hours',m_a['sun_hours'],m_a['sun_hours']-m_b['sun_hours']),('A Earth-link hours',m_a['earth_hours'],m_a['earth_hours']-m_b['earth_hours']),('A joint windows (hours)',m_a['joint_hours'],m_a['joint_hours']-m_b['joint_hours']),('A joint visibility (%)',m_a['joint_pct'],m_a['joint_pct']-m_b['joint_pct'])]):
    c.metric(title,f'{v:.1f}',f'{delta:+.1f} vs B',delta_color='off')

st.caption('DATA STATUS: ' + ('JPL LIVE API RESPONSE' if data_mode.startswith('NASA') else 'SYNTHETIC TEST SIGNALS — NOT NASA DATA') + ' • UTC • site-specific horizon masks • sampled screening only')
st.subheader('🧭 Mission Decision Lab — constraints & resilience')
eval_a=assess(df_a,m_a,limits)
eval_b=assess(df_b,m_b,limits)
cc=st.columns(4)
cc[0].metric('A • Longest Earth blackout',f'{eval_a["max_earth_blackout_h"]:.1f} h')
cc[1].metric('B • Longest Earth blackout',f'{eval_b["max_earth_blackout_h"]:.1f} h')
cc[2].metric('A screening result',eval_a['status'])
cc[3].metric('B screening result',eval_b['status'])
for line in explain(m_a,m_b,eval_a,eval_b):
    st.write('• '+line)
with st.expander('🧪 Best / nominal / worst clearance sensitivity',expanded=True):
    stress_a=scenario_stress(s_a,e_a,lambda x,y,threshold:analyze(x,y,threshold=threshold,horizon=horizon_a),threshold,limits,uncertainty)
    stress_b=scenario_stress(s_b,e_b,lambda x,y,threshold:analyze(x,y,threshold=threshold,horizon=horizon_b),threshold,limits,uncertainty)
    stress_a.insert(0,'Scenario','A');stress_b.insert(0,'Scenario','B')
    st.dataframe(pd.concat([stress_a,stress_b],ignore_index=True).round(2),hide_index=True,use_container_width=True)
    st.caption('Stress margins are user-selected assumptions. Each candidate retains its own independent horizon mask.')
if inject_fault:
    _,fm,fe=fault_injection(s_a,e_a,lambda x,y:analyze(x,y,threshold=threshold,horizon=horizon_a),limits)
    st.error(f'FAULT INJECTION: 8h hypothetical communications interruption from mission hour 12: A joint visibility {m_a["joint_pct"]:.1f}% → {fm["joint_pct"]:.1f}%; longest blackout {fe["max_earth_blackout_h"]:.1f}h. No flight/RF failure prediction is implied.')
for label, profile in [('A',profile_a),('B',profile_b)]:
    if profile is not None:
        with st.expander(f'⛰️ Site {label} terrain horizon profile',expanded=False):
            fig_h=go.Figure(go.Scatterpolar(r=profile.elevation_deg,theta=profile.azimuth_deg,mode='lines',line_color='#66d8cd'))
            fig_h.update_layout(template='plotly_dark',height=320)
            st.plotly_chart(fig_h,use_container_width=True)

st.subheader('⏳ Rise/set forecasts, communication deadlines and solar opportunity')
st.caption('Rise/set is bracketed by adjacent samples; it is NOT a precise calculated crossing. Time uncertainty is at least the sampling interval.')
for c, lab, dd in zip(st.columns(2),['A','B'],[df_a,df_b]):
    with c:
        st.markdown(f'**Candidate {lab}**')
        for column,word in [('sun_visible','Sun'),('earth_visible','Earth')]:
            ev=event_forecast(dd,column)
            st.write(f'{word}: {ev["next_event"]}; maximum uninterrupted visible window {ev["longest_visible_h"]:.1f} h; longest blackout {ev["longest_blackout_h"]:.1f} h')
        proxy=solar_incidence_proxy(dd,panel_tilt_deg=array_tilt)
        st.metric('Horizontal-panel sunlight proxy (0–1)',f'{proxy:.3f}',help='Dimensionless geometric incident sunlight proxy; not electrical power.')

st.subheader('🔋 Power-reserve survivability (assumption-based)')
st.caption('Illustrative energy balance for a FIXED HORIZONTAL array. Not a lunar-qualified battery model; no array tracking, eclipse penumbra, thermal management, dust, night heater, or RF power model.')
pa,pb=st.columns(2)
for col,tag,sim,report in [(pa,'A',power_a,energy_a),(pb,'B',power_b,energy_b)]:
    with col:
        st.metric(f'{tag} minimum battery charge',f'{report["minimum_battery_pct"]:.1f} %')
        if report['reserve_breached']: st.error(f'{tag}: ASSUMED battery reserve violated')
        else: st.success(f'{tag}: assumed battery reserve maintained')
        chart=go.Figure(go.Scatter(x=sim.time,y=sim.battery_pct,mode='lines',line=dict(color='#5ee2ae',width=3)))
        chart.add_hline(y=reserve_pct,line_dash='dash',line_color='#ff7a91')
        chart.update_layout(template='plotly_dark',height=230,margin=dict(l=5,r=5,t=5,b=5),yaxis_title='Charge (%)',xaxis_title='UTC')
        st.plotly_chart(chart,use_container_width=True)
status_a,issues_a=verdict(eval_a,quality,energy_a)
status_b,issues_b=verdict(eval_b,quality,energy_b)
st.subheader('🧾 Evidence-gated overall results')
c1,c2=st.columns(2)
for c,label,stat,issues in [(c1,'A',status_a,issues_a),(c2,'B',status_b,issues_b)]:
    c.write(f'**{label}: {stat}**')
    if issues: c.caption('; '.join(issues))
st.subheader('🌍 Interactive 3D lunar observation geometry')
st.caption('3D terrain illustration is procedural and NOT a NASA LOLA DEM. Sun/Earth arrow angles correspond to the selected ephemeris sample; horizontal distances are schematic.')
which=st.radio('Animate scenario', ['A','B'],horizontal=True)
df=df_a if which=='A' else df_b
idx=st.slider('Time scrubber · UTC sample',0,len(df)-1,0)
frame=df.iloc[idx]
st.write(f"**Selected UTC:** {frame['time'].strftime('%Y-%m-%d %H:%M')}  |  Sun elevation **{frame['sun_el']:+.2f}°**, Earth elevation **{frame['earth_el']:+.2f}°**")

def vector_from_az_el(az,el,length=2.65):
    a,e=np.radians([az,el]);return np.array([length*np.sin(a)*np.cos(e),length*np.cos(a)*np.cos(e),length*np.sin(e)])

def make_3d(record, trajectory):
    # Deterministic illustrative terrain relief. Must not be represented as NASA measurement.
    v=np.linspace(-3,3,95);x,y=np.meshgrid(v,v)
    z=.10*np.sin(x*3.3)*np.cos(y*2.4)-.35*np.exp(-((x-1)**2+(y+.5)**2)/.4)+.12*np.exp(-((x+1.3)**2+(y-1)**2)/.9)
    fig=go.Figure()
    fig.add_trace(go.Surface(x=x,y=y,z=z,colorscale=[[0,'#27384c'],[.5,'#6e7c92'],[1,'#c2d3e3']],showscale=False,opacity=.95,name='Illustrative terrain'))
    # Geometric horizon reference plane, NOT actual terrain horizon.
    fig.add_trace(go.Surface(x=[[-2.9,2.9],[-2.9,2.9]],y=[[-2.9,-2.9],[2.9,2.9]],z=[[0.,0.],[0.,0.]],opacity=.13,colorscale=[[0,'#1cb7b7'],[1,'#1cb7b7']],showscale=False,name='Flat geometric horizon'))
    fig.add_trace(go.Scatter3d(x=[0],y=[0],z=[0.05],mode='markers+text',text=['LANDER'],textposition='top center',marker=dict(size=7,color='#ecf1ff'),name='Site origin'))
    for label,az,el,color in [('SUN',record['sun_az'],record['sun_el'],'#ffb743'),('EARTH',record['earth_az'],record['earth_el'],'#55c9ff')]:
        p=vector_from_az_el(az,el)
        fig.add_trace(go.Scatter3d(x=[0,p[0]],y=[0,p[1]],z=[.1,p[2]],mode='lines+markers+text',text=['',f'{label} {el:+.1f}°'],textposition='top center',line=dict(color=color,width=9),marker=dict(color=color,size=[2,11]),name=label))
    # Animate observed directions; never animate terrain shape as though it were measured.
    def ray(az,el,label,color):
        q=vector_from_az_el(az,el)
        return go.Scatter3d(x=[0,q[0]],y=[0,q[1]],z=[.1,q[2]],mode='lines+markers+text',text=['',f'{label} {el:+.1f}°'],textposition='top center',line=dict(color=color,width=9),marker=dict(color=color,size=[2,11]),name=label)
    stride=max(1,len(trajectory)//48)
    anim_rows=list(range(0,len(trajectory),stride))
    if anim_rows[-1]!=len(trajectory)-1: anim_rows.append(len(trajectory)-1)
    fig.frames=[go.Frame(name=str(i),data=[ray(trajectory.iloc[i]['sun_az'],trajectory.iloc[i]['sun_el'],'SUN','#ffb743'),
                                        ray(trajectory.iloc[i]['earth_az'],trajectory.iloc[i]['earth_el'],'EARTH','#55c9ff')],
                         traces=[3,4]) for i in anim_rows]
    fig.update_layout(updatemenus=[dict(type='buttons',showactive=False,x=.02,y=1.07,
       buttons=[dict(label='▶ Play orbital geometry',method='animate',args=[None,dict(frame=dict(duration=250,redraw=True),fromcurrent=True,transition=dict(duration=0))]),
                dict(label='⏸ Pause',method='animate',args=[[None],dict(frame=dict(duration=0,redraw=False),mode='immediate')])])],
       sliders=[dict(active=0,y=-.03,steps=[dict(label=str(i),method='animate',args=[[str(i)],dict(mode='immediate',frame=dict(duration=0,redraw=True))]) for i in anim_rows])])
    fig.update_layout(height=510,margin=dict(l=0,r=0,t=10,b=0),paper_bgcolor='#0b1527',font_color='#e4efff',scene=dict(bgcolor='#0b1527',xaxis=dict(title='East',range=[-3,3],showbackground=False),yaxis=dict(title='North',range=[-3,3],showbackground=False),zaxis=dict(title='Up',range=[-2.6,3],showbackground=False),aspectratio=dict(x=1,y=1,z=.75),camera=dict(eye=dict(x=1.7,y=-2,z=1.3))),legend=dict(orientation='h',y=1.0))
    return fig
st.plotly_chart(make_3d(frame, df),use_container_width=True)

st.subheader('📈 Sun and Earth elevation over time')
fig=go.Figure()
for d,tag,style in [(df_a,'A','solid'),(df_b,'B','dash')]:
    fig.add_trace(go.Scatter(x=d.time,y=d.sun_el,mode='lines',name=f'{tag} Sun',line=dict(color='#fbbd5b',dash=style,width=2.5)))
    fig.add_trace(go.Scatter(x=d.time,y=d.earth_el,mode='lines',name=f'{tag} Earth',line=dict(color='#58caff',dash=style,width=2.5)))
fig.add_hline(y=threshold,line_dash='dot',line_color='#dddddd',annotation_text=f'Clearance {threshold}°')
fig.update_layout(template='plotly_dark',paper_bgcolor='#0b1527',plot_bgcolor='#0b1527',height=350,yaxis_title='Elevation (degrees)',xaxis_title='UTC',legend=dict(orientation='h',y=1.18),margin=dict(l=20,r=20,t=30,b=20))
st.plotly_chart(fig,use_container_width=True)

st.subheader('🛰️ Explainable recommendation')
# Reject battery-unsafe candidates before selecting a preferred scenario.
from copy import deepcopy
safe_eval_a=deepcopy(eval_a);safe_eval_b=deepcopy(eval_b)
if energy_a['reserve_breached']: safe_eval_a['failed'].append('Assumed battery reserve')
if energy_b['reserve_breached']: safe_eval_b['failed'].append('Assumed battery reserve')
recommendation=rank_scenarios([('A',m_a,safe_eval_a),('B',m_b,safe_eval_b)])
if quality['label']=='DEMO ONLY':
    st.warning('SYNTHETIC DEMO: any comparison below is illustrative only, not a real mission recommendation.')
    st.write(recommendation['reason'])
elif recommendation['winner'] is None:
    st.warning(recommendation['reason'])
else:
    st.info(recommendation['reason'] + ' Independent scientific verification remains required.')
st.caption('Constraint-first screening: an infeasible candidate cannot win purely from its nominal joint-visibility percentage. Never interpreted as landing-safety approval.')

st.subheader('📊 Scenario comparison')
compare=pd.DataFrame([{'Scenario':'A','Coordinates':f'{lat_a:.3f}°, {lon_a:.3f}°E','UTC start':str(start_a),**{k:round(v,2) for k,v in m_a.items()}},
                      {'Scenario':'B','Coordinates':f'{lat_b:.3f}°, {lon_b:.3f}°E','UTC start':str(start_b),**{k:round(v,2) for k,v in m_b.items()}}])
st.dataframe(compare,hide_index=True,use_container_width=True)
st.write('**Scenario A:**', advisory(m_a,minimum_joint),'  **Scenario B:**',advisory(m_b,minimum_joint))
if m_a['joint_pct'] != m_b['joint_pct']:
    winner='A' if m_a['joint_pct'] > m_b['joint_pct'] else 'B'
    st.success(f'On the configured joint-visibility metric only, scenario {winner} has a greater observed sampled joint window. This is NOT a safe-landing determination.')
else:
    st.info('Both scenarios tie on sampled joint-visibility percentage.')

st.subheader('🔁 Mission delay resilience explorer')
st.caption('Compare one candidate at alternative launch/landing dates using exactly the same geometry and engineering constraints. Live mode makes additional Horizons API requests only when Run is clicked.')
shifts=st.multiselect('Explore schedule offsets (days, relative to A)',options=[-7,-3,-1,0,1,3,7],default=[-3,0,3],max_selections=5)
if st.button('▶ Analyze selected date shifts',type='primary'):
    rows=[]
    for shift in shifts:
        shifted_start=start_a+timedelta(days=int(shift))
        try:
            ss,ee=load_data(data_mode,lat_a,lon_a,shifted_start,days,step)
            sdf,sm=analyze(ss,ee,threshold=threshold,horizon=horizon_a)
            assessment=assess(sdf,sm,limits)
            rows.append({'Shift days':shift,'Start UTC':str(shifted_start),'Joint visibility %':round(sm['joint_pct'],2),'Solar h':round(sm['sun_hours'],2),'Earth h':round(sm['earth_hours'],2),'Longest Earth blackout h':round(assessment['max_earth_blackout_h'],2),'Screening':assessment['status']})
        except (HorizonsError, ValueError) as ex:
            st.warning(f'Date shift {shift:+d} unavailable: {ex}')
    if rows:
        schedule=pd.DataFrame(rows)
        st.dataframe(schedule,hide_index=True,use_container_width=True)
        st.write(recommend_schedule(schedule))

st.subheader('⏱ Sampled communication / power windows')
cols=st.columns(2)
for col,dd,label in [(cols[0],df_a,'A'),(cols[1],df_b,'B')]:
    with col:
        st.markdown(f'**Scenario {label}**')
        win=[]
        for cname,caption in [('sun_visible','Solar geometry'),('earth_visible','Earth-link geometry'),('joint','Joint window')]:
            for begin,end in window_intervals(dd,cname):
                win.append({'Window':caption,'From UTC':str(begin),'To UTC':str(end),'Hours':round((end-begin).total_seconds()/3600,1)})
        if win: st.dataframe(pd.DataFrame(win),hide_index=True,use_container_width=True)
        else: st.warning('No above-threshold sampled windows')

if ai_flag:
    st.subheader('🤖 Exploratory machine-learning observations')
    st.caption('Isolation Forest finds unusual Sun/Earth angle combinations within these computed samples. It is NOT trained on NASA mission outcomes, does not predict landing safety, and does not replace physics.')
    flags=anomaly_flags(df_a)
    if flags is None: st.info('ML extension unavailable. Install scikit-learn or increase sample count.')
    else:
        flagged=df_a.loc[flags,['time','sun_el','earth_el']]
        st.write(f'{len(flagged)} / {len(df_a)} time samples flagged as relative numerical outliers (scenario A).')
        if len(flagged): st.dataframe(flagged,hide_index=True,use_container_width=True)

evidence=json.loads(build_evidence(data_mode,[(lat_a,lon_a,start_a,df_a,m_a),(lat_b,lon_b,start_b,df_b,m_b)],step,threshold,[(horizon_upload_a is not None,terrain_source_a),(horizon_upload_b is not None,terrain_source_b)]))
evidence['data_quality']=quality
evidence['power_assumptions']=vars(power_cfg)
evidence['power_results']={'A':energy_a,'B':energy_b}
evidence['overall_verdicts']={'A':status_a,'B':status_b}
evidence=json.dumps(evidence,indent=2,ensure_ascii=False)
st.download_button('⬇ Download reproducibility / provenance manifest (JSON)',data=evidence,file_name='AVIRA_evidence_manifest.json',mime='application/json')
st.download_button('⬇ Export screening stress-test CSV' ,data=pd.concat([stress_a,stress_b]).to_csv(index=False),file_name='AVIRA_mission_stress.csv',mime='text/csv')
st.download_button('⬇ Export Scenario A NASA/synthetic sample CSV',data=df_a.to_csv(index=False),file_name=('NASA_JPL_' if data_mode.startswith('NASA') else 'SYNTHETIC_')+'scenario_A.csv',mime='text/csv')
st.download_button('⬇ Export scenario comparison CSV',data=compare.to_csv(index=False),file_name='lunar_comparison.csv',mime='text/csv')
with st.expander('⚠ Scientific limitations, assumptions and citations', expanded=True):
    st.markdown('''
- **Live mode source:** NASA/JPL Horizons observer ephemeris API, with Moon site `coord@301`, targets Sun `10` and Earth `399`, and Q4 azimuth/elevation.
- **Reference frame / horizon:** topocentric airless, geometric local horizon by default. Upload separate site-specific horizon CSVs to apply terrain blocking; **the mask is not proven NASA-derived without provenance.** The procedural 3D landscape is not a NASA LOLA DEM.
- **Visibility:** local elevation above `max(0°, configured clearance)` is only a first-pass screening test. Antenna mount, terrain, link margin, Earth blockage and trajectory are not modeled.
- **Solar power:** Sun elevation and idealized panel incidence are **not** electrical power production. No complete array orientation, thermal or efficiency model is included.
- **Timing:** fractional hours are sampled and left-edge weighted. Rise/set predictions have up to approximately one sampling interval uncertainty. Continuous windows are not guaranteed.
- **3D scene:** a procedural illustration, NOT NASA terrain or photogrammetry. The arrows use live or clearly labeled synthetic angular values.
- **Mission Decision Lab:** deterministic constraints and date-offset recommendation, maximum blackout duration, and angle-clearance sensitivities; these are screening metrics, not mission certification. Optional fault injection represents an assumed link interruption.
- **ML module:** optional Isolation Forest numerical outlier detection, not scientific anomaly diagnosis or mission validation. Rule-based recommendations are **not** an LLM or a trained safety model.
- **NASA data / documentation:** [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/), [Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html), [NASA LRO/LOLA](https://pgda.gsfc.nasa.gov/products/90).
- **Independence:** AVIRA LunarNav RELOADED is an independent hackathon prototype and is not endorsed by NASA.
''')
st.caption('AVIRA LunarNav RELOADED v4 · Independent educational and early-stage engineering prototype · Not flight-qualified or mission approved.')

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from calculations import *
st.set_page_config(page_title='MCE 3413 | Heat Exchanger',page_icon='🌡️',layout='wide')
st.title('Concentric Tube Heat Exchanger | Performance Dashboard')
st.caption('MCE 3413 • Applied Heat Transfer • Part 1(c)')
with st.sidebar:
    st.header('Model assumptions')
    rho=st.number_input('Water density (kg/m³)',min_value=1.,value=1000.)
    cp=st.number_input('Specific heat (J/kg K)',min_value=1.,value=4180.)
    area=st.number_input('Reference area (m²)',min_value=.000001,value=.02,format='%.5f')
    di=st.number_input('Inner diameter (m)',min_value=.000001,value=.01,format='%.4f')
    do=st.number_input('Outer diameter of inner tube (m)',min_value=.000001,value=.012,format='%.4f')
    ds=st.number_input('Shell inside diameter (m)',min_value=.000001,value=.02,format='%.4f')
    ks=st.number_input('Steel conductivity (W/m K)',min_value=.01,value=16.)
    st.subheader('Transport properties')
    auto=st.checkbox('Automatically interpolate Table A–9',value=True)
    st.caption('Automatic mode uses the mean bulk temperature for each stream and run (0.01–100 °C). Manual overrides are available when unchecked.')
    mu_h=st.number_input('Hot viscosity (Pa s)',min_value=.000001,value=.000467,format='%.7f')
    mu_c=st.number_input('Cold viscosity (Pa s)',min_value=.000001,value=.00085287,format='%.8f')
    kh=st.number_input('Hot conductivity (W/m K)',min_value=.001,value=.654,format='%.5f')
    kc=st.number_input('Cold conductivity (W/m K)',min_value=.001,value=.61028,format='%.5f')
    pr=st.number_input('Hot Prandtl number',min_value=.01,value=2.99)
args=(rho,cp,area,di,do,ds,ks,mu_h,mu_c,kh,kc,pr,auto)
t1,t2,t3,t4,t5=st.tabs(['Calculator','All runs & graphs','Help','Instructions','References'])
with t1:
    flow=st.radio('Flow arrangement',['Parallel','Counter'],horizontal=True)
    run=st.selectbox('Load experimental run',list(range(1,11)))
    defaults=(PARALLEL if flow=='Parallel' else COUNTER)[run-1]
    a,b=st.columns([1,1])
    with a:
        st.subheader('Experimental inputs')
        vals=[st.number_input(c,value=float(v),format='%.3f',key=f'{flow}-{run}-{i}') for i,(c,v) in enumerate(zip(COLS,defaults))]
    with b:
        st.subheader('Calculated performance')
        try:
            r=calculate(vals,flow,*args)
            for labels in [('Q (W)','LMTD (K)'),('U exp','Effectiveness exp (%)'),('NTU exp','Heat imbalance (%)')]:
                for col,label in zip(st.columns(2),labels): col.metric({'U exp':'U exp (W/m²·K)','NTU exp':'NTU exp (dimensionless)'}.get(label,label),f'{r[label]:,.4f}' if 'NTU' in label else f'{r[label]:,.2f}')
            if r['Heat imbalance (%)']>10:st.warning('Heat balance difference exceeds 10%. Check measurements.')
            if r['Re cold']>=2300:st.warning('Annulus may not be laminar; theoretical model is outside its assumed conditions.')
            if 2300<=r['Re hot']<4000:st.info('Hot-side transitional flow: theoretical correlation is approximate.')
            if r['Effectiveness exp (%)']>100:st.warning('Effectiveness exceeds 100%; check measurements.')
        except ValueError as e:st.error(str(e));r=None
    if r:
        st.subheader('Experimental and theoretical comparison')
        st.dataframe(pd.DataFrame([[r['U exp'],r['U theory'],r['U difference (%)']],[r['NTU exp'],r['NTU theory'],r['NTU difference (%)']],[r['Effectiveness exp (%)'],r['Effectiveness theory (%)'],r['Effectiveness difference (%)']]],index=['U (W/m² K)','NTU','Effectiveness (%)'],columns=['Experimental','Theoretical','Difference (%)']).round(4))
        with st.expander('Detailed heat duties, resistances and convection calculations'):st.dataframe(pd.DataFrame(r.items(),columns=['Parameter','Value']))
        fig=go.Figure();fig.add_scatter(x=[0,1],y=[vals[2],vals[3]],name='Hot water',mode='lines+markers');fig.add_scatter(x=[0,1],y=([vals[4],vals[5]] if flow=='Parallel' else [vals[5],vals[4]]),name='Cold water',mode='lines+markers');fig.update_layout(title='Temperature profile (endpoints only)',xaxis_title='Position x/L along hot flow',yaxis_title='Temperature (°C)');st.plotly_chart(fig,use_container_width=True)
with t2:
    st.subheader('20 measured operating points')
    base=pd.DataFrame([['Parallel',i+1,*v] for i,v in enumerate(PARALLEL)]+[['Counter',i+1,*v] for i,v in enumerate(COUNTER)],columns=['Arrangement','Run',*COLS]);base['Cold setting']=['Low']*5+['High']*5+['Low']*5+['High']*5
    data=st.data_editor(base,num_rows='dynamic',use_container_width=True)
    results=[]
    for _,row in data.iterrows():
        try:
            if row['Arrangement'] not in ['Parallel','Counter']:raise ValueError('Select Parallel or Counter')
            results.append({**row.to_dict(),**calculate([row[c] for c in COLS],row['Arrangement'],*args)})
        except (ValueError,TypeError) as e:st.warning(f"Run {row['Run']}: {e}")
    if results:
        out=pd.DataFrame(results); filt=st.multiselect('Show arrangements',['Parallel','Counter'],default=['Parallel','Counter']);view=out[out.Arrangement.isin(filt)]
        for col,(name,grp) in zip(st.columns(2),view.groupby('Arrangement')):col.metric(f'{name} mean U (W/m² K)',f'{grp["U exp"].mean():.2f}',help='Average of selected measured runs');col.metric(f'{name} mean effectiveness (%)',f'{grp["Effectiveness exp (%)"].mean():.2f}')
        st.dataframe(view.round(4),use_container_width=True)
        if not view.empty:
            st.plotly_chart(px.line(view.sort_values('Hot flow (L/min)'),x='Hot flow (L/min)',y='U exp',color='Arrangement',line_dash='Cold setting',markers=True,labels={'U exp':'U (W/m²·K)'},title='U versus hot water flow'),use_container_width=True)
            view=view.copy();view['Hot setting']=((view['Hot flow (L/min)']/.8).round()*.8).map(lambda x:f'{x:.1f}')
            st.plotly_chart(px.line(view.sort_values('Cold flow (L/min)'),x='Cold flow (L/min)',y='U exp',color='Hot setting',facet_col='Arrangement',markers=True,labels={'U exp':'U (W/m²·K)','Hot setting':'Hot flow (L/min)'},title='U versus cold water flow'),use_container_width=True)
            st.plotly_chart(px.scatter(view,x='NTU exp',y='Effectiveness exp (%)',color='Arrangement',hover_data=['Run'],labels={'NTU exp':'NTU (dimensionless)'},title='Effectiveness versus NTU'),use_container_width=True)
            long=view.melt(id_vars=['Run','Arrangement'],value_vars=['U exp','U theory'],var_name='Method',value_name='U (W/m² K)');st.plotly_chart(px.line(long.sort_values('Run'),x='Run',y='U (W/m² K)',color='Arrangement',line_dash='Method',markers=True,title='Experimental versus theoretical U'),use_container_width=True)
            st.download_button('Download results CSV',view.to_csv(index=False),'heat_exchanger_results.csv','text/csv')
with t3:
    st.markdown('**Q:** smaller of hot and cold heat duties (W). **LMTD:** logarithmic mean temperature difference (K). **U:** overall heat transfer coefficient (W/m² K). **NTU:** UA/Cmin. **Effectiveness:** Q divided by maximum possible heat duty. **Heat imbalance:** absolute duty difference divided by larger duty. **Percentage difference:** absolute experimental–theoretical difference divided by theoretical value. The theory assumes Nu = 4.36 for the annulus, Gnielinski for hot Re ≥ 3000 and Nu = 4.36 otherwise. Values close to transition require caution.')
    st.subheader('Governing equations')
    for eq in [r'Q_h=\dot m_h c_p(T_{hi}-T_{ho}),\quad Q_c=\dot m_c c_p(T_{co}-T_{ci})',r'Q=\min(Q_h,Q_c)',r'LMTD=\frac{\Delta T_1-\Delta T_2}{\ln(\Delta T_1/\Delta T_2)}',r'U=\frac{Q}{A_o LMTD}',r'NTU=\frac{UA_o}{C_{min}}',r'\varepsilon=\frac{Q}{C_{min}(T_{hi}-T_{ci})}',r'U_{th}=\frac{1}{A_o(R_h+R_w+R_c)}']:
        st.latex(eq)
with t4:
    st.markdown('1. Select an arrangement and run in Calculator.\n2. Edit measured flow rates and temperatures. Results update automatically.\n3. Keep automatic Table A–9 interpolation enabled for the report method. Adjust dimensions or disable automatic mode for manual property inputs.\n4. Use All runs & graphs to edit, add or compare data and export results.\n5. Consult Help for definitions and References for assumptions.')
with t5:
    st.markdown('**References**\n- HCT, MCE 3413 Applied Heat Transfer Course Project (202610).\n- HCT, Lab 05 and Lab 06, Concentric Tube Heat Exchangers.\n- HCT, Applied Heat Transfer formula sheet, Table A–9.\n- Gnielinski, V. (1976). New equations for heat and mass transfer in turbulent pipe and channel flow. International Chemical Engineering, 16, 359–368.\n\n**Data:** final report Tables 2 and 3. **Assumptions:** steady state, no fouling, negligible external losses, radial wall conduction, assumed geometry. Theory uses linear interpolation of saturated liquid water properties from Table A–9 (formula sheet page 8), or editable manual properties if automatic mode is disabled. Density and specific heat remain constant assumptions. The calculated experimental values are recomputed from raw data, not copied from rounded report tables.')

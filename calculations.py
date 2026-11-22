import math
COLS=['Hot flow (L/min)','Cold flow (L/min)','Hot inlet (°C)','Hot outlet (°C)','Cold inlet (°C)','Cold outlet (°C)']
PARALLEL=[[.78,1,64.6,55.4,23.4,30.7],[1.6,1,64.7,58.6,23.7,33.5],[2.39,1,65.3,60.6,23.8,35.1],[3.22,1,65.3,61.7,24,36.1],[4.04,1,65.8,62.6,24.2,37],[.8,1.73,63.8,53.5,24.5,29.2],[1.6,1.73,64.5,57.5,24.6,31.2],[2.4,1.73,65.3,59.8,24.9,32.5],[3.23,1.73,65.3,60.9,25.1,33.3],[4.05,1.74,65.7,61.9,25.4,34.1]]
COUNTER=[[.79,.99,61.5,53,23.1,29.3],[1.6,.99,64.5,58.5,23.4,32.5],[2.38,.99,65.3,60.7,23.4,34.2],[3.25,.99,65.3,61.6,23.5,35.1],[4.02,.99,65.7,62.5,23.6,35.8],[.79,1.72,64.5,54.6,23.8,28.2],[1.6,1.72,64.6,57.7,23.9,30.1],[2.4,1.72,64.8,59.5,24,31.1],[3.21,1.72,64.9,60.6,24,31.8],[4,1.73,65.1,61.5,24.3,32.4]]
# Table A-9, saturated liquid water, course formula sheet page 8.
# T (C), dynamic viscosity (mPa s), conductivity (W/m K), Prandtl number.
WATER = [(0.01,1.792,.561,13.5),(5,1.519,.571,11.2),(10,1.307,.580,9.45),(15,1.138,.589,8.09),(20,1.002,.598,7.01),(25,.891,.607,6.14),(30,.798,.615,5.42),(35,.720,.623,4.83),(40,.653,.631,4.32),(45,.596,.637,3.91),(50,.547,.644,3.55),(55,.504,.649,3.25),(60,.467,.654,2.99),(65,.433,.659,2.75),(70,.404,.663,2.55),(75,.378,.667,2.38),(80,.355,.670,2.22),(85,.333,.673,2.08),(90,.310,.675,1.96),(95,.297,.677,1.85),(100,.282,.679,1.75)]
def water_properties(t):
    if not WATER[0][0] <= t <= WATER[-1][0]:
        raise ValueError('Mean water temperature must be between 0.01 and 100 °C for automatic properties.')
    for a,b in zip(WATER,WATER[1:]):
        if a[0]<=t<=b[0]:
            w=(t-a[0])/(b[0]-a[0]); mu,k,pr=[a[i]+w*(b[i]-a[i]) for i in (1,2,3)]
            return mu*1e-3,k,pr

def calculate(row,flow,rho=1000,cp=4180,area=.02,di=.01,do=.012,ds=.02,ks=16,mu_h=.000467,mu_c=.000853,k_h=.654,k_c=.610,pr_h=2.99,auto=True):
    fh,fc,hi,ho,ci,co=map(float,row)
    if not all(math.isfinite(x) for x in [fh,fc,hi,ho,ci,co]) or min(fh,fc,hi-ho,co-ci,hi-ci)<=0: raise ValueError('Check flow rates and temperatures')
    if not 0<di<do<ds: raise ValueError('Diameters must satisfy Di < Do < Ds')
    mh,mc=fh*rho/60000,fc*rho/60000
    ch,cc=mh*cp,mc*cp; cm=min(ch,cc); cr=cm/max(ch,cc)
    qh,qc=ch*(hi-ho),cc*(co-ci); q=min(qh,qc)
    d1,d2=(hi-ci,ho-co) if flow=='Parallel' else (hi-co,ho-ci)
    if min(d1,d2)<=0: raise ValueError('Terminal temperature difference must be positive')
    lm=d1 if abs(d1-d2)<1e-9 else (d1-d2)/math.log(d1/d2)
    u=q/(area*lm); ntu=u*area/cm; eff=100*q/(cm*(hi-ci))
    if auto:
        mu_h,k_h,pr_h=water_properties((hi+ho)/2)
        mu_c,k_c,pr_c=water_properties((ci+co)/2)
    vh=fh/60000/(math.pi*di**2/4); vc=fc/60000/(math.pi*(ds**2-do**2)/4)
    re_h=rho*vh*di/mu_h; re_c=rho*vc*(ds-do)/mu_c
    def nu(re,pr):
        if re<3000:return 4.36
        f=(.79*math.log(re)-1.64)**-2
        return (f/8)*(re-1000)*pr/(1+12.7*math.sqrt(f/8)*(pr**(2/3)-1))
    nh=nu(re_h,pr_h); nc=4.36
    hh=nh*k_h/di; hc=nc*k_c/(ds-do); length=area/(math.pi*do)
    rh=1/(hh*math.pi*di*length); rw=math.log(do/di)/(2*math.pi*ks*length); rc=1/(hc*area)
    ut=1/(area*(rh+rw+rc)); nt=ut*area/cm
    if flow=='Parallel': et=(1-math.exp(-nt*(1+cr)))/(1+cr)
    elif abs(cr-1)<1e-9: et=nt/(1+nt)
    else: et=(1-math.exp(-nt*(1-cr)))/(1-cr*math.exp(-nt*(1-cr)))
    return {'Hot viscosity (Pa s)':mu_h,'Cold viscosity (Pa s)':mu_c,'Hot conductivity (W/m K)':k_h,'Cold conductivity (W/m K)':k_c,'Hot Prandtl':pr_h,'Q hot (W)':qh,'Q cold (W)':qc,'Q (W)':q,'LMTD (K)':lm,'U exp':u,'NTU exp':ntu,'Effectiveness exp (%)':eff,'Heat imbalance (%)':100*abs(qh-qc)/max(qh,qc),'Re hot':re_h,'Re cold':re_c,'Nu hot':nh,'Nu cold':nc,'h hot':hh,'h cold':hc,'R hot (K/W)':rh,'R wall (K/W)':rw,'R cold (K/W)':rc,'U theory':ut,'NTU theory':nt,'Effectiveness theory (%)':100*et,'U difference (%)':100*abs(u-ut)/ut,'NTU difference (%)':100*abs(ntu-nt)/nt,'Effectiveness difference (%)':100*abs(eff-100*et)/(100*et)}

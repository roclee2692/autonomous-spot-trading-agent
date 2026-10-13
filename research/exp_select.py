"""Exp 2: does point-in-time 'recent strength / repair ability' predict FORWARD strategy results?
Each quarter: PIT universe (top-40 by 90d volume, age>=365d). Features use data <= t only.
Outcome: next-365d V2-core log return (daily bars) and next-365d buy&hold."""
import numpy as np, pandas as pd, engine as E, lab, runner as R
from scipy.stats import spearmanr
from concurrent.futures import ProcessPoolExecutor
pd.set_option('display.width',250)
V2P=E.CoreParams(d=(0.07,0.17,0.29), max_gens=3, spike_frac=0.075)
DAY=E.DAY_MS
def feats(sym, t):
    piv=R.universe_panel(); c=piv['close'][sym].loc[:t-1].dropna(); qv=piv['quote_volume'][sym].loc[:t-1].dropna()
    btc=lab.universe_daily(); 
    if len(c)<365: return None
    c365=c.iloc[-365:]; p=c.iloc[-1]
    f={'mom90':p/c.iloc[-90]-1,'mom180':p/c.iloc[-180]-1,'mom365':p/c.iloc[-365]-1,
       'vol90':np.log(c.iloc[-90:]).diff().std()*np.sqrt(365),
       'dd365':1-c365.min()/c365.cummax().max(), 'off_high':1-p/c365.max(), 'off_low':p/c365.min()-1,
       'age':len(c), 'liq':qv.iloc[-90:].mean()}
    # rebound probability: from each local 20% drawdown point, did it rebound +20% within 60d (only completed episodes)
    a=c365.values; hits=tot=0
    for i in range(len(a)-60):
        if a[i] <= 0.8*a[max(0,i-30):i+1].max():
            tot+=1; hits+= a[i+1:i+61].max()>=1.2*a[i]
    f['rebound20']=hits/tot if tot else np.nan
    # trailing strategy fitness (user KPI): cycles and logret of V2 over past 365d
    b=R.symbol_bars(sym, t-365, t, pad=False)
    r=E.run_core(b, V2P); f['cycles365']=r['tp1_count']; f['strat365']=np.log(max(r['equity'][-1],1e-3))
    return f
def fwd(sym,t,H=365):
    b=R.symbol_bars(sym,t,t+H)
    r=E.run_core(b,V2P); bh=E.run_bh(b)
    return {'fwd_strat':np.log(max(r['equity'][-1],1e-3)),'fwd_bh':np.log(max(bh['equity'][-1],1e-3)),
            'fwd_maxdd':lab.metrics(r)['maxdd']}
def job(args):
    sym,t=args
    try:
        f=feats(sym,t)
        if f is None: return None
        f.update(fwd(sym,t)); f['sym']=sym; f['t']=t; return f
    except Exception as e:
        return None
if __name__=='__main__':
    t0=int(pd.Timestamp('2019-07-01').value//10**6//DAY); last=int(R.universe_panel()['close'].index.max())-365
    jobs=[]; t=t0
    while t<=last:
        for s in R.pit_universe(t, top=40, min_age=365): jobs.append((s,t))
        t+=91
    with ProcessPoolExecutor(4) as ex: rows=[x for x in ex.map(job,jobs,chunksize=8) if x]
    df=pd.DataFrame(rows); R.save(df,'select_panel.csv')
    F=['mom90','mom180','mom365','vol90','dd365','off_high','off_low','rebound20','cycles365','strat365','liq','age']
    out=[]
    for f in F:
        ics=[]; ics_bh=[]
        for t,g in df.groupby('t'):
            g=g.dropna(subset=[f])
            if len(g)>10:
                ics.append(spearmanr(g[f],g['fwd_strat']).correlation); ics_bh.append(spearmanr(g[f],g['fwd_bh']).correlation)
        ics=np.array(ics); 
        # non-overlapping subsample (every 4th quarter) for an honest t-stat
        sub=ics[::4]
        out.append((f, round(ics.mean(),3), round((ics>0).mean(),2), round(sub.mean()/ (sub.std(ddof=1)/np.sqrt(len(sub))),2), round(np.mean(ics_bh),3), len(ics)))
    print(pd.DataFrame(out,columns=['feature','IC_mean_fwd_strategy','share_dates_IC>0','t_nonoverlap','IC_mean_fwd_bh','n_dates']).to_string())
    # selection portfolios: top-4 by feature vs universe average vs liquidity top-4
    res=[]
    for f in F+['random']:
        vals=[]
        for t,g in df.groupby('t'):
            if f=='random': pick=g
            else: pick=g.dropna(subset=[f]).nlargest(4,f)
            vals.append((pick.fwd_strat.mean(), pick.fwd_bh.mean(), pick.fwd_maxdd.mean()))
        v=np.array(vals); res.append((f, *np.round(v.mean(0),3), round(np.percentile(v[:,0],10),3)))
    print(pd.DataFrame(res,columns=['top4_by','fwd_strat_logret','fwd_bh_logret','fwd_maxdd','p10_strat']).to_string())

"""Scenario table for V3 on one coin over 365 days: how deep did it go (max generation) and what happened."""
import numpy as np, pandas as pd, engine as E, lab, runner as R
from exp_final import V3P
from concurrent.futures import ProcessPoolExecutor
P=V3P()
def job(a):
    sym,d0,H=a; b=R.symbol_bars(sym,d0,d0+H)
    if b is None: return None
    r=E.run_core(b,P); m=lab.metrics(r,years_override=H/365)
    gens=r['max_gen'] if r['n_buys']>0 else 0
    used=float(np.max(r['pos_cost']/1.0)) if len(r['pos_cost']) else 0
    return {'sym':sym,'d0':d0,'gen':gens if r['n_buys'] else 0,'ret':m['ret'],'worst':m['worst_vs_principal'],'maxdd':m['maxdd'],'bh':b.c[-1]/b.o[0]-1,'maxcost':used}
if __name__=='__main__':
    H=365; d=int(pd.Timestamp('2019-01-01').value//10**6//86400000); last=int(R.universe_panel()['close'].index.max())-H; jobs=[]
    while d<=last:
        jobs+= [(s,d,H) for s in R.pit_universe(d,top=30)]; d+=30
    with ProcessPoolExecutor(2) as ex: rows=[x for x in ex.map(job,jobs,chunksize=16) if x]
    df=pd.DataFrame(rows); R.save(df,'scenario_universe.csv')
    # first-fill only counts gen 1 if any buy; spike-only fills would show gen 1 too (acceptable)
    df['scen']=pd.cut(df.gen,[-1,0,1,2,3],labels=['no fill','gen1 only','reached gen2','reached gen3'])
    t=df.groupby('scen',observed=True).agg(share=('ret',lambda x: len(x)/len(df)),ret_med=('ret','median'),ret_p10=('ret',lambda x:x.quantile(.1)),
        worst_med=('worst','median'),bh_med=('bh','median'),maxcost_med=('maxcost','median'))
    print(t.round(3)); 
    died=df[df.bh<=-0.8]; print('coin -80% or worse in the year: share',round(len(died)/len(df),3),' V3 median',round(died.ret.median(),3),' p10',round(died.ret.quantile(.1),3))

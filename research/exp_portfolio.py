"""Exp 10/13: portfolio-level risk and whether satellites add anything.
(a) PIT universe portfolios (survivorship-free), start every 60d, 540d horizon, daily bars.
(b) The user's actual 8-coin lineup over 2024-12-01..2026-10-11 (1h; HYPE daily): simultaneous
    fills, cash demand if every resting buy filled, crash-day correlation."""
import sys, numpy as np, pandas as pd, engine as E, lab, runner as R
from concurrent.futures import ProcessPoolExecutor
pd.set_option('display.width',250)
K=E.CoreParams(d=(0.07,0.17,0.35), w=(1/3,1/3,1/3), gen_gap=0.20, max_gens=3, spike_frac=0.075, tp2_reanchor=False, tp1_frac=0.75, tp2_frac=0.0, tail_exit=('target',1.0))
V2=E.CoreParams(d=(0.07,0.17,0.29), max_gens=3, spike_frac=0.075)
SAT=E.SatParams(rebuy=(0.09,))
def sub(sym,d0,H,kind):
    b=R.symbol_bars(sym,d0,d0+H)
    if b is None: return None
    r={'K':lambda:E.run_core(b,K),'V2':lambda:E.run_core(b,V2),'S':lambda:E.run_sat(b,SAT),'B':lambda:E.run_bh(b)}[kind]()
    eq=pd.Series(r['equity'],index=r['days']).reindex(range(d0,d0+H)).ffill().bfill()
    pend=pd.Series(r.get('pending',np.zeros(len(r['days']))),index=r['days']).reindex(range(d0,d0+H)).ffill().fillna(0)
    cost=pd.Series(r['pos_cost'],index=r['days']).reindex(range(d0,d0+H)).ffill().fillna(0)
    return eq.values, pend.values, cost.values
PORTS={
 'V2_core4+sat4_S':[(0,4,'V2',0.20),(4,8,'S',0.05)],
 'core4_K':[(0,4,'K',0.25)],
 'core4_V2':[(0,4,'V2',0.25)],
 'core4_K+sat4_S':[(0,4,'K',0.20),(4,8,'S',0.05)],
 'core4_K+sat4_K':[(0,4,'K',0.20),(4,8,'K',0.05)],
 'eq8_K':[(0,8,'K',0.125)], 'eq12_K':[(0,12,'K',1/12)], 'eq2_K':[(0,2,'K',0.5)],
 'core4_bh':[(0,4,'B',0.25)], 'eq8_bh':[(0,8,'B',0.125)],
}
def job(args):
    d0,H=args; uni=R.pit_universe(d0, top=12)
    if len(uni)<12: return []
    cache={}; out=[]
    for name,legs in PORTS.items():
        eq=np.zeros(H); pend=np.zeros(H); cost=np.zeros(H)
        for a,b,kind,w in legs:
            for sym in uni[a:b]:
                key=(sym,kind)
                if key not in cache: cache[key]=sub(sym,d0,H,kind)
                e,p,c=cache[key]; eq+=w*e; pend+=w*p; cost+=w*c
        dd=(1-eq/np.maximum.accumulate(eq)).max()
        out.append({'port':name,'start':d0,'ret':eq[-1]-1,'maxdd':dd,'worst':eq.min()-1,'pend_max':pend.max(),
                    'cost_jump7':np.max(cost[7:]-cost[:-7]) if H>7 else 0})
    return out
if __name__=='__main__':
    H=540; d=int(pd.Timestamp('2019-07-01').value//10**6//E.DAY_MS); last=int(R.universe_panel()['close'].index.max())-H
    jobs=[]
    while d<=last: jobs.append((d,H)); d+=60
    with ProcessPoolExecutor(4) as ex: rows=[x for p in ex.map(job,jobs) for x in p]
    df=pd.DataFrame(rows); R.save(df,'portfolio_universe.csv')
    df['lr']=np.log1p(df.ret)
    print(df.groupby('port').agg(n=('ret','size'),med=('ret','median'),mean=('ret','mean'),lr=('lr','mean'),p10=('ret',lambda x:x.quantile(.1)),
          p05=('ret',lambda x:x.quantile(.05)),dd_med=('maxdd','median'),dd_max=('maxdd','max'),worst=('worst','min'),pend_max=('pend_max','max'),fill7_max=('cost_jump7','max')).round(3).to_string())

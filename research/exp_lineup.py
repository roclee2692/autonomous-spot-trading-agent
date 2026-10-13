"""Exp 10 on the user's actual lineup, 2024-12-01 .. 2026-10-11."""
import numpy as np, pandas as pd, engine as E, lab, runner as R
pd.set_option('display.width',250)
from exp_final import V3P
K=V3P()
d0=int(pd.Timestamp('2024-12-01').value//10**6//E.DAY_MS); d1=int(pd.Timestamp('2026-10-12').value//10**6//E.DAY_MS)
coins=lab.CORE+lab.SAT
W={c:(0.20 if c in lab.CORE else 0.05) for c in coins}
res={}
for c in coins:
    b=lab.slice_days(lab.coin_bars(c,'1d' if c=='HYPE' else '1h'),d0,d1)
    for nm,p in [('V2',E.CoreParams(d=E.V2_CORE.get(c,(0.07,0.17,0.29)),max_gens=3,spike_frac=0.075)),('K',K)]:
        r=E.run_core(b,p)
        res[(c,nm)]=pd.DataFrame({'eq':r['equity'],'pend':r['pending'],'cost':r['pos_cost'],'pos':r['pos_value']},index=r['days'])
    bh=E.run_bh(b); res[(c,'BH')]=pd.DataFrame({'eq':bh['equity']},index=bh['days'])
idx=range(d0,d1)
for nm in ['V2','K','BH']:
    eq=sum(W[c]*res[(c,nm)]['eq'].reindex(idx).ffill().bfill() for c in coins)
    dd=(1-eq/eq.cummax())
    line=f"{nm}: ret {eq.iloc[-1]-1:+.3f} maxDD {dd.max():.3f} worst {eq.min()-1:+.3f}"
    if nm!='BH':
        pend=sum(W[c]*res[(c,nm)]['pend'].reindex(idx).ffill().fillna(0) for c in coins)
        cost=sum(W[c]*res[(c,nm)]['cost'].reindex(idx).ffill().fillna(0) for c in coins)
        pos=sum(W[c]*res[(c,nm)]['pos'].reindex(idx).ffill().fillna(0) for c in coins)
        jump=(cost-cost.shift(7)).max(); jday=(cost-cost.shift(1)).max()
        line+=f" | resting buys max {pend.max():.3f} med {pend.median():.3f} | max 1d new cost {jday:.3f} 7d {jump:.3f} | coin exposure med {(pos/eq).median():.2f} max {(pos/eq).max():.2f}"
    print(line)
# crash correlation
rets=pd.DataFrame({c: lab.coin_frame(c,'1d').assign(day=lambda f:f.open_time_ms//86400000).set_index('day').close.pct_change() for c in coins+['BTC']}).loc[d0:d1]
crash=rets['BTC']<-0.05
print('avg pairwise corr normal days', round(rets[~crash][coins].corr().values[np.triu_indices(8,1)].mean(),2), 'BTC<-5% days', round(rets[crash][coins].corr().values[np.triu_indices(8,1)].mean(),2), 'n crash days', int(crash.sum()))
print('mean coin return on BTC<-5% days', rets[crash][coins].mean().round(3).to_dict())

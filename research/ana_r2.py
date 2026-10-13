"""Round-2 scoring: per-coin AND portfolio (equal-weight basket) metrics for every variant vs V3,
by sample, horizon, IS/OOS, and (universe) liquidity-rank bucket. Usage: python3 ana_r2.py > results/r2_scores.txt"""
import numpy as np, pandas as pd, runner as R
from functools import lru_cache
pd.set_option('display.width',280); pd.set_option('display.max_rows',400); pd.set_option('display.max_columns',40)
IS_END=R.IS_END_DAY
def lr(x): return np.log1p(np.clip(x,-0.99,None))
def focus_scores(H):
    df=pd.read_csv(f'results/sens_focus_H{H}.csv'); df['lr']=lr(df.ret)
    def agg(g):
        per=g.groupby('coin').agg(lr=('lr','mean'),med=('ret','median'),dd=('maxdd','median'))
        w=1/g.groupby('coin').coin.transform('size')
        p10=R._wq(g.ret.values,w.values,0.10)
        return pd.Series({'lr':per.lr.mean(),'med':per.med.mean(),'p10':p10,'dd':per.dd.mean()})
    out={}
    for tag,sub in [('all',df),('IS',df[df.start_day+H<=IS_END]),('OOS',df[df.start_day>=IS_END])]:
        if len(sub)==0: continue
        out[tag]=sub.groupby('variant').apply(agg,include_groups=False)
    t=pd.concat(out,axis=1)
    return t
@lru_cache(maxsize=None)
def rank_of(d0):
    return {s:i for i,s in enumerate(R.pit_universe(d0, top=30))}
def universe_scores(H):
    df=pd.read_csv(f'results/sens_universe_H{H}.csv'); df['lr']=lr(df.ret)
    df['rank']=[rank_of(int(d)).get(s,99) for s,d in zip(df.symbol,df.start_day)]
    rows={}
    for v,g in df.groupby('variant'):
        r={'coin_lr':g.lr.mean(),'coin_p10':g.ret.quantile(.1),'coin_dd':g.maxdd.median()}
        for b,(a,z) in {'top8':(0,8),'r9_30':(8,30),'all30':(0,30)}.items():
            gb=g[(g['rank']>=a)&(g['rank']<z)].groupby('start_day').ret.mean()
            r[f'{b}_lr']=lr(gb).mean(); r[f'{b}_p10']=gb.quantile(.1); r[f'{b}_med']=gb.median()
        gi=g[g.start_day+H<=IS_END]; go=g[g.start_day>=IS_END]
        r['IS_coin_lr']=gi.lr.mean() if len(gi) else np.nan; r['OOS_coin_lr']=go.lr.mean() if len(go) else np.nan
        bi=gi.groupby('start_day').ret.mean(); bo=go.groupby('start_day').ret.mean()
        r['IS_all30_lr']=lr(bi).mean() if len(bi) else np.nan; r['OOS_all30_lr']=lr(bo).mean() if len(bo) else np.nan
        rows[v]=r
    return pd.DataFrame(rows).T
if __name__=='__main__':
    for H in [540,1095]:
        try:
            f=focus_scores(H); base=f.loc['V3']
            print(f'\n######## FOCUS H={H}  (absolute for V3; others = minus V3)')
            d=f.sub(base,axis=1); d.loc['V3']=base
            print(d.round(3).to_string())
        except FileNotFoundError: pass
        try:
            u=universe_scores(H); base=u.loc['V3']
            print(f'\n######## UNIVERSE H={H}  (absolute for V3; others = minus V3)')
            d=u.sub(base,axis=1); d.loc['V3']=base
            print(d.round(3).to_string())
        except FileNotFoundError: pass

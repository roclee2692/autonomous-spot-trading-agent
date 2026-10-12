"""Expanding-window walk-forward on the PIT universe (daily, 365d windows, monthly starts).
Each test year Y: choose the config with best mean logret among windows that ENDED before Y;
evaluate it on windows starting in Y. Compare with fixed V3 and fixed V2."""
import itertools, numpy as np, pandas as pd, engine as E, runner as R
pd.set_option('display.width',220)
def cfg(d3,gap,struct):
    kw=dict(d=(0.07,0.17,d3), gen_gap=gap, max_gens=3, spike_frac=0.075)
    if struct=='v3': kw.update(w=(1/3,1/3,1/3), tp2_reanchor=False, tp1_frac=0.75, tp2_frac=0.0, tail_exit=('target',1.0))
    return ('core', E.CoreParams(**kw))
SPECS={f'{d3}|{gap}|{s}':cfg(d3,gap,s) for d3,gap,s in itertools.product([0.29,0.35,0.40],[0.0,0.1,0.2,0.3],['v2','v3'])}
if __name__=='__main__':
    df=R.universe_grid(SPECS, horizon=365, step=30, top=30, workers=2); R.save(df,'wf_universe.csv')
    df['lr']=np.log1p(df.ret.clip(lower=-0.99)); df['year']=pd.to_datetime(df.start_day*86400000,unit='ms').dt.year
    rows=[]
    for Y in range(2021,2026):
        y0=int(pd.Timestamp(f'{Y}-01-01').value//10**6//86400000)
        train=df[df.start_day+365<=y0]; test=df[df.year==Y]
        best=train.groupby('variant').lr.mean().idxmax()
        te=test.groupby('variant').agg(lr=('lr','mean'),p10=('ret',lambda x:x.quantile(.1)))
        rows.append({'year':Y,'chosen':best,'WF_lr':te.loc[best,'lr'],'V3_lr':te.loc['0.35|0.2|v3','lr'],'V2_lr':te.loc['0.29|0.0|v2','lr'],
                     'WF_p10':te.loc[best,'p10'],'V3_p10':te.loc['0.35|0.2|v3','p10'],'V2_p10':te.loc['0.29|0.0|v2','p10'],
                     'test_best':te.lr.idxmax(),'rank_V3':int(te.lr.rank(ascending=False)['0.35|0.2|v3']),'n_cfg':len(te)})
    r=pd.DataFrame(rows); print(r.round(3).to_string()); print(r[['WF_lr','V3_lr','V2_lr','WF_p10','V3_p10','V2_p10']].mean().round(3))
    # structure effect alone, every year
    df['struct']=df.variant.str.split('|').str[2]
    print(df.groupby(['year','struct']).lr.mean().unstack().round(3))

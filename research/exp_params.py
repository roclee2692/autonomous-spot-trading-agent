"""Exp 1: uniform vs group vs per-coin ladder parameters, IS (<2024) vs OOS (>=2024)."""
import itertools, sys, numpy as np, pandas as pd
import engine as E, lab, runner as R
pd.set_option('display.width',250)

D1=[0.05,0.07,0.10]; D2=[0.12,0.15,0.18,0.22]; D3=[0.25,0.30,0.35,0.40]
TEMPL=[(a,b,c) for a,b,c in itertools.product(D1,D2,D3) if a<b<c]
def spec(d): return ('core', E.CoreParams(d=d, max_gens=3, spike_frac=0.0))
VARS={f"{d[0]:.2f}/{d[1]:.2f}/{d[2]:.2f}": spec(d) for d in TEMPL}
V2LAB='V2'
COINS=lab.CORE+lab.SAT+['UNI']
if __name__=='__main__':
    H=365
    split=R.IS_END_DAY
    out=[]
    for per,(a,b) in {'IS':(None,split),'OOS':(split,None)}.items():
        df=R.grid(COINS, VARS, horizon=H, step=30, d_from=a, d_to=b)
        df['period']=per
        # V2 per-coin params
        v2=R.grid([c for c in COINS if c in E.V2_CORE], {V2LAB: lambda c: spec(E.V2_CORE[c])}, horizon=H, step=30, d_from=a, d_to=b)
        v2['period']=per
        out += [df, v2]
    df=pd.concat(out, ignore_index=True)
    df['logret']=np.log1p(df['ret'].clip(lower=-0.99))
    R.save(df,'params_grid.csv')
    print(df.groupby(['period','coin']).start_day.nunique().unstack(0))

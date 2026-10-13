"""Execution-realism checks: daily vs 1h bars; spike order with wicks clipped; fees/penetration."""
import numpy as np, pandas as pd, engine as E, lab, runner as R
pd.set_option('display.width',250)
def V(**kw):
    def f(coin):
        base=dict(d=E.V2_CORE.get(coin,(0.07,0.17,0.29)), max_gens=3, spike_frac=0.075); base.update(kw)
        return ('core', E.CoreParams(**base))
    return f
coins=['TAO','AAVE','LINK','NEAR','ZRO','PENDLE','RENDER','UNI']
out=[]
for iv in ['1h','1d']:
    df=R.grid(coins, {'V2':V(),'noSpike':V(spike_frac=0.0),'sat':lambda c:('sat',E.SatParams(rebuy=(E.V2_SAT_REBUY.get(c,0.08),)))}, horizon=540, step=30, interval=iv)
    df['iv']=iv; out.append(df)
df=pd.concat(out)
t=R.table(df, by=('iv','variant'))
print(t[['iv','variant','ret_med','logret','p10','cycles_py','trades_py','util']].round(3).to_string())
# wick clipping: rebuild bars with lows clipped to 0.5*min(open,close) per 1h bar (removes extreme flash prints)
import engine
def clipped(coin):
    b=R._bars(coin,'1h'); lo=np.maximum(b.l, 0.75*np.minimum(b.o,b.c))
    return engine.Bars(b.t,b.o,b.h,lo,b.c,b.day_end,coin)
rows=[]
for coin in coins:
    for clip in [False, True]:
        b=clipped(coin) if clip else R._bars(coin,'1h')
        for name,spec in {'V2':V()(coin),'noSpike':V(spike_frac=0.0)(coin)}.items():
            d=lab.rolling(b, lambda x: R.run_strategy(x,spec), 540, 30); d['coin']=coin; d['clip']=clip; d['variant']=name; rows.append(d)
d=pd.concat(rows)
print(d.groupby(['clip','variant']).agg(ret_med=('ret','median'),lr=('ret',lambda x: np.log1p(x).mean())).round(3))
print(d.groupby(['coin','clip','variant']).ret.apply(lambda x: np.log1p(x).mean()).unstack([1,2]).round(3))
# fee & penetration sensitivity
rows=[]
for fee,pen in [(0.0,0.0),(0.001,0.0005),(0.001,0.002),(0.002,0.002)]:
    df=R.grid(coins, {'V2':V(fee=fee,pen=pen)}, horizon=540, step=30); s=R.table(df).iloc[0]
    rows.append((fee,pen,round(s.ret_med,3),round(s.logret,3),round(s.p10,3),round(s.fees,4)))
print(pd.DataFrame(rows,columns=['fee','pen','ret_med','logret','p10','fees_paid']))

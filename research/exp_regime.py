"""Exp 7: performance by (ex-post) market regime of the coin inside each window. The regime label
is only used to slice results, never to trade."""
import sys, numpy as np, pandas as pd, lab, runner as R
pd.set_option('display.width',250)
def label(sym_or_coin, d0, H, universe):
    if universe:
        c=R.universe_panel()['close'][sym_or_coin].loc[d0:d0+H-1].dropna()
    else:
        f=lab.coin_frame(sym_or_coin,'1d'); f=f.assign(day=f.open_time_ms//86400000).set_index('day').close
        c=f.loc[d0:d0+H-1]
    if len(c)<30: return 'na'
    ret=c.iloc[-1]/c.iloc[0]-1; dd=(1-c/c.cummax()).max(); vol=np.log(c).diff().std()*np.sqrt(365)
    if ret>=1.0: return '1 strong_up'
    if ret>=0.2: return '2 slow_up'
    if ret<=-0.6: return '6 crash'
    if ret<=-0.2: return '5 slow_bear'
    if dd>=0.5: return '7 V_rebound'
    return '3 range_hivol' if vol>=1.0 else '4 range_lovol'
def run(path, universe, variants):
    df=pd.read_csv(path); df=df[df.variant.isin(variants)]
    key='symbol' if universe else 'coin'
    labs={(k,s):label(k,s,540,universe) for k,s in df[[key,'start_day']].drop_duplicates().itertuples(index=False)}
    df['regime']=[labs[(k,s)] for k,s in zip(df[key],df.start_day)]
    df['lr']=np.log1p(df.ret.clip(lower=-0.99))
    t=df.groupby(['regime','variant']).agg(n=('lr','size'),med=('ret','median'),lr=('lr','mean'),p10=('ret',lambda x:x.quantile(.1)),dd=('maxdd','median')).unstack('variant')
    return t
if __name__=='__main__':
    print('FOCUS (1h):'); print(run('results/rules_H540_all.csv', False, sys.argv[1].split(',')).round(2).to_string())

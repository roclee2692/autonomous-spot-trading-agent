"""Exp 9 (+4H): can simple price rules spot 'slow death' early enough to stop averaging down?
Universe (PIT top-30, daily, 540d windows). Halt = no new generation/cycle while the signal is on;
pause = also cancel unfilled buys. Evaluated separately on windows where the coin later 'died'
(window B&H <= -80%) and on the rest (cost of false alarms)."""
import numpy as np, pandas as pd, engine as E, lab, runner as R
pd.set_option('display.width',250)
K=E.CoreParams(d=(0.07,0.17,0.35), w=(1/3,1/3,1/3), gen_gap=0.20, max_gens=3, spike_frac=0.075, tp2_reanchor=False, tp1_frac=0.75, tp2_frac=0.0, tail_exit=('target',1.0))
SPECS={'K':('core',K),'bh':('bh',)}
for rule in ['relweak','relweak2','idio_low','deep85','btc_bear','btc_crash']:
    SPECS[f'K_halt_{rule}']=('core_halt',K,rule,'halt')
for rule in ['relweak','idio_low']:
    SPECS[f'K_pause_{rule}']=('core_halt',K,rule,'pause')
if __name__=='__main__':
    df=R.universe_grid(SPECS, horizon=540, step=60, top=30, workers=2); R.save(df,'death_universe.csv')
    bh=df[df.variant=='bh'][['symbol','start_day','ret']].rename(columns={'ret':'bh'})
    df=df.merge(bh,on=['symbol','start_day'])
    df['class']=np.where(df.bh<=-0.8,'died(<=-80%)',np.where(df.bh<=-0.5,'bad(-50..-80%)','ok(>-50%)'))
    df['lr']=np.log1p(df.ret.clip(lower=-0.99))
    g=df.groupby(['variant','class']).agg(n=('lr','size'),logret=('lr','mean'),ret_med=('ret','median'),p10=('ret',lambda x:x.quantile(.1))).unstack('class')
    print(g.round(3).to_string())
    print(df.groupby('variant').agg(logret=('lr','mean'),p10=('ret',lambda x:x.quantile(.1)),med=('ret','median')).round(3))

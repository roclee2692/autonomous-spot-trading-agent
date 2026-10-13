"""Is a simple market filter worth adding? 'BTC below its 200d MA -> open no new generation / cycle'
(halt) and the stronger 'also cancel unfilled buys' (pause). IS vs OOS, focus and universe."""
import sys, numpy as np, pandas as pd, engine as E, lab, runner as R
from exp_final import V3P
pd.set_option('display.width',240)
SPECS={'V3':('core',V3P()),'V3+btc200_halt':('core_halt',V3P(),'btc_bear','halt'),'V3+btc200_pause':('core_halt',V3P(),'btc_bear','pause'),
       'V3+btc-35%_halt':('core_halt',V3P(),'btc_crash','halt'),'bh':('bh',)}
if __name__=='__main__':
    which=sys.argv[1]
    if which=='universe':
        for H in [365,540]:
            df=R.universe_grid(SPECS, horizon=H, step=30, top=30, workers=2); R.save(df,f'btcfilter_universe_H{H}.csv')
            df['lr']=np.log1p(df.ret.clip(lower=-0.99)); df['yr']=pd.to_datetime(df.start_day*86400000,unit='ms').dt.year
            print(f'== universe H={H}'); print(R.utable(df)[['n','ret_med','logret','p10','maxdd_med','util','basket_med','basket_p10']].round(3))
            df['period']=np.where(df.start_day+H<=R.IS_END_DAY,'IS',np.where(df.start_day>=R.IS_END_DAY,'OOS','straddle'))
            print(df.groupby(['period','variant']).agg(lr=('lr','mean'),p10=('ret',lambda x:x.quantile(.1)),med=('ret','median')).unstack(0).round(3))
            print(df.groupby(['yr','variant']).lr.mean().unstack().round(3))
    else:
        for tag,kw in [('ALL',{}),('IS',dict(d_to=R.IS_END_DAY)),('OOS',dict(d_from=R.IS_END_DAY))]:
            df=R.grid(lab.CORE+lab.SAT+['UNI'], SPECS, horizon=365, step=30, workers=2, **kw)
            print(f'== focus {tag} H=365'); print(R.table(df)[['variant','n','ret_med','logret','p10','maxdd_med','util','cycles_py']].round(3).to_string())

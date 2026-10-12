"""Tail exit driven by a simple bull/bear identifier (user request): hold the tail in bull,
sell it when bear. Signals are price-only and known at the daily close; the tail sells at the
next bar's open. Two forms per signal:  R  = hold until bear (no target);
T+R = sell at 2xC or when bear, whichever first. Baselines: V3 (2xC), permanent, trail, no tail."""
import sys, numpy as np, pandas as pd, engine as E, lab, runner as R
from exp_final import V3P, v2spec
pd.set_option('display.width',260); pd.set_option('display.max_rows',200)
SIGNALS=['btc_ma100','btc_ma150','btc_ma200','btc_ma300','btc_ma350','btc_ma200_h5','btc_mom365','btc_dd30',
         'btc_cross','coin_ma200','coin_mom365','both_ma200']
SPECS={'V3 (2xC)':('core',V3P()), 'V3 tail permanent':('core',V3P(tail_exit=('none',))),
       'V3 tail trail50/30':('core',V3P(tail_exit=('trail',0.5,0.30))), 'V3 no tail':('core',V3P(tp1_frac=1.0)),
       'V2':v2spec, 'bh':('bh',)}
for s in SIGNALS:
    SPECS[f'R:{s}']=('core_regime',V3P(tail_exit=('regime',)),s)
    SPECS[f'T+R:{s}']=('core_regime',V3P(tail_exit=('target_or_regime',1.0)),s)
SPECS['Rcost:btc_ma200']=('core_regime',V3P(tail_exit=('regime_above_cost',)),'btc_ma200')
SPECS['T+Rcost:btc_ma200']=('core_regime',V3P(tail_exit=('target_or_regime_above_cost',1.0)),'btc_ma200')
COLS=['variant','n','ret_med','ret_mean','logret','alpha','p10','p05','maxdd_med','util','trades_py']
if __name__=='__main__':
    which=sys.argv[1]
    if which=='focus':
        for H in [365,540,1095]:
            df=R.grid(lab.CORE+lab.SAT+['UNI'], SPECS, horizon=H, step=30, workers=4)
            R.save(df,f'tailregime_focus_H{H}.csv')
            print(f'=== FOCUS H={H}'); print(R.table(df)[COLS].sort_values('logret',ascending=False).round(3).to_string(), flush=True)
    else:
        sp={k:(v('X') if callable(v) else v) for k,v in SPECS.items()}
        for H in [540,1095]:
            df=R.universe_grid(sp, horizon=H, step=60, top=30, workers=4); R.save(df,f'tailregime_universe_H{H}.csv')
            print(f'=== UNIVERSE H={H}'); print(R.utable(df).reset_index()[COLS+['basket_med','basket_p10']].sort_values('logret',ascending=False).round(3).to_string(), flush=True)

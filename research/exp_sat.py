"""Satellite rules: V2 (sell 75% at +20%, rebuy one tier at -d, batches sell 100% at +20%, tail 25%)
vs rebuy structures, sell levels, tail sizes; and vs the core ladder applied to the same coins."""
import sys, numpy as np, pandas as pd
import engine as E, lab, runner as R
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
def S(**kw): return ('sat', E.SatParams(**kw))
SPECS={'S_v2': lambda c: S(rebuy=(E.V2_SAT_REBUY.get(c,0.08),)), 'bh': ('bh',)}
for d in [0.05,0.07,0.09,0.12,0.15,0.20]: SPECS[f'S_r{int(d*100)}']=S(rebuy=(d,))
for a,b in [(0.07,0.15),(0.09,0.18),(0.10,0.20),(0.09,0.21),(0.10,0.25),(0.12,0.25)]:
    SPECS[f'S_r{int(a*100)}_{int(b*100)}']=S(rebuy=(a,b), rebuy_w=(0.5,0.5))
SPECS['S_r7_15_25']=S(rebuy=(0.07,0.15,0.25), rebuy_w=(1/3,1/3,1/3))
for x in [0.15,0.25,0.30]: SPECS[f'S_sell{int(x*100)}']=S(sell=x, rebuy=(0.09,))
SPECS['S_tail0']=S(sell_frac0=1.0, rebuy=(0.09,)); SPECS['S_tail50']=S(sell_frac0=0.5, rebuy=(0.09,))
SPECS['S_tail_t100']=S(rebuy=(0.09,), tail_exit=('target',1.0))
SPECS['S_r9_tail_t100_sell25']=S(sell=0.25, rebuy=(0.09,), tail_exit=('target',1.0))
SPECS['S_r10_20_tail_t100']=S(rebuy=(0.10,0.20), rebuy_w=(0.5,0.5), tail_exit=('target',1.0))
SPECS['K3_core']=('core', E.CoreParams(d=(0.07,0.17,0.35), w=(1/3,1/3,1/3), gen_gap=0.2, max_gens=3, spike_frac=0.075, tp2_reanchor=False, tp1_frac=0.75, tp2_frac=0.0, tail_exit=('target',1.0)))
SPECS['K_core']=('core', E.CoreParams(d=(0.07,0.17,0.35), w=(1/3,1/3,1/3), gen_gap=0.2, max_gens=3, spike_frac=0.075, tp2_reanchor=False, tail_exit=('target',1.0)))
SPECS['K_core_allin1gen']=('core', E.CoreParams(d=(0.07,0.17,0.35), w=(1/3,1/3,1/3), max_gens=1, budget_units=1, tp2_reanchor=False, tail_exit=('target',1.0)))
COLS=['variant','n','ret_med','ret_mean','logret','p10','p05','maxdd_med','under_avg','util','trades_py','cycles_py']
if __name__=='__main__':
    which=sys.argv[1]
    if which=='focus':
        df=R.grid(lab.SAT+['UNI','ONDO'], SPECS, horizon=540 if len(sys.argv)<3 else int(sys.argv[2]), step=30, workers=2); R.save(df,'sat_focus.csv'); t=R.table(df)
        print(t[COLS].round(3).to_string())
        t2=R.table(df,by=('coin','variant'),coin_equal=False)
        print(t2[t2.variant.isin(['S_v2','S_r9','S_r10_20','bh','K_core'])][['coin','variant','n','ret_med','logret','p10','maxdd_med','cycles_py']].round(3).to_string())
    else:
        sp={k:(v('X') if callable(v) else v) for k,v in SPECS.items()}
        df=R.universe_grid(sp, horizon=540, step=60, top=30, workers=2); R.save(df,'sat_universe.csv'); t=R.utable(df).reset_index()
        print(t[COLS+['basket_med','basket_p10']].round(3).to_string())

import sys, numpy as np, pandas as pd
import engine as E, lab, runner as R
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)

def v2(coin, **kw):
    base = dict(d=E.V2_CORE.get(coin,(0.07,0.17,0.29)), max_gens=3, spike_frac=0.075)
    base.update(kw)
    return ('core', E.CoreParams(**base))

VARIANTS = {
 'A_v2': lambda c: v2(c),
 'B_bh': ('bh',),
 'C_simple': ('core', E.CoreParams(d=(0.07,0.17,0.29), tp1=0.25, tp1_frac=1.0, tp2_frac=0.0, max_gens=1, budget_units=1, tp2_reanchor=False)),
 'C_simple_3u': ('core', E.CoreParams(d=(0.07,0.17,0.29), tp1=0.25, tp1_frac=1.0, tp2_frac=0.0, max_gens=1, budget_units=3, tp2_reanchor=False)),
 'D_cash': ('cash',),
 'E_v2lite': lambda c: v2(c, max_gens=1, budget_units=3, tp2_frac=0.0, tp1_frac=0.75, spike_frac=0.0),
 'A_v2_allin': lambda c: v2(c, budget_units=1, max_gens=1, spike_frac=0.0),
 'mix33': ('mix', 0.33), 'mix50': ('mix',0.5),
}
if __name__ == '__main__':
    H = int(sys.argv[1]) if len(sys.argv)>1 else 540
    coins = lab.CORE + lab.SAT + ['UNI']
    df = R.grid(coins, VARIANTS, horizon=H, step=30)
    R.save(df, f'base_H{H}.csv')
    t = R.table(df)
    cols=['variant','n','ret_med','ret_mean','p10','p05','maxdd_med','maxdd_p90','deep30','under_max','util','trades_py','cycles_py']
    print('POOLED (coin-equal):'); print(t[cols].round(3).to_string())
    t2 = R.table(df, by=('coin','variant'), coin_equal=False)
    print(t2[['coin','variant','n','ret_med','p10','maxdd_med','util','cycles_py']].round(3).to_string())

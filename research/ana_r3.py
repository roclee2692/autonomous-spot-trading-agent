"""Round 3 summaries for the long-horizon runs (cohorts, 5y and 7y windows)."""
import sys
import numpy as np
import pandas as pd
from exp_r3_long import basket, MAJORS
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)


def coin_table(df):
    a = df[~df.sym.isin(MAJORS)].copy()
    bh = a[a.strat == 'bh'].set_index(['tag', 'd0', 'sym']).ret_B.rename('bhB')
    a = a.join(bh, on=['tag', 'd0', 'sym'])
    a['lrB'] = np.log1p(a.ret_B.clip(lower=-.99)); a['lrP'] = np.log1p(a.ret_P.clip(lower=-.99))
    a['lrS'] = np.log1p(a.shadow_ret.clip(lower=-.99))
    a['winB'] = a.ret_B > a.bhB; a['winS'] = a.ret_P > a.shadow_ret
    return a.groupby('strat').agg(n=('ret_B', 'size'), medB=('ret_B', 'median'), lrB=('lrB', 'mean'),
                                  p10B=('ret_B', lambda x: x.quantile(.1)), medP=('ret_P', 'median'), lrP=('lrP', 'mean'),
                                  med_shadow=('shadow_ret', 'median'), lr_shadow=('lrS', 'mean'), win_bh=('winB', 'mean'),
                                  win_shadow=('winS', 'mean'), irr_med=('irr', 'median'), sh_irr=('shadow_irr', 'median'),
                                  dd_med=('maxdd', 'median'), P_med=('P', 'median'), util=('util', 'mean'))


def basket_table(df):
    a = df[~df.sym.isin(MAJORS)]
    bk = a.groupby(['tag', 'd0', 'strat']).apply(basket, include_groups=False).reset_index()
    bk['lr_bk'] = np.log1p(bk.ret_B.clip(lower=-.99))
    return bk, bk.groupby('strat').agg(n=('ret_B', 'size'), mean_bk=('ret_B', 'mean'), med_bk=('ret_B', 'median'),
                                       lr_bk=('lr_bk', 'mean'), p10_bk=('ret_B', lambda x: x.quantile(.1)),
                                       dd_bk=('maxdd', 'median'), retP_bk=('ret_P', 'median'), shadowP_bk=('shadow_P', 'median'))


def majors_table(df):
    m = df[df.sym.isin(MAJORS)]
    return m.groupby(['sym', 'strat']).agg(n=('ret_B', 'size'), medB=('ret_B', 'median'), medP=('ret_P', 'median'),
                                           med_shadow=('shadow_ret', 'median'), irr=('irr', 'median'),
                                           sh_irr=('shadow_irr', 'median'), dd=('maxdd', 'median'))


if __name__ == '__main__':
    for f in sys.argv[1:]:
        df = pd.read_pickle(f)
        print(f'\n################ {f}  (alts: per coin-window)')
        print(coin_table(df).round(3).to_string())
        bk, t = basket_table(df)
        print('-- equal-budget baskets of the PIT top-30 (one per start date)')
        print(t.round(3).to_string())
        print('-- BTC / ETH')
        print(majors_table(df).round(2).to_string())

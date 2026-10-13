"""Tail share x tail target grid: score every cell against V3.1 (s25x2) on every horizon."""
import sys
import numpy as np
import pandas as pd
from exp_r3_long import MAJORS
pd.set_option('display.width', 260); pd.set_option('display.max_rows', 400)
CUT = int(pd.Timestamp('2022-01-01').value // 10**9 // 86400)


def cell_stats(H, prefix='g2'):
    df = pd.read_pickle(f'results/r3_{prefix}_{H}.pkl'); bk = pd.read_pickle(f'results/r3_{prefix}bk_{H}.pkl')
    a = df[~df.sym.isin(MAJORS)].copy(); a['lr'] = np.log1p(a.ret_B.clip(lower=-.99))
    t = a.groupby('strat').agg(med=('ret_B', 'median'), lr=('lr', 'mean'), p10=('ret_B', lambda x: x.quantile(.1)), dd=('maxdd', 'median'))
    bk['lr'] = np.log1p(bk.ret_B.clip(lower=-.99))
    tb = bk.groupby('strat').agg(bk_lr=('lr', 'mean'), bk_p10=('ret_B', lambda x: x.quantile(.1)), bk_dd=('maxdd', 'median'))
    tb['bk_lr_late'] = bk[bk.d0 >= CUT].groupby('strat').lr.mean()
    m = df[df.sym.isin(MAJORS)].copy(); m['lr'] = np.log1p(m.ret_B.clip(lower=-.99))
    tb['maj_lr'] = m.groupby('strat').lr.mean()
    return t.join(tb)


if __name__ == '__main__':
    base = 's25x2'
    allh = {}
    for H in [540, 1095, 1825, 2555]:
        s = cell_stats(H)
        d = s - s.loc[base]
        allh[H] = d
        print(f'\n===== H={H}: absolute for base, then differences vs {base}')
        print(s.loc[[base, 'bh']].round(3).to_string())
        print(d.drop(index='bh').sort_values('bk_lr', ascending=False).round(3).to_string())
    # cells that never lose on per-coin lr/p10 or basket lr/p10 by more than tolerance and gain on long baskets
    rows = []
    for c in allh[540].index:
        if c == 'bh':
            continue
        r = {'cell': c}
        for H, d in allh.items():
            for k in ('lr', 'p10', 'bk_lr', 'bk_p10', 'dd', 'bk_dd'):
                r[f'{k}_{H}'] = d.loc[c, k]
        rows.append(r)
    R = pd.DataFrame(rows).set_index('cell')
    R['worst_lr'] = R[[f'lr_{H}' for H in allh]].min(1)
    R['worst_p10'] = R[[f'p10_{H}' for H in allh]].min(1)
    R['worst_bk_lr'] = R[[f'bk_lr_{H}' for H in allh]].min(1)
    R['worst_bk_p10'] = R[[f'bk_p10_{H}' for H in allh]].min(1)
    R['max_dd_up'] = R[[f'dd_{H}' for H in allh] + [f'bk_dd_{H}' for H in allh]].max(1)
    R['sum_bk_lr'] = R[[f'bk_lr_{H}' for H in allh]].sum(1)
    print('\n===== ROBUSTNESS SCORE (differences vs V3.1 across all 4 horizons)')
    print(R[['worst_lr', 'worst_p10', 'worst_bk_lr', 'worst_bk_p10', 'max_dd_up', 'sum_bk_lr']].sort_values('sum_bk_lr', ascending=False).round(3).to_string())

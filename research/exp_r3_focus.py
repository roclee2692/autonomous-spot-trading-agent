"""Round 3: tail share / target candidates on the focus coins with 1h bars
(rolling 540 / 1095 days, step 30) and full history, plus the 10-year external
series and the Bitfinex 2017 cohort."""
import sys
import numpy as np
import pandas as pd
import engine as E
import lab
import runner as R
import principal as PR
from exp_final import V31P

pd.set_option('display.width', 260); pd.set_option('display.max_rows', 300)
CAND = {
    'V3.1 (25%@2x)': ('core', V31P()),
    '10%@4x': ('core', V31P(tp1_frac=0.90, tail_exit=('target', 3.0))),
    '10%@5x': ('core', V31P(tp1_frac=0.90, tail_exit=('target', 4.0))),
    '15%@4x': ('core', V31P(tp1_frac=0.85, tail_exit=('target', 3.0))),
    '15%@5x': ('core', V31P(tp1_frac=0.85, tail_exit=('target', 4.0))),
    '10%@3x': ('core', V31P(tp1_frac=0.90, tail_exit=('target', 2.0))),
    'no tail': ('core', V31P(tp1_frac=1.0)),
    'bh': ('bh',),
}
COINS = lab.CORE + lab.SAT + ['UNI']

if __name__ == '__main__':
    part = sys.argv[1]
    if part == 'windows':
        for H in (540, 1095):
            df = R.grid(COINS, CAND, horizon=H, step=30)
            df.to_pickle(f'results/r3_focus_{H}.pkl')
            t = R.table(df)
            df['lr'] = np.log1p(df.ret.clip(lower=-.99))
            t = t.set_index('variant')
            t['lr'] = df.groupby('variant').lr.mean()
            late = df[df.start_day >= R.IS_END_DAY].groupby('variant').lr.mean() if 'start_day' in df else None
            if late is not None:
                t['lr_oos2024'] = late
            print(f'\n=== FOCUS COINS 1h, H={H}')
            cols = [c for c in ['n', 'ret_med', 'lr', 'lr_oos2024', 'p10', 'p05', 'maxdd_med', 'maxdd_p90', 'util', 'trades_py'] if c in t]
            print(t[cols].round(3).to_string())
            per = df.pivot_table(index='coin', columns='variant', values='lr')
            print(per.round(3).to_string())
    elif part == 'full':
        rows = []
        for c in COINS:
            b = R._bars(c, '1d' if c == 'HYPE' else '1h')
            for n, sp in CAND.items():
                r = R.run_strategy(b, sp)
                st = PR.principal_stats(r, b)
                eq = r['equity']
                st.update(coin=c, variant=n, final=eq[-1], maxdd=(1 - eq / np.maximum.accumulate(eq)).max())
                rows.append(st)
        f = pd.DataFrame(rows)
        print('=== FULL HISTORY (focus coins, 1h): final multiple of budget')
        print(f.pivot_table(index='coin', columns='variant', values='final').round(2).to_string())
        print(f.pivot_table(index='coin', columns='variant', values='maxdd').round(2).to_string())
        print('mean log final:', f.assign(l=np.log(f.final)).groupby('variant').l.mean().round(3).to_dict())

"""Round 2: one-at-a-time sensitivity of every V3 parameter + alternative structures.
Goal: try to overturn V3. A change is only interesting if it beats V3 on BOTH samples, several horizons,
in and out of sample. Focus coins (1h; HYPE daily) and PIT universe (daily)."""
import sys, numpy as np, pandas as pd, engine as E, lab, runner as R
from exp_final import V3P, v2spec
pd.set_option('display.width',260); pd.set_option('display.max_rows',300)
S={'V3':('core',V3P()),'V2':v2spec,'bh':('bh',)}
def add(name, **kw): S[name]=('core',V3P(**kw))
for x in [0.04,0.05,0.10,0.12]: add(f'd1={x}', d=(x,0.17,0.35))
for x in [0.12,0.14,0.20,0.25]: add(f'd2={x}', d=(0.07,x,0.35))
for x in [0.25,0.29,0.30,0.40,0.45,0.50]: add(f'd3={x}', d=(0.07,0.17,x))
for x in [0.0,0.05,0.10,0.15,0.25,0.30,0.40]: add(f'gap={x}', gen_gap=x)
add('gens=1 (budget 3u)', max_gens=1, budget_units=3); add('gens=2 (budget 3u)', max_gens=2, budget_units=3)
add('gens=2 (budget 2u)', max_gens=2); add('gens=4 (budget 4u)', max_gens=4)
for x in [0.5,1.5,2.0]: add(f'gen_mult={x}', gen_mult=x)
add('w=50/30/20', w=(0.5,0.3,0.2)); add('w=20/30/50', w=(0.2,0.3,0.5)); add('w=40/35/25', w=(0.40,0.35,0.25))
add('tiers=2 (10/30)', d=(0.10,0.30), w=(0.5,0.5)); add('tiers=4 (5/12/22/35)', d=(0.05,0.12,0.22,0.35), w=(0.25,)*4)
for x in [0.15,0.20,0.30,0.35,0.40,0.50]: add(f'tp={x}', tp1=x)
for x in [0.5,0.6,0.67,0.8,0.9,1.0]: add(f'tp_sell={x}', tp1_frac=x)
for x in [0.5,0.75,1.5,2.0,3.0]: add(f'tail_target={x}', tail_exit=('target',x))
add('tail_target=none', tail_exit=('none',))
add('drift=none', drift=None)
for x in [0.10,0.15,0.25,0.30,0.40]: add(f'drift={x}', drift=x)
for x in [0.0,0.05,0.10,0.15,0.20,0.30]: add(f'spike_size={x}', spike_frac=x)
for x in [0.40,0.50,0.55,0.65,0.70,0.80]: add(f'spike_depth={x}', spike_depth=x)
for x in [0.20,0.30,0.50,0.60,1.00]: add(f'spike_tp={x}', spike_tp=x)
add('roll=off', roll=False)
add('costs x2 (fee .2%, pen .2%)', fee=0.002, pen=0.002)
if __name__=='__main__':
    which=sys.argv[1]
    COLS=['variant','n','ret_med','logret','p10','p05','maxdd_med','util','trades_py','cycles_py']
    if which=='focus':
        for H in [540,1095]:
            df=R.grid(lab.CORE+lab.SAT+['UNI'], S, horizon=H, step=30, workers=4); R.save(df,f'sens_focus_H{H}.csv')
            print(f'=== FOCUS H={H}'); print(R.table(df)[COLS].round(3).to_string(), flush=True)
    else:
        sp={k:(v('X') if callable(v) else v) for k,v in S.items()}
        for H,step in [(540,60),(1095,90)]:
            df=R.universe_grid(sp, horizon=H, step=step, top=30, workers=4); R.save(df,f'sens_universe_H{H}.csv')
            print(f'=== UNIVERSE H={H}'); print(R.utable(df).reset_index()[COLS+['basket_med','basket_p10']].round(3).to_string(), flush=True)

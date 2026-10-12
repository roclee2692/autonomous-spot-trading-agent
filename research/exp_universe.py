"""Key variants on the point-in-time top-30 liquid USDT altcoin universe (daily bars).
Survivorship-free: coins chosen by trailing 90d volume at each start date, delisted coins included."""
import sys, numpy as np, pandas as pd
import engine as E, lab, runner as R
pd.set_option('display.width',260); pd.set_option('display.max_rows',300)
D=(0.07,0.17,0.29)
def C(**kw):
    base=dict(d=D, max_gens=3, spike_frac=0.075); base.update(kw); return ('core', E.CoreParams(**base))
SPECS={
 'V2': C(), 'bh': ('bh',), 'cash': ('cash',),
 'simple_allin': ('core', E.CoreParams(d=D, tp1_frac=1.0, tp2_frac=0.0, max_gens=1, budget_units=1, tp2_reanchor=False)),
 'noSpike': C(spike_frac=0.0), 'noTP2reanchor': C(tp2_reanchor=False), 'noDrift': C(drift=None),
 'noRoll': C(roll=False), 'sellAll_TP1': C(tp1_frac=1.0, tp2_frac=0.0), 'noTail': C(tp2_frac=0.5),
 'f75_0_25': C(tp1_frac=0.75, tp2_frac=0.0),
 'tail_t50': C(tail_exit=('target',0.5)), 'tail_t100': C(tail_exit=('target',1.0)), 'tail_t200': C(tail_exit=('target',2.0)),
 'tail_tr50_25': C(tail_exit=('trail',0.5,0.25)), 'tail_tr100_30': C(tail_exit=('trail',1.0,0.30)),
 'gens1_u4': C(max_gens=1, budget_units=4), 'gens2_u4': C(max_gens=2, budget_units=4),
 'gens3_u4': C(max_gens=3, budget_units=4), 'gens4_u4': C(max_gens=4, budget_units=4),
 'gap10': C(gen_gap=0.10), 'gap20': C(gen_gap=0.20), 'gap30': C(gen_gap=0.30),
 'gen_single20': C(gen_d=(0.20,), gen_w=(1.0,)), 'gen_single30': C(gen_d=(0.30,), gen_w=(1.0,)),
 'reb20': C(gen_rebound=0.20), 'genhalf': C(gen_mult=0.5),
 'tp20': C(tp1=0.20, tp2=0.40), 'tp30': C(tp1=0.30, tp2=0.60), 'tp40': C(tp1=0.40, tp2=0.80),
 'w33': C(w=(1/3,1/3,1/3)), 'w50_30_20': C(w=(0.5,0.3,0.2)), 'w30_30_40': C(w=(0.3,0.3,0.4)),
 'd3_35': C(d=(0.07,0.18,0.35)), 'd3_40': C(d=(0.07,0.18,0.40)), 'd3_25': C(d=(0.06,0.14,0.25)),
}
COLS=['n','ret_med','ret_mean','logret','alpha','p10','p05','maxdd_med','maxdd_p90','deep30','under_avg','util','trades_py','cycles_py','basket_med','basket_p10']
if __name__=='__main__':
    H=int(sys.argv[1]) if len(sys.argv)>1 else 540
    df=R.universe_grid(SPECS, horizon=H, step=60, top=30)
    R.save(df, f'universe_H{H}.csv')
    t=R.utable(df)
    print(t[COLS].round(3).to_string())

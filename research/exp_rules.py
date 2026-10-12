"""Ablations and rule scans on the V2 core (focus coins, 1h; HYPE daily)."""
import sys, numpy as np, pandas as pd
import engine as E, lab, runner as R
pd.set_option('display.width',260); pd.set_option('display.max_rows',300)

def V(**kw):
    def f(coin):
        base=dict(d=E.V2_CORE.get(coin,(0.07,0.17,0.29)), max_gens=3, spike_frac=0.075)
        base.update(kw); return ('core', E.CoreParams(**base))
    return f

VARIANTS = {
 'V2': V(),
 # ---- ablation
 'abl_noTP2_tail50': V(tp2_frac=0.0),
 'abl_noTP2_sell75': V(tp2_frac=0.0, tp1_frac=0.75),
 'abl_noTail': V(tp2_frac=0.5),
 'abl_sellAll_TP1': V(tp1_frac=1.0, tp2_frac=0.0),
 'abl_noRoll': V(roll=False),
 'abl_noTP2reanchor': V(tp2_reanchor=False),
 'abl_noDrift': V(drift=None),
 'drift10': V(drift=0.10), 'drift30': V(drift=0.30),
 'abl_noSpike': V(spike_frac=0.0),
 # ---- generations at fixed gen-1 size (budget = 4 units)
 'gens1_u4': V(max_gens=1, budget_units=4), 'gens2_u4': V(max_gens=2, budget_units=4),
 'gens3_u4': V(max_gens=3, budget_units=4), 'gens4_u4': V(max_gens=4, budget_units=4),
 'gens1_u1': V(max_gens=1, budget_units=1, spike_frac=0.0),
 'gap05': V(gen_gap=0.05), 'gap10': V(gen_gap=0.10), 'gap15': V(gen_gap=0.15), 'gap20': V(gen_gap=0.20),
 'gap25': V(gen_gap=0.25), 'gap30': V(gen_gap=0.30),
 'genhalf': V(gen_mult=0.5), 'reb10': V(gen_rebound=0.10), 'reb20': V(gen_rebound=0.20),
 'gen_single20': V(gen_d=(0.20,), gen_w=(1.0,)), 'gen_single30': V(gen_d=(0.30,), gen_w=(1.0,)),
 'gen_wide': V(gen_d=(0.10,0.22,0.35)),
 # ---- TP structure
 'tp15': V(tp1=0.15, tp2=0.30), 'tp20': V(tp1=0.20, tp2=0.40), 'tp30': V(tp1=0.30, tp2=0.60),
 'tp40': V(tp1=0.40, tp2=0.80), 'tp20_50': V(tp1=0.20, tp2=0.50), 'tp25_75': V(tp1=0.25, tp2=0.75),
 'tp25_100': V(tp1=0.25, tp2=1.00),
 'f50_30_20': V(tp1_frac=0.5, tp2_frac=0.3), 'f60_20_20': V(tp1_frac=0.6, tp2_frac=0.2),
 'f40_30_30': V(tp1_frac=0.4, tp2_frac=0.3), 'f34_33_33': V(tp1_frac=0.34, tp2_frac=0.33),
 'f75_0_25': V(tp1_frac=0.75, tp2_frac=0.0), 'f50_50_0': V(tp1_frac=0.5, tp2_frac=0.5),
 'f25_25_50': V(tp1_frac=0.25, tp2_frac=0.25),
 # ---- tier weights
 'w33': V(w=(1/3,1/3,1/3)), 'w50_30_20': V(w=(0.5,0.3,0.2)), 'w30_30_40': V(w=(0.3,0.3,0.4)),
 'w20_30_50': V(w=(0.2,0.3,0.5)),
 # ---- tail exits
 'tail_t50': V(tail_exit=('target',0.5)), 'tail_t75': V(tail_exit=('target',0.75)),
 'tail_t100': V(tail_exit=('target',1.0)), 'tail_t150': V(tail_exit=('target',1.5)),
 'tail_t200': V(tail_exit=('target',2.0)), 'tail_t300': V(tail_exit=('target',3.0)),
 'tail_tr50_25': V(tail_exit=('trail',0.5,0.25)), 'tail_tr100_30': V(tail_exit=('trail',1.0,0.30)),
 'tail_tr100_40': V(tail_exit=('trail',1.0,0.40)), 'tail_tr50_35': V(tail_exit=('trail',0.5,0.35)),
 'tail_time365c': V(tail_exit=('time',365)), 'tail_time730c': V(tail_exit=('time',730)),
 'tail_timeany365': V(tail_exit=('time_any',365)), 'tail_t100_or730': V(tail_exit=('target_or_time',1.0,730)),
 'tail_tr100_30_or730': V(tail_exit=('trail_or_time',1.0,0.30,730)),
 # ---- uniform template (vs per-coin)
 'uni_7_17_29': lambda c: ('core', E.CoreParams(d=(0.07,0.17,0.29), max_gens=3, spike_frac=0.075)),
 'uni_7_18_35': lambda c: ('core', E.CoreParams(d=(0.07,0.18,0.35), max_gens=3, spike_frac=0.075)),
 'uni_7_18_40': lambda c: ('core', E.CoreParams(d=(0.07,0.18,0.40), max_gens=3, spike_frac=0.075)),
 'bh': ('bh',),
}
COLS=['variant','n','ret_med','logret','alpha','p10','p05','maxdd_med','maxdd_p90','deep30','under_avg','under_max','util','trades_py','cycles_py']
if __name__=='__main__':
    H=int(sys.argv[1]) if len(sys.argv)>1 else 540
    tag=sys.argv[2] if len(sys.argv)>2 else 'all'
    kw={}
    if tag=='oos': kw=dict(d_from=R.IS_END_DAY)
    if tag=='is': kw=dict(d_to=R.IS_END_DAY)
    coins=lab.CORE+lab.SAT+['UNI']
    df=R.grid(coins, VARIANTS, horizon=H, step=30, **kw)
    R.save(df, f'rules_H{H}_{tag}.csv')
    t=R.table(df)
    print(t[COLS].round(3).to_string())

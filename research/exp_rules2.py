"""Second batch: cost accounting (pooled vs per-generation), next-gen anchor (B3 vs cost),
time-based degrade (stale_days), spike-order shape. Base = candidate ladder (equal weights,
d3 0.35, gap 0.20, 3 gens, no TP2 re-anchor) and V2 for reference."""
import sys, numpy as np, pandas as pd
import engine as E, lab, runner as R
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
W=(1/3,1/3,1/3)
def K(**kw):
    base=dict(d=(0.07,0.17,0.35), w=W, gen_gap=0.20, max_gens=3, spike_frac=0.075, tp2_reanchor=False)
    base.update(kw); return ('core', E.CoreParams(**base))
V2=('core', E.CoreParams(d=(0.07,0.17,0.29), max_gens=3, spike_frac=0.075))
SPECS={
 'V2': V2, 'V2_pergen': ('core', E.CoreParams(d=(0.07,0.17,0.29), max_gens=3, spike_frac=0.075, cost_mode='pergen')),
 'K': K(), 'K_pergen': K(cost_mode='pergen'), 'K_anchorC': K(gen_anchor='cost'), 'K_anchorC_gap20': K(gen_anchor='cost', gen_gap=0.35),
 'K_stale90': K(stale_days=90), 'K_stale180': K(stale_days=180), 'K_stale365': K(stale_days=365),
 'K_nospike': K(spike_frac=0.0), 'K_spike50': K(spike_depth=0.50), 'K_spike70': K(spike_depth=0.70),
 'K_spike_tp25': K(spike_tp=0.25), 'K_spike_tp60': K(spike_tp=0.60), 'K_spike15': K(spike_frac=0.15),
 'K_gens2': K(max_gens=2), 'K_gens4': K(max_gens=4),
 'K_tailt100': K(tail_exit=('target',1.0)), 'K_tailtr50_25': K(tail_exit=('trail',0.5,0.25)),
 'K_tailtr50_30': K(tail_exit=('trail',0.5,0.30)), 'K_tailtr100_30': K(tail_exit=('trail',1.0,0.30)),
 'K_tailt50': K(tail_exit=('target',0.5)), 'K_sellall': K(tp1_frac=1.0, tp2_frac=0.0),
 'K_f75_25tail_t100': K(tp1_frac=0.75, tp2_frac=0.0, tail_exit=('target',1.0)),
 'K_tailtime365': K(tail_exit=('time_any',365)), 'K_tailt100or730': K(tail_exit=('target_or_time',1.0,730)),
 'bh': ('bh',),
}
COLS=['variant','n','ret_med','ret_mean','logret','alpha','p10','p05','maxdd_med','deep30','under_avg','util','trades_py','cycles_py']
if __name__=='__main__':
    which=sys.argv[1]; H=int(sys.argv[2]) if len(sys.argv)>2 else 540
    if which=='focus':
        df=R.grid(lab.CORE+lab.SAT+['UNI'], SPECS, horizon=H, step=30, workers=2); R.save(df,f'rules2_focus_H{H}.csv'); t=R.table(df)
        print(t[COLS].round(3).to_string())
    else:
        df=R.universe_grid(SPECS, horizon=H, step=60, top=30, workers=2); R.save(df,f'rules2_universe_H{H}.csv'); t=R.utable(df).reset_index()
        print(t[COLS+['basket_med','basket_p10']].round(3).to_string())

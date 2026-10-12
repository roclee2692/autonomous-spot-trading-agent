"""Joint scan: tier-3 depth x generation gap x max generations (equal weights, budget 4 units
so gen-1 size is fixed), on focus coins (1h) and on the PIT universe (1d)."""
import sys, itertools, numpy as np, pandas as pd
import engine as E, lab, runner as R
pd.set_option('display.width',250); pd.set_option('display.max_rows',400)
W=(1/3,1/3,1/3)
def P(d3,gap,gens, **kw):
    return E.CoreParams(d=(0.07,0.17,d3), w=W, gen_gap=gap, max_gens=gens, budget_units=4, spike_frac=0.075, tp2_reanchor=False, **kw)
SPECS={f"d3={d3:.2f} gap={gap:.2f} g={g}": ('core', P(d3,gap,g)) for d3,gap,g in itertools.product([0.25,0.30,0.35,0.40],[0.0,0.10,0.20,0.30],[2,3,4])}
if __name__=='__main__':
    which=sys.argv[1]
    if which=='focus':
        df=R.grid(lab.CORE+lab.SAT+['UNI'], SPECS, horizon=540, step=30, workers=2)
        R.save(df,'depth_focus.csv'); t=R.table(df)
    else:
        df=R.universe_grid(SPECS, horizon=540, step=60, top=30, workers=2)
        R.save(df,'depth_universe.csv'); t=R.utable(df).reset_index()
    cols=['variant','ret_med','logret','alpha','p10','maxdd_med','util','cycles_py']+(['basket_med','basket_p10'] if which!='focus' else [])
    print(t[cols].round(3).to_string())

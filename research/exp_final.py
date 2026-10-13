"""Final validation of the V3 candidate: ablation of every V3 rule, horizons, IS/OOS, universe,
block-bootstrap CI of V3-V2, and an expanding-window walk-forward re-selection test."""
import sys, itertools, numpy as np, pandas as pd
import engine as E, lab, runner as R
pd.set_option('display.width',260); pd.set_option('display.max_rows',200)
W3=(1/3,1/3,1/3)
def V3P(**kw):
    base=dict(d=(0.07,0.17,0.35), w=W3, gen_gap=0.20, max_gens=3, spike_frac=0.075, tp2_reanchor=False,
              tp1=0.25, tp1_frac=0.75, tp2_frac=0.0, tail_exit=('target',1.0), drift=0.20)
    base.update(kw); return E.CoreParams(**base)
def V31P(**kw):
    """V3.1 = V3 with the next-generation anchor at B3 fill x 0.60 (gen_gap 0.40)."""
    kw.setdefault('gen_gap', 0.40)
    return V3P(**kw)
def v2spec(coin): return ('core', E.CoreParams(d=E.V2_CORE.get(coin,(0.07,0.17,0.29)), max_gens=3, spike_frac=0.075))
SPECS={
 'V2': v2spec, 'V3': ('core', V3P()), 'bh': ('bh',),
 'V3-noSpike': ('core', V3P(spike_frac=0.0)),
 'V3-gens1': ('core', V3P(max_gens=1, budget_units=3)),
 'V3-gens2': ('core', V3P(max_gens=2, budget_units=3)),
 'V3-gap0': ('core', V3P(gen_gap=0.0)),
 'V3-noDrift': ('core', V3P(drift=None)),
 'V3-noRoll': ('core', V3P(roll=False)),
 'V3-tailPermanent': ('core', V3P(tail_exit=('none',))),
 'V3-noTail(sell100)': ('core', V3P(tp1_frac=1.0)),
 'V3-w40/35/25': ('core', V3P(w=(0.40,0.35,0.25))),
 'V3-d3=29': ('core', V3P(d=(0.07,0.17,0.29))),
 'V3-tp20': ('core', V3P(tp1=0.20)), 'V3-tp30': ('core', V3P(tp1=0.30)),
 'V3-tail trail50/30': ('core', V3P(tail_exit=('trail',0.5,0.30))),
 'V3-tail t150': ('core', V3P(tail_exit=('target',1.5))),
 'V3+TP2(50/25/25)': ('core', V3P(tp1_frac=0.5, tp2_frac=0.25, tp2=0.5)),
 'V3-gens4': ('core', V3P(max_gens=4)),
 'V3-spike15': ('core', V3P(spike_frac=0.15)),
}
COLS=['variant','n','ret_med','ret_mean','logret','alpha','p10','p05','maxdd_med','maxdd_p90','deep20','deep30','under_avg','under_max','util','trades_py','cycles_py','fees']
def boot(df, a, b, key='coin', B=2000, block=180, seed=1):
    """Block bootstrap over start dates (blocks of `block` days) of mean logret and p10 differences."""
    x=df[df.variant.isin([a,b])].copy(); x['lr']=np.log1p(x.ret.clip(lower=-0.99))
    p=x.pivot_table(index=[key,'start_day'],columns='variant',values=['lr','ret']).dropna()
    starts=p.index.get_level_values('start_day'); blocks=(starts//block).values; ub=np.unique(blocks)
    rng=np.random.default_rng(seed); d_lr=[]; d_p10=[]
    for _ in range(B):
        pick=rng.choice(ub, len(ub)); idx=np.concatenate([np.where(blocks==u)[0] for u in pick])
        s=p.iloc[idx]
        d_lr.append(s['lr'][a].mean()-s['lr'][b].mean())
        d_p10.append(s['ret'][a].quantile(.1)-s['ret'][b].quantile(.1))
    return np.percentile(d_lr,[5,50,95]), np.percentile(d_p10,[5,50,95])
if __name__=='__main__':
    which=sys.argv[1]
    if which=='focus':
        for H in [365,540,1095]:
            df=R.grid(lab.CORE+lab.SAT+['UNI'], SPECS, horizon=H, step=30, workers=2); R.save(df,f'final_focus_H{H}.csv')
            print(f'=== FOCUS H={H}'); print(R.table(df)[COLS].round(3).to_string())
            lr,p10=boot(df,'V3','V2'); print('bootstrap V3-V2 logret 5/50/95%:',lr.round(3),' p10 diff:',p10.round(3))
        for tag,kw in [('IS',dict(d_to=R.IS_END_DAY)),('OOS',dict(d_from=R.IS_END_DAY))]:
            df=R.grid(lab.CORE+lab.SAT+['UNI'], {k:SPECS[k] for k in ['V2','V3','bh','V3-tailPermanent','V3-gap0','V3-noSpike']}, horizon=365, step=30, workers=2, **kw)
            print(f'=== FOCUS {tag} H=365'); print(R.table(df)[COLS].round(3).to_string())
    elif which=='universe':
        sp={k:(v('X') if callable(v) else v) for k,v in SPECS.items()}
        for H in [365,540,1095]:
            df=R.universe_grid(sp, horizon=H, step=60, top=30, workers=2); R.save(df,f'final_universe_H{H}.csv')
            print(f'=== UNIVERSE H={H}'); print(R.utable(df).reset_index()[COLS+['basket_med','basket_p10']].round(3).to_string())
            lr,p10=boot(df.rename(columns={'symbol':'coin'}),'V3','V2'); print('bootstrap V3-V2 logret 5/50/95%:',lr.round(3),' p10 diff:',p10.round(3))
            df['period']=np.where(df.start_day+H<=R.IS_END_DAY,'IS(window ends<2024)',np.where(df.start_day>=R.IS_END_DAY,'OOS(start>=2024)','straddle'))
            for per,g in df.groupby('period'):
                t=R.utable(g)[['n','ret_med','logret','p10','maxdd_med','basket_med','basket_p10']]
                print('  ',per); print(t.loc[['V2','V3','bh','V3-tailPermanent','V3-gap0']].round(3).to_string())

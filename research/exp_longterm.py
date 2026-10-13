"""Round 2 support runs:
 G2 long-term: full-history single paths per focus coin + universe 5-year windows (V2, V3, V3 tail permanent, V3 no tail, B&H).
 G3 portfolio: PIT baskets by liquidity-rank bucket, equal weight, daily equity aggregated; plus 'V2 at reduced size'
    (k*V2 + (1-k)*cash) chosen to match V3's drawdown, to test whether V3's structure beats simply holding less.
 G4 spike event study: every spike-order fill, its P&L, holding time and whether it was a wick."""
import sys, numpy as np, pandas as pd, engine as E, lab, runner as R
from exp_final import V3P
from concurrent.futures import ProcessPoolExecutor
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
DAY=E.DAY_MS
STRATS={'V2':None,'V3':V3P(),'V3 tail permanent':V3P(tail_exit=('none',)),'V3 no tail':V3P(tp1_frac=1.0),
        'V3 no spike':V3P(spike_frac=0.0)}
def v2p(name): return E.CoreParams(d=E.V2_CORE.get(name,(0.07,0.17,0.29)), max_gens=3, spike_frac=0.075)
def run(b, name, strat):
    if strat=='bh': return E.run_bh(b)
    p=v2p(name) if strat=='V2' else STRATS[strat]
    return E.run_core(b,p)
def g2_focus():
    rows=[]
    for c in lab.CORE+lab.SAT+['UNI']:
        b=R._bars(c,'1d' if c=='HYPE' else '1h')
        yrs=len(np.unique(b.t//DAY))/365
        for s in list(STRATS)+['bh']:
            r=run(b,c,s); eq=r['equity']; dd=(1-eq/np.maximum.accumulate(eq)).max()
            rows.append({'coin':c,'strat':s,'years':round(yrs,1),'final':eq[-1],'cagr':eq[-1]**(1/yrs)-1 if eq[-1]>0 else -1,'maxdd':dd,
                         'tail_share': (r.get('tail_qty',0)*b.c[-1]/eq[-1]) if s!='bh' else np.nan})
    return pd.DataFrame(rows)
def _uj(a):
    sym,d0,H=a; b=R.symbol_bars(sym,d0,d0+H)
    if b is None: return []
    out=[]
    for s in list(STRATS)+['bh']:
        r=run(b,sym,s); m=lab.metrics(r,years_override=H/365); out.append({'sym':sym,'d0':d0,'strat':s,'ret':m['ret'],'maxdd':m['maxdd'],'eq':r['equity']})
    return out
def universe_runs(H, step, top=30, start='2019-01-01'):
    d=int(pd.Timestamp(start).value//10**6//DAY); last=int(R.universe_panel()['close'].index.max())-H; jobs=[]
    while d<=last:
        jobs+=[(s,d,H) for s in R.pit_universe(d,top)]; d+=step
    with ProcessPoolExecutor(4) as ex: rows=[x for p in ex.map(_uj,jobs,chunksize=8) for x in p]
    return pd.DataFrame(rows)
def baskets(df, H):
    """rank buckets by PIT liquidity rank within each start date."""
    out=[]
    for d0,g in df.groupby('d0'):
        syms=list(dict.fromkeys(g.sym))  # order = liquidity rank (pit_universe order)
        for name,(a,b) in {'rank1-4':(0,4),'rank5-8':(4,8),'rank9-16':(8,16),'rank17-30':(16,30),'top8':(0,8),'top30':(0,30)}.items():
            pick=syms[a:b]
            if len(pick)<(b-a)*0.75: continue
            for s,gs in g[g.sym.isin(pick)].groupby('strat'):
                eqs=np.vstack([np.pad(e,(0,H-len(e)),mode='edge')[:H] for e in gs['eq']])
                eq=eqs.mean(0); dd=(1-eq/np.maximum.accumulate(eq)).max()
                out.append({'d0':d0,'bucket':name,'strat':s,'ret':eq[-1]-1,'maxdd':dd,'eq':eq})
    return pd.DataFrame(out)
def summarize(bk):
    bk=bk.copy(); bk['lr']=np.log1p(bk.ret.clip(lower=-0.99))
    return bk.groupby(['bucket','strat']).agg(n=('ret','size'),med=('ret','median'),lr=('lr','mean'),p10=('ret',lambda x:x.quantile(.1)),
                                               dd_med=('maxdd','median'),dd_p90=('maxdd',lambda x:x.quantile(.9))).round(3)
def matched_v2(bk):
    """For each bucket: k*V2+(1-k)*cash with k s.t. median maxDD equals V3's; compare log return."""
    rows=[]
    for b,g in bk.groupby('bucket'):
        v3=g[g.strat=='V3'].set_index('d0'); v2=g[g.strat=='V2'].set_index('d0'); bh=g[g.strat=='bh'].set_index('d0')
        j=v3.index.intersection(v2.index)
        target=v3.loc[j,'maxdd'].median()
        for nm,src in [('V2',v2),('bh',bh)]:
            best=None
            for k in np.linspace(0.05,1,96):
                dds=[]; rets=[]
                for d0 in j:
                    e=1-k+k*src.loc[d0,'eq']; dds.append((1-e/np.maximum.accumulate(e)).max()); rets.append(e[-1]-1)
                if np.median(dds)>=target: best=(k,np.mean(np.log1p(rets)),np.quantile(rets,.1),np.median(dds)); break
            if best: rows.append({'bucket':b,'scaled':nm,'k':round(best[0],2),'lr_scaled':round(best[1],3),'p10_scaled':round(best[2],3),'dd_med':round(best[3],3),
                                  'V3_lr':round(np.mean(np.log1p(v3.loc[j,'ret'])),3),'V3_p10':round(v3.loc[j,'ret'].quantile(.1),3),'V3_dd_med':round(target,3)})
    return pd.DataFrame(rows)
def g4_spike():
    rows=[]
    def collect(b, name, src):
        r=E.run_core(b,V3P()); ev=r['events']; buys=[e for e in ev if e[1]=='spike_buy']; sells=[e for e in ev if e[1]=='spike_sell']
        for k,bu in enumerate(buys):
            se=sells[k] if k<len(sells) else None
            i=bu[0]; day_close=b.c[min(len(b.c)-1, np.searchsorted(b.t, (b.t[i]//DAY+1)*DAY)-1)]
            rows.append({'src':src,'coin':name,'buy_t':pd.to_datetime(b.t[i],unit='ms'),'buy':bu[2],'sell':se[2] if se else np.nan,
                         'days_held':(b.t[se[0]]-b.t[i])/DAY if se else np.nan,'wick':day_close>=bu[2]*1.15,
                         'open_at_end': se is None, 'mark_end': b.c[-1]/bu[2]-1 if se is None else np.nan})
    for c in lab.CORE+lab.SAT+['UNI']:
        collect(R._bars(c,'1d' if c=='HYPE' else '1h'), c, 'focus')
    return pd.DataFrame(rows)
if __name__=='__main__':
    part=sys.argv[1]
    if part=='g2':
        f=g2_focus(); R.save(f,'longterm_focus_fullhistory.csv')
        print('FULL HISTORY per coin (final equity multiple, CAGR, maxDD, tail share of equity):')
        print(f.pivot_table(index='coin',columns='strat',values='final').round(2).to_string())
        print(f.pivot_table(index='coin',columns='strat',values='cagr').round(3).to_string())
        print(f.pivot_table(index='coin',columns='strat',values='maxdd').round(2).to_string())
        print(f.pivot_table(index='coin',columns='strat',values='tail_share').round(2).to_string())
        u=universe_runs(1825,90); u['lr']=np.log1p(u.ret.clip(lower=-0.99))
        print('\nUNIVERSE 5-year windows (H=1825):'); print(u.groupby('strat').agg(n=('ret','size'),med=('ret','median'),lr=('lr','mean'),p10=('ret',lambda x:x.quantile(.1)),dd=('maxdd','median')).round(3))
        bk=baskets(u,1825); print(summarize(bk).to_string())
    elif part=='g3':
        for H,step in [(540,60),(1095,90)]:
            u=universe_runs(H,step); bk=baskets(u,H)
            print(f'\n=== PORTFOLIO BASKETS H={H} (equal weight within bucket, PIT liquidity rank)'); print(summarize(bk).to_string())
            print('V2 / B&H scaled down to V3 median drawdown:'); print(matched_v2(bk).to_string())
            u.drop(columns=['eq']).to_csv(f'results/portfolio2_runs_H{H}.csv',index=False)
    elif part=='g4':
        s=g4_spike(); R.save(s,'spike_events.csv')
        s['ret']=s.sell/s.buy-1
        print('spike fills per coin:'); print(s.groupby('coin').agg(fills=('buy','size'),sold=('ret','count'),med_days=('days_held','median'),wick_share=('wick','mean'),open_now=('open_at_end','sum')).to_string())
        print('fill years:'); print(s.buy_t.dt.year.value_counts().sort_index().to_dict())
        print('open positions marked:'); print(s[s.open_at_end][['coin','buy_t','buy','mark_end']].to_string())

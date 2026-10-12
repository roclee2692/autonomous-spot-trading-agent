import numpy as np, pandas as pd
from scipy.stats import spearmanr
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
df=pd.read_csv('results/params_grid.csv')
obj='logret'
agg=df.groupby(['period','coin','variant']).agg(lr=('logret','mean'),med=('ret','median'),p10=('ret',lambda x: x.quantile(.1)),dd=('maxdd','median'),n=('ret','size')).reset_index()
IS=agg[agg.period=='IS']; OOS=agg[agg.period=='OOS']
is_coins=sorted(IS.coin.unique()); print('IS coins',is_coins)
tem=IS[IS.variant!='V2']
# uniform: best pooled IS
uni=tem.groupby('variant').lr.mean().sort_values(ascending=False)
print('Top uniform IS templates:'); print(uni.head(8).round(3)); print('worst', uni.tail(3).round(3))
best_uni=uni.index[0]
core_is=['LINK','AAVE']; sat_is=['NEAR','RENDER','UNI']
best_core=tem[tem.coin.isin(core_is)].groupby('variant').lr.mean().idxmax()
best_sat=tem[tem.coin.isin(sat_is)].groupby('variant').lr.mean().idxmax()
best_coin=tem.loc[tem.groupby('coin').lr.idxmax()].set_index('coin').variant
print('best uniform',best_uni,'core',best_core,'sat',best_sat); print('per-coin', best_coin.to_dict())
rows=[]
for coin in sorted(OOS.coin.unique()):
    o=OOS[OOS.coin==coin].set_index('variant')
    grp = best_core if coin in ['LINK','AAVE','TAO','HYPE'] else best_sat
    r={'coin':coin,'uniform':o.loc[best_uni,'lr'],'group':o.loc[grp,'lr'],
       'percoin':o.loc[best_coin[coin],'lr'] if coin in best_coin else np.nan,
       'V2':o.loc['V2','lr'] if 'V2' in o.index else np.nan,
       'oos_best':o[o.index!='V2'].lr.max(),'oos_median_template':o[o.index!='V2'].lr.median(),'oos_worst':o[o.index!='V2'].lr.min()}
    rows.append(r)
res=pd.DataFrame(rows).set_index('coin'); print('\nOOS mean log-return (365d windows) by selection method:'); print(res.round(3)); print(res.mean().round(3))
# IS->OOS rank stability per coin
print('\nSpearman(IS rank, OOS rank) of 47 templates per coin:')
for coin in is_coins:
    a=IS[(IS.coin==coin)&(IS.variant!='V2')].set_index('variant').lr; b=OOS[(OOS.coin==coin)&(OOS.variant!='V2')].set_index('variant').lr
    j=a.index.intersection(b.index); print(coin, round(spearmanr(a[j],b[j]).correlation,2))
# cross-coin: does a template's rank on coin X predict rank on coin Y (OOS)?
piv=OOS[OOS.variant!='V2'].pivot(index='variant',columns='coin',values='lr')
print('\nOOS cross-coin template rank correlation:'); print(piv.corr(method='spearman').round(2))
# plateau: marginal effect of each dimension (OOS, coin-equal)
o2=OOS[OOS.variant!='V2'].copy(); o2[['d1','d2','d3']]=o2.variant.str.split('/',expand=True).astype(float)
for per,data in [('IS',IS[IS.variant!='V2']),('OOS',OOS[OOS.variant!='V2'])]:
    d=data.copy(); d[['d1','d2','d3']]=d.variant.str.split('/',expand=True).astype(float)
    for k in ['d1','d2','d3']:
        print(per,k, d.groupby(k).agg(lr=('lr','mean'),p10=('p10','mean'),dd=('dd','mean')).round(3).T.to_dict())

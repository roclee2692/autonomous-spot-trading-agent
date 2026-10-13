"""Paired block bootstrap and White reality check for the tail grid (universe runs).
Unit = one start date (basket of the PIT top-30 alts, equal budget). Blocks of
consecutive start dates as long as the horizon, so overlapping windows stay together."""
import numpy as np
import pandas as pd

pd.set_option('display.width', 250)
STEP = {540: 60, 1095: 90, 1825: 90, 2555: 90}


def basket_lr(H):
    bk = pd.read_pickle(f'results/r3_g2bk_{H}.pkl')
    bk['lr'] = np.log1p(bk.ret_B.clip(lower=-.99))
    return bk.pivot_table(index='d0', columns='strat', values='lr').sort_index()


def coin_lr(H):
    from exp_r3_long import MAJORS
    df = pd.read_pickle(f'results/r3_g2_{H}.pkl')
    df = df[~df.sym.isin(MAJORS)]
    df['lr'] = np.log1p(df.ret_B.clip(lower=-.99))
    p = df.pivot_table(index=['d0', 'sym'], columns='strat', values='lr')
    return p.groupby(level='d0').mean()          # mean per start date = equal-weight coin log return


def block_boot(diff: np.ndarray, block: int, B=5000, seed=7):
    rng = np.random.default_rng(seed)
    n = len(diff)
    nb = int(np.ceil(n / block))
    out = np.empty(B)
    for b in range(B):
        starts = rng.integers(0, max(n - block + 1, 1), nb)
        idx = np.concatenate([np.arange(s, min(s + block, n)) for s in starts])[:n]
        out[b] = diff[idx].mean()
    return out


if __name__ == '__main__':
    base = 's25x2'
    for H in (540, 1095, 1825, 2555):
        for label, M in (('basket log', basket_lr(H)), ('coin-mean log', coin_lr(H))):
            block = max(1, int(np.ceil(H / STEP[H] / 2)))
            cells = [c for c in M.columns if c not in ('bh', base)]
            D = M[cells].values - M[[base]].values
            # White reality check: max mean diff over cells vs bootstrap of centred max
            rng = np.random.default_rng(11)
            n = len(D); nb = int(np.ceil(n / block)); Bn = 3000
            mx = []
            for _ in range(Bn):
                starts = rng.integers(0, max(n - block + 1, 1), nb)
                idx = np.concatenate([np.arange(s, min(s + block, n)) for s in starts])[:n]
                mx.append((D[idx].mean(0) - D.mean(0)).max())
            p_white = float(np.mean(np.array(mx) >= D.mean(0).max()))
            rows = []
            for c in ('s10x4', 's10x5', 's15x4', 's15x5', 's10x3'):
                d = M[c].values - M[base].values
                bs = block_boot(d, block)
                rows.append({'cell': c, 'mean_diff': d.mean(), 'ci05': np.quantile(bs, .05), 'ci95': np.quantile(bs, .95),
                             'P(diff<=0)': float((bs <= 0).mean()), 'share_starts_better': float((d > 0).mean())})
            print(f'\nH={H} {label}: n_starts={n} block={block}  White RC p (best of {len(cells)} cells) = {p_white:.3f}')
            print(pd.DataFrame(rows).round(3).to_string(index=False))

"""Station-level MCDA allocation (Equations 8-9) with rounding, regional
rebalancing and the minimum-coverage rule (Section 3.2.4).

The procedure is applied separately for every region r, scenario k and charger
type c, and is written so that the station counts always sum exactly to the
regional total N_c,r,k fixed beforehand by Equations (5)-(7):

  1. w_s = w1*D_s + w2*R_s + w3*T_s                                   (Eq. 8)
  2. x_s = N_c,r,k * w_s / sum(w_s)                                   (Eq. 9)
  3. n_s = round(x_s)                                       (integer rounding)
  4. add/remove units by largest remainder until sum(n_s) = N_c,r,k
                                                          (regional rebalancing)
  5. every station of the predominant class left with zero units (x_s < 0.5)
     gets one unit;
     each unit added is offset by removing one unit from the station that
     currently holds the most units, so sum(n_s) = N_c,r,k still holds
                                                         (minimum coverage)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["station_id", "region", "station_class", "pop_density", "dist_highway_km"]


def _minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = np.nanmin(x), np.nanmax(x)
    return np.zeros_like(x, dtype=float) if hi == lo else (x - lo) / (hi - lo)


def composite_weights(stations: pd.DataFrame, p: dict, ctype: str) -> pd.Series:
    """Equation (8). D_s: normalised population density; R_s: normalised road
    proximity (1 at the station closest to a highway corridor); T_s: 1 when the
    station class suits the charger type (urban/peri-urban for AC,
    highway/remote for DC)."""
    a = p["allocation"]
    pred = set(p["chargers"][ctype]["predominant_classes"])

    def score(df):
        d = _minmax(df["pop_density"].to_numpy(float))
        r = 1.0 - _minmax(df["dist_highway_km"].to_numpy(float))
        t = df["station_class"].isin(pred).to_numpy(float)
        return pd.Series(a["w1_population_density"] * d + a["w2_road_proximity"] * r
                         + a["w3_typology"] * t, index=df.index)

    if a.get("normalization", "national") == "regional":
        return stations.groupby("region", group_keys=False).apply(score)
    return score(stations)


def allocate_region(weights: np.ndarray, is_predominant: np.ndarray, total: int,
                    min_share: float = 0.5) -> tuple[np.ndarray, dict]:
    """Steps 2-5 for one region and charger type. Returns integer counts and a log."""
    weights = np.asarray(weights, float)
    n_st = len(weights)
    if n_st == 0 or total == 0:
        return np.zeros(n_st, int), {"floor_units": 0}
    wsum = weights.sum()
    x = total * (weights / wsum if wsum > 0 else np.full(n_st, 1.0 / n_st))   # Eq. (9)

    n = np.floor(x + 0.5).astype(int)                     # step 3: round half up
    diff = total - n.sum()                                                       # step 4
    rem = x - n
    if diff > 0:
        n[np.argsort(-rem, kind="stable")[:diff]] += 1
    elif diff < 0:
        cand = np.where(n > 0)[0]
        n[cand[np.argsort(rem[cand], kind="stable")[: -diff]]] -= 1

    # step 5: stations whose share rounded to zero (x_s < 0.5, or trimmed in step 4)
    need = np.where(is_predominant & (n == 0))[0]
    # if the regional total cannot cover every station, the highest-weight ones are served first
    need = need[np.argsort(-weights[need], kind="stable")]
    placed = 0
    for idx in need:
        donor = int(np.argmax(n))
        if n[donor] <= 1:          # no station can give up a unit without losing coverage
            break
        n[donor] -= 1
        n[idx] += 1
        placed += 1
    assert n.sum() == total and (n >= 0).all()
    return n, {"floor_units": placed, "floor_unserved": int(len(need) - placed)}


def allocate_stations(stations: pd.DataFrame, regional: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Allocate the regional AC and DC totals of one scenario to stations."""
    missing = [c for c in REQUIRED_COLUMNS if c not in stations.columns]
    if missing:
        raise ValueError(f"station file is missing columns: {missing}")
    out = stations.copy()
    thr = p["allocation"]["min_coverage_threshold"]
    for ctype in ("AC", "DC"):
        w = composite_weights(out, p, ctype)
        out[f"w_{ctype}"] = w
        out[f"n_{ctype}"] = 0
        pred = set(p["chargers"][ctype]["predominant_classes"])
        for region, total in zip(regional["region"], regional[f"n_{ctype}"]):
            idx = out.index[out["region"] == region]
            n, _ = allocate_region(w.loc[idx].to_numpy(),
                                   out.loc[idx, "station_class"].isin(pred).to_numpy(),
                                   int(total), thr)
            out.loc[idx, f"n_{ctype}"] = n
    out["n_total"] = out["n_AC"] + out["n_DC"]
    return out


def check_totals(alloc: pd.DataFrame, regional: pd.DataFrame) -> pd.DataFrame:
    """Demonstrates that station counts reproduce regional and national totals."""
    g = alloc.groupby("region")[["n_AC", "n_DC", "n_total"]].sum()
    r = regional.set_index("region")[["n_AC", "n_DC", "n_total"]]
    chk = r.join(g, rsuffix="_stations", how="left").fillna(0).astype(int)
    for c in ("n_AC", "n_DC", "n_total"):
        chk[f"{c}_match"] = chk[c] == chk[f"{c}_stations"]
    return chk.reset_index()

"""Regional demand, charger sizing and Coverage Gap Index (Equations 2-7 and 10)."""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_params(path: str | Path | None = None) -> dict:
    path = Path(path) if path else ROOT / "params" / "model_parameters.yaml"
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_regions(path: str | Path | None = None) -> pd.DataFrame:
    path = Path(path) if path else ROOT / "data" / "regional_inputs.csv"
    return pd.read_csv(path)


def charger_annual_energy_kwh(p: dict, ctype: str, beta: float | None = None) -> float:
    """Equation (5): E_charger,c = P_c * U_c * beta * 8760 (kWh per charger per year)."""
    c = p["chargers"][ctype]
    beta = p["chargers"]["availability_beta"] if beta is None else beta
    return c["rated_power_kw"] * c["utilization"] * beta * p["chargers"]["hours_per_year"]


def regional_requirements(p: dict, regions: pd.DataFrame, scenario: str,
                          beta: float | None = None) -> pd.DataFrame:
    """Equations (2)-(7) for every region under one scenario.

    Returns one row per region with EV stock, annual and public energy (kWh/yr)
    and the AC, DC and total charger counts (regional ceiling, Equation 6).
    """
    d = p["demand"]
    pen = d["scenarios"][scenario]
    out = regions[["region", "population_million", "vehicle_stock_thousand"]].copy()
    out["scenario"] = scenario
    out["ev_stock"] = out["vehicle_stock_thousand"] * 1e3 * pen                       # Eq. (2)
    out["e_annual_kwh"] = out["ev_stock"] * d["annual_vkt_km"] * d["specific_consumption_kwh_per_km"]  # Eq. (3)
    out["e_public_kwh"] = out["e_annual_kwh"] * d["public_charging_fraction"]         # Eq. (4)
    for ctype in ("AC", "DC"):
        e_ch = charger_annual_energy_kwh(p, ctype, beta)
        share = p["chargers"][ctype]["demand_share"]
        # Eq. (6); a tiny tolerance guards against floating-point noise before the ceiling
        out[f"n_{ctype}"] = [math.ceil(e * share / e_ch - 1e-9) for e in out["e_public_kwh"]]
    out["n_total"] = out["n_AC"] + out["n_DC"]                                       # Eq. (7)
    return out


def national_summary(p: dict, regions: pd.DataFrame, beta: float | None = None) -> pd.DataFrame:
    """Table 3: national totals for S1-S4 (sum of regional values)."""
    rows = []
    for s in p["demand"]["scenarios"]:
        r = regional_requirements(p, regions, s, beta)
        rows.append({
            "scenario": s,
            "penetration": p["demand"]["scenarios"][s],
            "ev_fleet_million": r["ev_stock"].sum() / 1e6,
            "public_energy_gwh": r["e_public_kwh"].sum() / 1e6,
            "n_AC": int(r["n_AC"].sum()),
            "n_DC": int(r["n_DC"].sum()),
            "n_total": int(r["n_total"].sum()),
        })
    return pd.DataFrame(rows)


def coverage_gap_index(p: dict, req: pd.DataFrame) -> pd.DataFrame:
    """Equation (10) and the classification bands of Section 3.2.5 (Table 5)."""
    out = req[["region", "n_total", "population_million"]].copy()
    out["charger_share_pct"] = 100 * out["n_total"] / out["n_total"].sum()
    out["population_share_pct"] = 100 * out["population_million"] / out["population_million"].sum()
    out["cgi"] = out["charger_share_pct"] / out["population_share_pct"]
    lo, hi = p["cgi"]["underserved_below"], p["cgi"]["oversupplied_from"]
    out["status"] = ["Underserved" if c < lo else "Oversupplied" if c >= hi else "Adequate"
                     for c in out["cgi"].round(2)]
    return out


def cgi_threshold_sensitivity(p: dict, cgi: pd.DataFrame) -> pd.DataFrame:
    """Number and names of underserved regions for each tested threshold (Section 4.4)."""
    rows = []
    for t in p["cgi"]["threshold_sensitivity"]:
        under = cgi.loc[cgi["cgi"].round(2) < t, "region"].tolist()
        rows.append({"threshold": t, "n_underserved": len(under), "regions": "; ".join(under)})
    return pd.DataFrame(rows)

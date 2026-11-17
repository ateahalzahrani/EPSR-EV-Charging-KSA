"""Sensitivity (Table 6) and techno-economic calculations (Sections 4.3, 4.6, 4.8, Table 8)."""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from .model import coverage_gap_index, national_summary, regional_requirements

# ---------------------------------------------------------------- sensitivity

OAT_PARAMETERS = {
    "alpha_public": ("demand", "public_charging_fraction"),
    "D_annual": ("demand", "annual_vkt_km"),
    "eta": ("demand", "specific_consumption_kwh_per_km"),
    "U_AC": ("chargers", "AC", "utilization"),
    "U_DC": ("chargers", "DC", "utilization"),
    "w1": ("allocation", "w1_population_density"),
    "w2": ("allocation", "w2_road_proximity"),
}


def _set(p: dict, path: tuple, factor: float) -> dict:
    q = copy.deepcopy(p)
    node = q
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] *= factor
    return q


def oat_sensitivity(p: dict, regions: pd.DataFrame) -> pd.DataFrame:
    """One-at-a-time +/-30 % perturbation of the national total under the reference scenario.

    The MCDA weights w1 and w2 enter only Equations (8)-(9), which redistribute a
    fixed regional total among stations, so their effect on N_total is zero by
    construction."""
    s = p["sensitivity"]["reference_scenario"]
    d = p["sensitivity"]["perturbation"]
    base = regional_requirements(p, regions, s)["n_total"].sum()
    rows = []
    for name, path in OAT_PARAMETERS.items():
        res = {"parameter": name, "base_N_total": int(base)}
        for label, f in (("minus", 1 - d), ("plus", 1 + d)):
            n = regional_requirements(_set(p, path, f), regions, s)["n_total"].sum()
            res[f"N_{label}"] = int(n)
            res[f"dN_{label}_pct"] = 100 * (n - base) / base
        rows.append(res)
    return pd.DataFrame(rows)


def beta_sensitivity(p: dict, regions: pd.DataFrame, beta: float = 0.92) -> dict:
    s4 = national_summary(p, regions).set_index("scenario").loc["S4", "n_total"]
    s4b = national_summary(p, regions, beta=beta).set_index("scenario").loc["S4", "n_total"]
    return {"beta": beta, "N_S4_beta1": int(s4), "N_S4_beta": int(s4b),
            "increase_pct": 100 * (s4b - s4) / s4}


# ------------------------------------------------------------------ economics

def npv(rate: float, cashflows: np.ndarray) -> float:
    t = np.arange(len(cashflows))
    return float(np.sum(cashflows / (1 + rate) ** t))


def irr(cashflows: np.ndarray, lo: float = -0.99, hi: float = 10.0) -> float:
    f = lambda r: npv(r, cashflows)
    if f(lo) * f(hi) > 0:
        return float("nan")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def capex_and_peak(p: dict, regions: pd.DataFrame, scenario: str = "S4") -> dict:
    """Section 4.8 opening paragraph: investment and peak-load derivation."""
    e = p["economics"]
    nat = national_summary(p, regions).set_index("scenario").loc[scenario]
    ac, dc = nat["n_AC"], nat["n_DC"]
    eq = ac * e["capex_equipment_usd"]["AC"] + dc * e["capex_equipment_usd"]["DC"]
    inst = ac * e["capex_installed_usd"]["AC"] + dc * e["capex_installed_usd"]["DC"]
    avg_gw = nat["public_energy_gwh"] / 8760
    cap_ac = ac * p["chargers"]["AC"]["rated_power_kw"] / 1e6
    cap_dc = dc * p["chargers"]["DC"]["rated_power_kw"] / 1e6
    return {
        "scenario": scenario,
        "capex_equipment_busd": eq / 1e9, "capex_installed_busd": inst / 1e9,
        "capex_per_year_busd_low": eq / 1e9 / e["rollout_years"],
        "capex_per_year_busd_high": inst / 1e9 / e["rollout_years"],
        "avg_load_gw": avg_gw,
        "avg_load_from_capacity_gw": cap_ac * p["chargers"]["AC"]["utilization"]
                                     + cap_dc * p["chargers"]["DC"]["utilization"],
        "installed_capacity_gw": cap_ac + cap_dc, "installed_AC_gw": cap_ac, "installed_DC_gw": cap_dc,
        "coincident_peak_gw": avg_gw * e["peak_to_average_ratio"],
        "annual_installs_AC": ac / e["rollout_years"], "annual_installs_DC": dc / e["rollout_years"],
    }


def lcoc_sensitivity(p: dict) -> pd.DataFrame:
    """Section 4.6: LCOC = tariff + non-energy component (inversely proportional to U)."""
    e = p["economics"]
    t0, ne0, u0 = e["tariff_sar_per_kwh"], e["lcoc_non_energy_sar_per_kwh_at_UDC"], p["chargers"]["DC"]["utilization"]
    d = p["sensitivity"]["perturbation"]
    rows = [{"case": "baseline", "tariff": t0, "U_DC": u0, "lcoc_sar": t0 + ne0}]
    for f in (1 - d, 1 + d):
        rows.append({"case": f"tariff x{f:.1f}", "tariff": t0 * f, "U_DC": u0, "lcoc_sar": t0 * f + ne0})
    for f in (1 - d, 1 + d):
        rows.append({"case": f"U_DC x{f:.1f}", "tariff": t0, "U_DC": u0 * f, "lcoc_sar": t0 + ne0 / f})
    out = pd.DataFrame(rows)
    out["lcoc_usd"] = out["lcoc_sar"] * e["usd_per_sar"]
    return out


def payback(p: dict, ctype: str = "DC", utilization: float | None = None) -> dict:
    """Simple payback PP = CAPEX / (revenue - energy purchase - OPEX), Section 4.8."""
    e, c = p["economics"], p["chargers"][ctype]
    u = c["utilization"] if utilization is None else utilization
    kwh = c["rated_power_kw"] * u * 8760
    capex = e["capex_installed_usd"][ctype]
    net = kwh * (e["retail_price_sar_per_kwh"] - e["tariff_sar_per_kwh"]) * e["usd_per_sar"] \
        - e["opex_fraction_of_capex"] * capex
    return {"type": ctype, "U": u, "kwh_per_year": kwh, "capex_usd": capex,
            "net_revenue_usd": net, "payback_years": capex / net}


def regional_npv_irr(p: dict, regions: pd.DataFrame) -> pd.DataFrame:
    """Table 8 (recomputed): regional NPV and IRR for the Table 8 scenario.

    CAPEX = installed unit cost x charger counts (Table 4); annual revenue =
    regional public energy x net margin (retail price - tariff), optionally scaled
    by regional CGI; OPEX = 3 % of CAPEX; 15 years; 10 % discount rate."""
    e = p["economics"]
    s = e["table8_scenario"]
    req = regional_requirements(p, regions, s)
    cgi = coverage_gap_index(p, req).set_index("region")["cgi"]
    margin = e["retail_price_sar_per_kwh"] - e["tariff_sar_per_kwh"]
    rows = []
    for _, r in req.iterrows():
        capex = r["n_AC"] * e["capex_installed_usd"]["AC"] + r["n_DC"] * e["capex_installed_usd"]["DC"]
        scale = round(cgi[r["region"]], e.get("table8_cgi_decimals", 2)) \
            if e["table8_scale_revenue_by_cgi"] else 1.0   # CGI as printed in Table 5
        revenue = r["e_public_kwh"] * margin * e["usd_per_sar"] * scale
        net = revenue - e["opex_fraction_of_capex"] * capex
        cf = np.r_[-capex, np.full(e["npv_horizon_years"], net)]
        rows.append({"region": r["region"], "chargers": int(r["n_total"]),
                     "share_pct": 100 * r["n_total"] / req["n_total"].sum(),
                     "cgi": cgi[r["region"]], "capex_musd": capex / 1e6,
                     "annual_net_musd": net / 1e6,
                     "npv_musd": npv(e["discount_rate"], cf) / 1e6, "irr_pct": 100 * irr(cf)})
    return pd.DataFrame(rows)


def pv_s5(p: dict) -> dict:
    """Scenario S5: PV + BESS + one 50 kW DC charger at highway/remote stations."""
    e = p["economics"]
    s5 = e["pv_s5"]
    fx = e["usd_per_sar"]
    gen = s5["pv_kwp"] * s5["ghi_kwh_m2_day"] * 365 * s5["performance_ratio"]
    charge = p["chargers"]["DC"]["rated_power_kw"] * p["chargers"]["DC"]["utilization"] * 8760
    export = gen - charge
    capex = sum(s5["capex_usd"].values())
    opex = e["opex_fraction_of_capex"] * capex
    r, n = e["discount_rate"], s5["lifetime_years"]
    crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
    export_rev = export * s5["export_rate_sar_per_kwh"] * fx
    lcoc_usd = (capex * crf + opex - export_rev) / charge
    net = charge * e["retail_price_sar_per_kwh"] * fx + export_rev - opex
    cf = np.r_[-capex, np.full(n, net)]
    st_npv = npv(r, cf)
    return {"pv_generation_kwh": gen, "capacity_factor": gen / (s5["pv_kwp"] * 8760),
            "charging_kwh": charge, "export_kwh": export, "capex_usd": capex,
            "lcoc_sar": lcoc_usd / fx, "lcoc_usd": lcoc_usd, "annual_net_usd": net,
            "npv_usd": st_npv, "irr_pct": 100 * irr(cf),
            "fleet_capex_musd": capex * s5["stations"] / 1e6,
            "fleet_npv_musd": st_npv * s5["stations"] / 1e6}

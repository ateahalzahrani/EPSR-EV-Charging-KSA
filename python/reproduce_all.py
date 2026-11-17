"""Reproduce every regional and national number reported in the revised manuscript.

Usage (from the repository root):
    python python/reproduce_all.py

Writes CSV tables to results/ and a pass/fail comparison against the values
printed in the manuscript to results/verification_report.md. If the processed
station file data/processed/stations_classified.csv is present, the
station-level allocation (Equations 8-9) is also run for S1-S4 and its regional
and national totals are checked.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ev_planning.allocation import allocate_stations, check_totals  # noqa: E402
from ev_planning.analysis import (beta_sensitivity, capex_and_peak, lcoc_sensitivity,  # noqa: E402
                                  oat_sensitivity, payback, pv_s5, regional_npv_irr)
from ev_planning.model import (ROOT, cgi_threshold_sensitivity, coverage_gap_index,  # noqa: E402
                               load_params, load_regions, national_summary,
                               regional_requirements)

RES = ROOT / "results"
STATIONS = ROOT / "data" / "processed" / "stations_classified.csv"

# Values printed in the revised manuscript: (label, reproduced value getter, reported, tolerance)
checks: list[tuple[str, float, float, float]] = []


def chk(label, value, reported, tol):
    checks.append((label, float(value), float(reported), float(tol)))


def main() -> int:
    RES.mkdir(exist_ok=True)
    p, regions = load_params(), load_regions()

    # Table 3 -----------------------------------------------------------------
    nat = national_summary(p, regions)
    nat.to_csv(RES / "table3_national_requirements.csv", index=False)
    t3 = {"S1": (5193.7, 329390, 39531, 368921), "S2": (8656.2, 548981, 65882, 614863),
          "S3": (13503.7, 856405, 102774, 959179), "S4": (17312.4, 1097953, 131759, 1229712)}
    for s, (e, ac, dc, tot) in t3.items():
        row = nat.set_index("scenario").loc[s]
        chk(f"Table 3 {s} public energy (GWh/yr)", row["public_energy_gwh"], e, 0.1)
        chk(f"Table 3 {s} AC chargers", row["n_AC"], ac, 0)
        chk(f"Table 3 {s} DC chargers", row["n_DC"], dc, 0)
        chk(f"Table 3 {s} total chargers", row["n_total"], tot, 0)

    # Regional requirements for every scenario --------------------------------
    allreq = pd.concat([regional_requirements(p, regions, s) for s in p["demand"]["scenarios"]])
    allreq.to_csv(RES / "regional_requirements_S1-S4.csv", index=False)

    # Table 4 (regional totals, S3) --------------------------------------------
    r3 = regional_requirements(p, regions, "S3")
    t4 = {"Riyadh": (236850, 28422), "Makkah": (218151, 26179), "Eastern Province": (137124, 16455),
          "Madinah": (59213, 7106), "Qassim": (38644, 4638), "Aseer": (48617, 5834),
          "Tabuk": (21816, 2618), "Hail": (17453, 2095), "Northern Borders": (8103, 973),
          "Jazan": (36774, 4413), "Najran": (13090, 1571), "Al Baha": (8727, 1048),
          "Al Jouf": (11843, 1422)}
    for reg, (ac, dc) in t4.items():
        row = r3.set_index("region").loc[reg]
        chk(f"Table 4 {reg} AC (S3)", row["n_AC"], ac, 0)
        chk(f"Table 4 {reg} DC (S3)", row["n_DC"], dc, 0)

    # Table 5 -----------------------------------------------------------------
    cgi = coverage_gap_index(p, r3)
    cgi.to_csv(RES / "table5_cgi_S3.csv", index=False)
    cgi_threshold_sensitivity(p, cgi).to_csv(RES / "cgi_threshold_sensitivity.csv", index=False)
    t5 = {"Riyadh": 1.04, "Makkah": 0.98, "Eastern Province": 1.12, "Madinah": 1.01, "Qassim": 1.04,
          "Aseer": 0.90, "Tabuk": 0.95, "Hail": 0.98, "Northern Borders": 0.79, "Jazan": 0.84,
          "Najran": 0.88, "Al Baha": 0.78, "Al Jouf": 0.81}
    for reg, v in t5.items():
        chk(f"Table 5 CGI {reg}", cgi.set_index("region").loc[reg, "cgi"], v, 0.005)
    chk("Table 5 number of underserved regions", (cgi["status"] == "Underserved").sum(), 5, 0)

    # Table 6 -----------------------------------------------------------------
    oat = oat_sensitivity(p, regions)
    oat.to_csv(RES / "table6_oat_sensitivity_S2.csv", index=False)
    t6 = {"alpha_public": (-30.0, 30.0), "D_annual": (-30.0, 30.0), "eta": (-30.0, 30.0),
          "U_AC": (38.3, -20.6), "U_DC": (4.6, -2.5), "w1": (0, 0), "w2": (0, 0)}
    for name, (m, pl) in t6.items():
        row = oat.set_index("parameter").loc[name]
        chk(f"Table 6 {name} -30 % (dN %)", row["dN_minus_pct"], m, 0.05)
        chk(f"Table 6 {name} +30 % (dN %)", row["dN_plus_pct"], pl, 0.05)

    # Section 4.3 beta --------------------------------------------------------
    b = beta_sensitivity(p, regions)
    chk("Sec 4.3 beta=0.92 increase (%)", b["increase_pct"], 8.7, 0.05)
    chk("Sec 4.3 beta=0.92 N_S4 (million)", b["N_S4_beta"] / 1e6, 1.34, 0.005)

    # Section 4.8 investment and peak load -------------------------------------
    cp = capex_and_peak(p, regions)
    pd.DataFrame([cp]).to_csv(RES / "sec4-8_capex_peak_S4.csv", index=False)
    chk("Sec 4.8 equipment CAPEX (bn USD)", cp["capex_equipment_busd"], 7.4, 0.05)
    chk("Sec 4.8 installed CAPEX (bn USD)", cp["capex_installed_busd"], 15.3, 0.05)
    chk("Sec 4.8 CAPEX per year low (bn USD)", cp["capex_per_year_busd_low"], 0.6, 0.05)
    chk("Sec 4.8 CAPEX per year high (bn USD)", cp["capex_per_year_busd_high"], 1.3, 0.05)
    chk("Sec 4.8 average load (GW)", cp["avg_load_gw"], 1.98, 0.005)
    chk("Sec 4.8 installed capacity (GW)", cp["installed_capacity_gw"], 14.5, 0.05)
    chk("Sec 4.8 coincident peak (GW)", cp["coincident_peak_gw"], 3.0, 0.05)
    chk("Sec 5 annual AC installations", cp["annual_installs_AC"], 91500, 50)
    chk("Sec 5 annual DC installations", cp["annual_installs_DC"], 11000, 50)

    # Section 4.6 LCOC ---------------------------------------------------------
    lc = lcoc_sensitivity(p)
    lc.to_csv(RES / "sec4-6_lcoc_sensitivity.csv", index=False)
    lci = lc.set_index("case")["lcoc_sar"]
    chk("Sec 4.6 LCOC baseline (SAR/kWh)", lci["baseline"], 1.42, 0.005)
    chk("Sec 4.6 LCOC tariff -30 %", lci["tariff x0.7"], 1.37, 0.005)
    chk("Sec 4.6 LCOC tariff +30 %", lci["tariff x1.3"], 1.47, 0.005)
    chk("Sec 4.6 LCOC U_DC -30 %", lci["U_DC x0.7"], 1.95, 0.005)
    chk("Sec 4.6 LCOC U_DC +30 %", lci["U_DC x1.3"], 1.13, 0.005)

    # Section 4.8 payback ------------------------------------------------------
    pb = pd.DataFrame([payback(p, "DC"), payback(p, "DC", 0.18), payback(p, "AC")])
    pb.to_csv(RES / "sec4-8_payback.csv", index=False)
    chk("Sec 4.8 DC net revenue (USD/yr)", pb.loc[0, "net_revenue_usd"], 21400, 50)
    chk("Sec 4.8 DC payback (yr)", pb.loc[0, "payback_years"], 2.1, 0.05)
    chk("Sec 4.8 DC payback U=0.18 (yr)", pb.loc[1, "payback_years"], 1.4, 0.05)
    chk("Sec 4.8 AC payback (yr)", pb.loc[2, "payback_years"], 2.2, 0.05)

    # Table 8 -----------------------------------------------------------------
    t8 = regional_npv_irr(p, regions)
    t8.to_csv(RES / "table8_regional_npv_irr_S3.csv", index=False)
    chk("Table 8 aggregate NPV (bn USD)", t8["npv_musd"].sum() / 1e3, 30.0, 0.05)
    chk("Table 8 minimum IRR (%)", t8["irr_pct"].min(), 34.8, 0.05)
    chk("Table 8 maximum IRR (%)", t8["irr_pct"].max(), 51.8, 0.05)
    chk("Table 8 regions with positive NPV", (t8["npv_musd"] > 0).sum(), 13, 0)

    # Scenario S5 ---------------------------------------------------------------
    s5 = pv_s5(p)
    pd.DataFrame([s5]).to_csv(RES / "sec4-8_scenario_S5_pv.csv", index=False)
    chk("S5 PV generation (kWh/yr)", s5["pv_generation_kwh"], 97200, 50)
    chk("S5 LCOC (SAR/kWh)", s5["lcoc_sar"], 1.23, 0.005)
    chk("S5 annual net revenue (USD)", s5["annual_net_usd"], 22800, 50)
    chk("S5 NPV per station (USD)", s5["npv_usd"], 67500, 100)
    chk("S5 IRR (%)", s5["irr_pct"], 17, 0.5)
    chk("S5 fleet investment (M USD)", s5["fleet_capex_musd"], 310, 0.5)
    chk("S5 fleet NPV (M USD)", s5["fleet_npv_musd"], 165, 0.5)

    # Station-level allocation (needs the processed station dataset) ----------
    station_note = ""
    if STATIONS.exists():
        st = pd.read_csv(STATIONS)
        all_ok = True
        for s in p["demand"]["scenarios"]:
            req = regional_requirements(p, regions, s)
            alloc = allocate_stations(st, req, p)
            alloc.to_csv(RES / f"station_allocation_{s}.csv", index=False)
            tot = check_totals(alloc, req)
            tot.to_csv(RES / f"station_allocation_totals_check_{s}.csv", index=False)
            ok = bool(tot[["n_AC_match", "n_DC_match", "n_total_match"]].all().all())
            all_ok &= ok
            chk(f"Station allocation {s}: national total preserved", alloc["n_total"].sum(),
                req["n_total"].sum(), 0)
            inten = (alloc.groupby("region")["n_total"].sum() / alloc.groupby("region").size())
            inten.rename("chargers_per_mapped_station").to_csv(RES / f"station_intensity_{s}.csv")
        station_note = ("Station-level allocation run on "
                        f"{len(st):,} stations; regional totals preserved in every region: {all_ok}.")
    else:
        station_note = ("data/processed/stations_classified.csv not found: station-level "
                        "allocation skipped (see data/processed/README.md).")

    # Report -------------------------------------------------------------------
    lines = ["# Verification against the revised manuscript", "",
             "Generated by `python/reproduce_all.py`. Each row compares a value reproduced "
             "from `params/model_parameters.yaml` and `data/regional_inputs.csv` with the value "
             "printed in the manuscript (rounded as printed).", "",
             "| Quantity | Reproduced | Manuscript | Result |", "|---|---:|---:|:---:|"]
    n_pass = 0
    for label, val, rep, tol in checks:
        ok = abs(val - rep) <= tol + 1e-9
        n_pass += ok
        fmt = (lambda v: f"{v:,.0f}") if abs(rep) >= 1000 else (lambda v: f"{v:,.3f}")
        lines.append(f"| {label} | {fmt(val)} | {fmt(rep)} | {'PASS' if ok else 'CHECK'} |")
    lines += ["", f"**{n_pass} of {len(checks)} checks pass.**", "", station_note, ""]
    (RES / "verification_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{n_pass}/{len(checks)} checks pass. {station_note}")
    return 0 if n_pass == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

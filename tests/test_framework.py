"""Unit tests: run with `pytest -q` from the repository root."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from ev_planning.allocation import allocate_region, allocate_stations, check_totals  # noqa: E402
from ev_planning.model import (charger_annual_energy_kwh, load_params, load_regions,  # noqa: E402
                               national_summary, regional_requirements)

P, R = load_params(), load_regions()


def test_charger_energy_worked_example():
    # Section 3.2.3 worked example
    assert round(charger_annual_energy_kwh(P, "DC")) == 52560
    assert round(charger_annual_energy_kwh(P, "AC")) == 9461


def test_table3_totals():
    nat = national_summary(P, R).set_index("scenario")["n_total"].to_dict()
    assert nat == {"S1": 368921, "S2": 614863, "S3": 959179, "S4": 1229712}


def test_ceiling_adds_at_most_26_units():
    for s in P["demand"]["scenarios"]:
        r = regional_requirements(P, R, s)
        exact = sum(r["e_public_kwh"] * P["chargers"][c]["demand_share"]
                    / charger_annual_energy_kwh(P, c) for c in ("AC", "DC")).sum()
        assert 0 <= r["n_total"].sum() - exact <= 26


def test_allocation_preserves_total_and_min_coverage():
    rng = np.random.default_rng(0)
    for _ in range(500):
        n = int(rng.integers(1, 80))
        w = rng.random(n) ** 3                       # skewed weights create many small shares
        pred = rng.random(n) < 0.6
        total = int(rng.integers(0, 400))
        counts, log = allocate_region(w, pred, total)
        assert counts.sum() == total and (counts >= 0).all()
        if total >= 2 * n:                           # enough units: every predominant station covered
            assert (counts[pred] >= 1).all()


def _toy_stations():
    rng = np.random.default_rng(1)
    rows = []
    for reg in R["region"]:
        for i in range(int(rng.integers(5, 40))):
            rows.append({"station_id": f"{reg[:3]}-{i}", "region": reg,
                         "station_class": rng.choice(["urban", "peri-urban", "highway", "remote"]),
                         "pop_density": rng.lognormal(3, 1.5),
                         "dist_highway_km": rng.exponential(15)})
    return pd.DataFrame(rows)


def test_station_allocation_matches_regional_and_national_totals():
    st = _toy_stations()
    for s in P["demand"]["scenarios"]:
        req = regional_requirements(P, R, s)
        alloc = allocate_stations(st, req, P)
        chk = check_totals(alloc, req)
        assert chk[["n_AC_match", "n_DC_match", "n_total_match"]].all().all()
        assert alloc["n_total"].sum() == req["n_total"].sum()

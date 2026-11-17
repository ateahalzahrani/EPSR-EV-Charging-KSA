# Reviewer comments addressed in this repository

| Comment | Request | Where it is addressed |
|---|---|---|
| R5-C10 | Make the MATLAB scripts, processed station dataset, parameter files and allocation procedure available in a public repository; verify internal numerical consistency | `matlab/original/`, `matlab/reference/`, `data/processed/`, `params/`, `docs/allocation_algorithm.md`; `results/verification_report.md` recomputes 101 published values from the inputs |
| R1-C3, R5-C4 | Units of `U_c`; transparent derivation of ≈1.23 million chargers | `params/model_parameters.yaml` (U dimensionless), `model.charger_annual_energy_kwh`, `tests/test_framework.py::test_charger_energy_worked_example`, `results/table3_national_requirements.csv` |
| R1-C4, R5-C5 | Implementation order of rounding, rebalancing and minimum coverage; pseudocode or flowchart; proof that regional and national totals are preserved | `docs/allocation_algorithm.md`, `python/ev_planning/allocation.py`, `matlab/reference/allocate_region.m`, `allocation.check_totals`, `results/station_allocation_totals_check_S*.csv` |
| R1-C1, R5-C1 | Which station dataset is used at each stage; quality-control steps | `docs/workflow.md` steps 1–5, `python/osm_extract_dedup.py`, `data/processed/README.md` |
| R5-C2 | Procedure for regional vehicle stock | `data/regional_inputs.csv`, `docs/workflow.md`; charger requirement is linear in stock (`tests/`) |
| R1-C2, R5-C3 | Effect of `D_annual`, `η`, `α_public` | `results/table6_oat_sensitivity_S2.csv`; any value can be changed in `params/` and rerun |
| R1-C5, R5-C8 | CGI bands, Najran classification, threshold sensitivity | `model.coverage_gap_index`, `results/table5_cgi_S3.csv`, `results/cgi_threshold_sensitivity.csv` |
| R5-C6 | MCDA weights and their effect | `params/model_parameters.yaml` (`allocation`), `results/table6_oat_sensitivity_S2.csv` (w1, w2: 0 % on national total) |
| R5-C7 | Classification rules and thresholds | `params/classification.yaml`, `python/ev_planning/classification.py`, `matlab/original/` |
| R1-C6, R5-C9 | Derivation of investment (USD 7.4–15.3 bn) and peak load (≈3.0 GW); Table 8 inputs | `analysis.capex_and_peak`, `analysis.regional_npv_irr`, `results/sec4-8_capex_peak_S4.csv`, `results/table8_regional_npv_irr_S3.csv` |

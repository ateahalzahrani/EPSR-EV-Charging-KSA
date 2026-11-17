# EPSR-EV-Charging-KSA

Code, data and parameter files for

> **Ateyah Alzahrani.** *Planning Electric Vehicle Charging Infrastructure: A Data-Driven Framework for Saudi Arabia's Transition.* Manuscript EPSR-D-26-08185, submitted to *Electric Power Systems Research* (revised version, November 2026).

The repository contains everything needed to rerun the framework, from the OpenStreetMap fuel-station extract through regional demand, charger sizing, station-level allocation, the Coverage Gap Index, the sensitivity analysis and the techno-economic estimates. Running one script recomputes **all regional and national figures in Tables 3–6 and 8 and in Sections 4.3, 4.6 and 4.8** and checks them against the values printed in the paper.

[![tests](https://github.com/ateahalzahrani/EPSR-EV-Charging-KSA/actions/workflows/tests.yml/badge.svg)](https://github.com/ateahalzahrani/EPSR-EV-Charging-KSA/actions/workflows/tests.yml)

---

## Quick start

```bash
git clone https://github.com/ateahalzahrani/EPSR-EV-Charging-KSA.git
cd EPSR-EV-Charging-KSA
pip install -r requirements.txt
python python/reproduce_all.py      # writes results/*.csv and results/verification_report.md
pytest -q                           # unit tests (totals preserved, worked examples)
```

MATLAB or GNU Octave:

```matlab
cd matlab/reference
run_all          % prints Tables 3, 4 (regional totals), 5 and 6 and runs the station allocation
```

Result of the current version: **101 of 101 checks pass** – see [`results/verification_report.md`](results/verification_report.md).

---

## Repository layout

| Path | Contents |
|---|---|
| `params/model_parameters.yaml` | Every model parameter with its baseline value and source (Table 2, Sections 3.2–4.8) |
| `params/classification.yaml` | Highway keyword list and thresholds of the station classification, Equation (1) |
| `data/regional_inputs.csv` | Population, area, light-duty vehicle stock and fuel-station estimate for the 13 regions (Table 1) |
| `data/raw/overpass_query.ql` | Overpass API query used to extract `amenity=fuel` features |
| `data/processed/` | Deduplicated, region-assigned and classified station dataset (4,464 stations) – see its README |
| `python/ev_planning/model.py` | Equations (2)–(7) and (10): EV stock, energy, public energy, charger sizing, CGI |
| `python/ev_planning/allocation.py` | Equations (8)–(9) with rounding, regional rebalancing and minimum coverage |
| `python/ev_planning/classification.py` | Equation (1) and the Haversine distance |
| `python/ev_planning/analysis.py` | One-at-a-time sensitivity, β sensitivity, LCOC, payback, Table 8 NPV/IRR, Scenario S5 |
| `python/osm_extract_dedup.py` | OSM download, 110 m de-duplication and point-in-polygon assignment |
| `python/reproduce_all.py` | Recomputes all results and writes the verification report |
| `matlab/original/` | The authors' original MATLAB scripts used to produce the figures in the paper |
| `matlab/reference/` | Compact MATLAB/Octave implementation of Equations (2)–(10), tested in GNU Octave |
| `results/` | Reproduced tables as CSV and `verification_report.md` |
| `docs/workflow.md` | Step-by-step workflow from raw data to results |
| `docs/allocation_algorithm.md` | Pseudocode and flowchart of the station-level allocation |
| `docs/reviewer_response_map.md` | Where each reproducibility-related reviewer comment is addressed in this repository |
| `tests/` | Unit tests |

---

## Model summary

| Step | Equation | Implementation |
|---|---|---|
| Station class (urban, peri-urban, highway, remote) | (1) `Class_s = f(Pop_city, Keyword_s, Dist_highway,s)` | `classification.py`, `params/classification.yaml` |
| EV stock | (2) `EVs_r,k = Fleet_r × Penetration_k` | `model.regional_requirements` |
| Annual energy | (3) `E_annual = EVs × D_annual × η` | 〃 |
| Public energy | (4) `E_public = E_annual × α_public` | 〃 |
| Energy per charger | (5) `E_charger,c = P_c × U_c × β × 8760` | `model.charger_annual_energy_kwh` |
| Regional chargers | (6)–(7) `N_c,r,k = ⌈E_public × σ_c / E_charger,c⌉` | `model.regional_requirements` |
| Station weight | (8) `w_s = w1·D̂_s + w2·R̂_s + w3·T_s` | `allocation.composite_weights` |
| Station share | (9) `N_c,s,k = N_c,r,k × w_s / Σ w_s` + post-processing | `allocation.allocate_region` |
| Coverage Gap Index | (10) `CGI_r = (N_r/ΣN) / (Pop_r/ΣPop)` | `model.coverage_gap_index` |

**Units.** `U_c` is a dimensionless average power-utilisation (load) factor: mean delivered power divided by rated power over 8,760 h. With `U_AC = 0.15` and `U_DC = 0.12`, Equation (5) gives 9,461 kWh/yr per AC Level 2 charger and 52,560 kWh/yr per 50 kW DC charger.

**Worked example (S4).** Public demand 17,312.4 GWh/yr → `N_AC = 0.60 × 17,312.4×10⁶ / 9,461 ≈ 1.098 M`, `N_DC = 0.40 × 17,312.4×10⁶ / 52,560 ≈ 0.132 M`, total ≈ 1.23 M chargers (`results/table3_national_requirements.csv`).

**Which station dataset is used where.** The 4,466-record inventory is used only for the coverage statistics (Table 7); the 4,464 region-assigned stations for classification, station-level allocation and the CGI; the 7,225–10,000 national estimate only to scale station densities. Regional charger totals come from vehicle stock and do not depend on the station count.

**Station-level allocation.** Regional totals are fixed by Equations (5)–(7) *before* allocation. The allocation only distributes each regional total among that region's stations, and the code asserts that the station counts sum exactly to the regional total for every region, scenario and charger type (see [`docs/allocation_algorithm.md`](docs/allocation_algorithm.md)). Station-level counts are relative siting priorities, not site designs: very high values (for example Jazan under S4) indicate that extra sites such as unmapped stations, car parks and workplaces are needed.

---

## Reproducing a figure or table

| Paper item | Output file |
|---|---|
| Table 3 – national requirement S1–S4 | `results/table3_national_requirements.csv` |
| Table 4 – regional AC/DC totals, S3 | `results/regional_requirements_S1-S4.csv` |
| Table 5 – CGI and status, S3 | `results/table5_cgi_S3.csv`, `results/cgi_threshold_sensitivity.csv` |
| Table 6 – OAT sensitivity, S2 | `results/table6_oat_sensitivity_S2.csv` |
| Section 4.3 – β = 0.92 | `results/verification_report.md` |
| Section 4.6 – LCOC sensitivity | `results/sec4-6_lcoc_sensitivity.csv` |
| Section 4.8 – investment and peak load | `results/sec4-8_capex_peak_S4.csv` |
| Section 4.8 – payback | `results/sec4-8_payback.csv` |
| Table 8 – regional NPV and IRR, S3 | `results/table8_regional_npv_irr_S3.csv` |
| Section 4.8 – Scenario S5 (PV + BESS) | `results/sec4-8_scenario_S5_pv.csv` |
| Station-level allocation S1–S4 | `results/station_allocation_S*.csv` (written when the station file is present) |

To test a different assumption, edit `params/model_parameters.yaml` and rerun `python/reproduce_all.py`; the report will show which published values change.

---

## Data sources and licences

* **Code:** MIT licence ([`LICENSE`](LICENSE)).
* **Station data:** derived from OpenStreetMap, © OpenStreetMap contributors, available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/). Any redistribution of `data/processed/` must keep this attribution and licence.
* **Regional inputs and parameters:** compiled by the author from GASTAT (population, 2024), the Ministry of Transport and Logistic Services (vehicle stock) and the sources cited in the paper; released under CC BY 4.0 ([`LICENSE-DATA.md`](LICENSE-DATA.md)).
* **Administrative boundaries (ADM1):** geoBoundaries, CC BY 4.0.

## Citation

Please cite the paper and this repository (see [`CITATION.cff`](CITATION.cff)). A permanent DOI for the release is provided through Zenodo.

## Contact

Ateyah Alzahrani – Department of Mechanical and Industrial Engineering, College of Engineering and Computing, Al-Qunfudhah, Umm Al-Qura University, Makkah, Saudi Arabia – aakzahrani@uqu.edu.sa

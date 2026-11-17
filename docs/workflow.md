# Step-by-step workflow

| # | Step | Input | Tool / script | Output |
|---|---|---|---|---|
| 1 | Extract `amenity=fuel` nodes, ways and relations for Saudi Arabia | Overpass API | `data/raw/overpass_query.ql`, `python/osm_extract_dedup.py` | 4,573 raw features (4,009 nodes, 558 ways, 6 relations) |
| 2 | Reduce ways/relations to centre points; merge features closer than 110 m | step 1 | `osm_extract_dedup.deduplicate` | 4,466 stations |
| 3 | Point-in-polygon join with ADM1 boundaries (WGS 84, EPSG:4326) | step 2, geoBoundaries ADM1 | `osm_extract_dedup.assign_regions` (GeoPandas) | 4,464 stations in 13 regions, 2 unassigned |
| 4 | Haversine distance to the nearest national highway corridor; municipal population | step 3, highway layer, census | `classification.haversine_km` | `dist_highway_km`, `city_population` |
| 5 | Station typology, Equation (1) | step 4 | MATLAB (`matlab/original/`), documented in `classification.py` | `station_class` (urban 1,453; peri-urban 571; highway 22; remote 2,418) |
| 6 | Regional EV stock, energy and public energy, Equations (2)–(4) | `data/regional_inputs.csv`, `params/` | `model.regional_requirements` | `results/regional_requirements_S1-S4.csv` |
| 7 | Charger sizing, Equations (5)–(7) | step 6 | 〃 | Tables 3 and 4 |
| 8 | Station-level allocation, Equations (8)–(9) | steps 5, 7 | `allocation.allocate_stations` | `results/station_allocation_S*.csv` |
| 9 | Coverage Gap Index, Equation (10), and threshold sensitivity | step 7 | `model.coverage_gap_index` | Table 5 |
| 10 | One-at-a-time sensitivity (±30 %, S2), β = 0.92 | steps 6–7 | `analysis.oat_sensitivity`, `analysis.beta_sensitivity` | Table 6, Section 4.3 |
| 11 | Investment, peak load, LCOC, payback, regional NPV/IRR, Scenario S5 | steps 7, 9 | `analysis.*` | Sections 4.6 and 4.8, Table 8 |
| 12 | Compare every reproduced value with the manuscript | all | `python/reproduce_all.py` | `results/verification_report.md` |

Steps 6–12 run in a few seconds with `python python/reproduce_all.py` (Python ≥ 3.9) or `run_all` in `matlab/reference` (MATLAB R2019b+ or GNU Octave ≥ 6).

## Key assumptions (all editable in `params/model_parameters.yaml`)

* Scenarios S1–S4: 30 %, 50 %, 78 %, 100 % of the light-duty fleet (indicative horizons S1 2027, S2 2030, S4 2037; S3 is the mid-term case).
* `D_annual` = 18,000 km/yr, `η` = 0.20 kWh/km (includes an air-conditioning penalty), `α_public` = 0.35.
* AC Level 2: 7.2 kW, `U` = 0.15, 60 % of public energy. DC fast: 50 kW, `U` = 0.12, 40 % of public energy. `β` = 1.
* MCDA weights 0.40 / 0.30 / 0.30. CGI bands: < 0.90 underserved, 0.90–1.10 adequate, ≥ 1.10 oversupplied.
* Economics: installed CAPEX USD 8,500 (AC) and 45,000 (DC); equipment-only USD 2,500 and 35,000; tariff SAR 0.18/kWh; retail price SAR 1.80/kWh; OPEX 3 % of CAPEX per year; 15 years; 10 % discount rate; 1 USD = 3.75 SAR.

## Limitations

The results are planning-level estimates. Distribution-grid hosting capacity is not modelled, no deployment data are yet available for validation, OpenStreetMap coverage is 44.7–61.8 % of the national network with an urban mapping bias, and regional vehicle stock is apportioned from national totals because regional registration statistics are not published.

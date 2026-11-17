# Processed station dataset

Place the authors' processed station file here as **`stations_classified.csv`** (UTF-8, comma-separated, one row per station). It is the dataset used for classification, station-level allocation and the CGI (4,464 region-assigned stations).

Required columns (used by `python/reproduce_all.py` and `matlab/reference/run_all.m`):

| Column | Type | Description |
|---|---|---|
| `station_id` | text | OSM identifier, e.g. `node/123456` |
| `region` | text | One of the 13 region names exactly as in `data/regional_inputs.csv` |
| `lat`, `lon` | float | WGS 84 (EPSG:4326) coordinates |
| `station_class` | text | `urban`, `peri-urban`, `highway` or `remote` (Equation 1) |
| `pop_density` | float | Population density assigned to the station (persons/km²) |
| `dist_highway_km` | float | Haversine distance to the nearest national highway corridor (km) |

Optional columns: `name`, `brand`, `operator`, `city_population`, `tags_text`.

Expected class counts: urban 1,453; peri-urban 571; highway 22; remote 2,418 (total 4,464).

Data © OpenStreetMap contributors, available under the Open Database License (ODbL) 1.0 – https://www.openstreetmap.org/copyright. The derived dataset in this folder is distributed under the same licence.

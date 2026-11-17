"""Steps (i), (ii) and (iv) of the station quality control (Section 3.1.2).

    1. download amenity=fuel features for Saudi Arabia from the Overpass API
       (nodes, ways and relations; ways/relations reduced to their centre point)
    2. topological de-duplication: features closer than 110 m are merged
       (4,573 raw features -> 4,466 stations in the paper's extract)
    3. point-in-polygon join with the ADM1 boundaries (4,464 stations inside the
       13 regional polygons; 2 left unassigned)

Usage:
    python python/osm_extract_dedup.py --boundaries data/raw/SAU_ADM1.geojson \
        --out data/processed/stations_dedup.csv [--raw data/raw/osm_fuel_raw.json]

OpenStreetMap changes continuously, so a fresh download will not return exactly
4,573 features. The snapshot used in the paper is the file supplied in
data/processed/ (see data/processed/README.md); this script documents how it
was produced and lets the procedure be repeated on a new snapshot.
Requires: requests, geopandas, shapely, numpy, pandas.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
QUERY = Path(__file__).resolve().parents[1] / "data" / "raw" / "overpass_query.ql"
DEDUP_THRESHOLD_M = 110.0


def download(raw_path: Path) -> dict:
    import requests
    r = requests.post(OVERPASS_URL, data={"data": QUERY.read_text()}, timeout=600)
    r.raise_for_status()
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(r.text, encoding="utf-8")
    return r.json()


def to_points(osm: dict) -> pd.DataFrame:
    rows = []
    for el in osm["elements"]:
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        tags = el.get("tags", {})
        rows.append({"osm_type": el["type"], "osm_id": el["id"], "lat": lat, "lon": lon,
                     "name": tags.get("name", ""), "name_ar": tags.get("name:ar", ""),
                     "brand": tags.get("brand", ""), "operator": tags.get("operator", ""),
                     "addr": " ".join(v for k, v in tags.items() if k.startswith("addr:"))})
    return pd.DataFrame(rows)


def deduplicate(df: pd.DataFrame, threshold_m: float = DEDUP_THRESHOLD_M) -> pd.DataFrame:
    """Greedy clustering: keep a feature unless it lies within threshold_m of one already
    kept. Nodes are preferred over ways/relations, and tagged features over untagged."""
    from sklearn.neighbors import BallTree  # haversine metric

    order = df.assign(_pri=df["osm_type"].map({"node": 0, "way": 1, "relation": 2}),
                      _tag=(df[["name", "brand", "operator"]] == "").sum(axis=1))
    order = order.sort_values(["_tag", "_pri"]).reset_index(drop=True)
    coords = np.radians(order[["lat", "lon"]].to_numpy())
    tree = BallTree(coords, metric="haversine")
    radius = threshold_m / 6371008.8
    removed = np.zeros(len(order), bool)
    for i in range(len(order)):
        if removed[i]:
            continue
        nbrs = tree.query_radius(coords[i:i + 1], r=radius)[0]
        removed[nbrs[nbrs > i]] = True
    return order.loc[~removed].drop(columns=["_pri", "_tag"]).reset_index(drop=True)


def assign_regions(df: pd.DataFrame, boundaries: Path, name_field: str = "shapeName") -> pd.DataFrame:
    import geopandas as gpd
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
    adm = gpd.read_file(boundaries).to_crs("EPSG:4326")[[name_field, "geometry"]]
    out = gpd.sjoin(pts, adm, how="left", predicate="within")
    return pd.DataFrame(out.drop(columns=["geometry", "index_right"])).rename(columns={name_field: "region"})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=Path("data/raw/osm_fuel_raw.json"))
    ap.add_argument("--boundaries", type=Path, required=True, help="ADM1 polygons (GeoJSON/shapefile)")
    ap.add_argument("--out", type=Path, default=Path("data/processed/stations_dedup.csv"))
    a = ap.parse_args()
    osm = json.loads(a.raw.read_text(encoding="utf-8")) if a.raw.exists() else download(a.raw)
    raw = to_points(osm)
    ded = deduplicate(raw)
    reg = assign_regions(ded, a.boundaries)
    reg.to_csv(a.out, index=False)
    print(f"raw features: {len(raw):,} | after {DEDUP_THRESHOLD_M:.0f} m de-duplication: {len(ded):,} "
          f"| inside regional polygons: {reg['region'].notna().sum():,}")


if __name__ == "__main__":
    main()

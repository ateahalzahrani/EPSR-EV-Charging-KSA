"""Station typology (Equation 1) and great-circle distance.

Class_s = f(Pop_city, Keyword_s, Dist_highway,s)

The processed station file in data/processed/ already carries the class labels
produced by the authors' MATLAB classification, and those labels are the ones
used in the paper. This module documents the rule so it can be re-run or
modified. Keyword list and thresholds are read from params/classification.yaml.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km (vectorised)."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def distance_to_polyline_km(lat, lon, line_lat, line_lon):
    """Approximate distance from points to the vertices of a densified highway polyline."""
    lat = np.asarray(lat, float)[:, None]
    lon = np.asarray(lon, float)[:, None]
    d = haversine_km(lat, lon, np.asarray(line_lat)[None, :], np.asarray(line_lon)[None, :])
    return d.min(axis=1)


def load_rules(path: str | Path | None = None) -> dict:
    path = Path(path) if path else ROOT / "params" / "classification.yaml"
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def keyword_indicator(text: str, terms: list[str]) -> int:
    """Keyword_s: 1 if the name/address tags contain a highway-related term, else 0."""
    if not isinstance(text, str) or not text:
        return 0
    pattern = "|".join(re.escape(t) for t in terms)
    return int(re.search(pattern, text, flags=re.IGNORECASE) is not None)


def classify(stations: pd.DataFrame, rules: dict) -> pd.Series:
    """Equation (1). Requires columns: tags_text, city_population, dist_highway_km."""
    kw = stations["tags_text"].apply(lambda t: keyword_indicator(t, rules["highway_terms"]))
    pop = stations["city_population"].fillna(0)
    dist = stations["dist_highway_km"].fillna(math.inf)
    cls = np.where(pop >= rules["urban_min_city_population"], "urban",
          np.where(pop >= rules["periurban_min_city_population"], "peri-urban", "remote"))
    highway = (kw == 1) & (dist <= rules["highway_max_distance_km"])
    cls = np.where(highway, "highway", cls)
    return pd.Series(cls, index=stations.index, name="station_class")

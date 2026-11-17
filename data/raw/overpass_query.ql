/* OpenStreetMap fuel stations in Saudi Arabia (amenity=fuel), Overpass QL.
   Run at https://overpass-turbo.eu or via python/osm_extract_dedup.py.
   Data (c) OpenStreetMap contributors, ODbL 1.0. */
[out:json][timeout:600];
area["ISO3166-1"="SA"][admin_level=2]->.sa;
(
  node["amenity"="fuel"](area.sa);
  way["amenity"="fuel"](area.sa);
  relation["amenity"="fuel"](area.sa);
);
out center tags;

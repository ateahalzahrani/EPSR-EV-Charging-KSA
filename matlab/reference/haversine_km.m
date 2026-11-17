function d = haversine_km(lat1, lon1, lat2, lon2)
%HAVERSINE_KM Great-circle distance (km) between points given in degrees.
R = 6371.0088;
lat1 = deg2rad(lat1); lat2 = deg2rad(lat2);
dlat = lat2 - lat1;   dlon = deg2rad(lon2 - lon1);
a = sin(dlat/2).^2 + cos(lat1).*cos(lat2).*sin(dlon/2).^2;
d = 2 * R * asin(sqrt(a));
end

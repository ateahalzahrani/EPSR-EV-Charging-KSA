function ws = composite_weight(pop_density, dist_highway_km, station_class, p, ctype)
%COMPOSITE_WEIGHT Equation (8): w_s = w1*D_s + w2*R_s + w3*T_s (ctype 1 = AC, 2 = DC).
mm = @(v) (v - min(v)) / max(max(v) - min(v), eps);
D  = mm(pop_density(:));
Rp = 1 - mm(dist_highway_km(:));          % closer to a highway corridor -> higher score
T  = double(ismember(station_class(:), p.predominant{ctype}));
ws = p.w(1) * D + p.w(2) * Rp + p.w(3) * T;
end

function R = read_regions(csvfile)
%READ_REGIONS Read data/regional_inputs.csv (Table 1).
fid = fopen(csvfile, 'r');
fgetl(fid);                                           % header
C = textscan(fid, '%s %f %f %f %f %f', 'Delimiter', ',');
fclose(fid);
R.region      = C{1};
R.population  = C{2} * 1e6;
R.area_km2    = C{3} * 1e3;
R.vehicles    = C{4} * 1e3;
end

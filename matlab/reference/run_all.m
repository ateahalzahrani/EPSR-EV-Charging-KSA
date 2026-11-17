% RUN_ALL  Reference MATLAB/Octave implementation of Equations (2)-(10).
% Reproduces Tables 3, 4 (regional totals), 5 and 6 of the revised manuscript
% and, if data/processed/stations_classified.csv exists, runs the station-level
% allocation and confirms that regional and national totals are preserved.
% Run from this folder:  >> run_all
here = fileparts(mfilename('fullpath')); root = fullfile(here, '..', '..');
p = ev_params();
R = read_regions(fullfile(root, 'data', 'regional_inputs.csv'));

fprintf('\nTable 3 - national requirement\n%-4s %12s %10s %10s %10s\n', 'Scen', 'E_pub(GWh)', 'AC', 'DC', 'Total');
for k = 1:4
    S = demand_sizing(R, p, k);
    fprintf('%-4s %12.1f %10d %10d %10d\n', p.scenarios{k}, sum(S.E_public)/1e6, sum(S.N_AC), sum(S.N_DC), sum(S.N_total));
end

S3 = demand_sizing(R, p, 3);
[cgi, status] = cgi_index(S3.N_total, R.population, p.cgi_bands);
fprintf('\nTables 4-5 - Scenario S3\n%-18s %9s %8s %9s %6s %s\n', 'Region', 'AC', 'DC', 'Total', 'CGI', 'Status');
for i = 1:numel(R.region)
    fprintf('%-18s %9d %8d %9d %6.2f %s\n', R.region{i}, S3.N_AC(i), S3.N_DC(i), S3.N_total(i), cgi(i), status{i});
end

% Table 6: one-at-a-time sensitivity (Scenario S2)
fprintf('\nTable 6 - OAT sensitivity (S2)\n');
base = sum(getfield(demand_sizing(R, p, 2), 'N_total'));
names = {'alpha_public', 'D_annual', 'eta', 'U_AC', 'U_DC'};
for j = 1:numel(names)
    out = zeros(1, 2); f = [1 - p.oat_delta, 1 + p.oat_delta];
    for m = 1:2
        q = p;
        switch names{j}
            case 'U_AC', q.U(1) = q.U(1) * f(m);
            case 'U_DC', q.U(2) = q.U(2) * f(m);
            otherwise,   q.(names{j}) = q.(names{j}) * f(m);
        end
        out(m) = 100 * (sum(getfield(demand_sizing(R, q, 2), 'N_total')) - base) / base;
    end
    fprintf('%-13s %+7.1f%% %+7.1f%%\n', names{j}, out(1), out(2));
end
fprintf('w1, w2         +0.0%%   +0.0%%  (weights only redistribute fixed regional totals)\n');

% Station-level allocation (Eqs. 8-9) if the processed station file is available
sf = fullfile(root, 'data', 'processed', 'stations_classified.csv');
if exist(sf, 'file')
    fid = fopen(sf, 'r'); hdr = strsplit(fgetl(fid), ',');
    fmt = repmat({'%s'}, 1, numel(hdr));
    num = {'lat', 'lon', 'pop_density', 'dist_highway_km'};
    fmt(ismember(hdr, num)) = {'%f'};
    C = textscan(fid, strjoin(fmt, ' '), 'Delimiter', ','); fclose(fid);
    col = @(name) C{strcmp(hdr, name)};
    reg = col('region'); cls = col('station_class');
    for k = 1:4
        S = demand_sizing(R, p, k); Ntot = 0;
        for ct = 1:2
            ws = composite_weight(col('pop_density'), col('dist_highway_km'), cls, p, ct);
            if ct == 1, Nreg = S.N_AC; else, Nreg = S.N_DC; end
            for i = 1:numel(R.region)
                idx = strcmp(reg, R.region{i});
                n = allocate_region(ws(idx), ismember(cls(idx), p.predominant{ct}), Nreg(i));
                assert(sum(n) == Nreg(i));
                Ntot = Ntot + sum(n);
            end
        end
        fprintf('Station allocation %s: %d chargers allocated, national total %d (preserved)\n', ...
                p.scenarios{k}, Ntot, sum(S.N_total));
    end
else
    fprintf('\n%s not found - station-level allocation skipped.\n', sf);
end

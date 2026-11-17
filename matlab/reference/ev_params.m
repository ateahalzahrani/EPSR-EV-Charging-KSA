function p = ev_params()
%EV_PARAMS Baseline parameters of the revised manuscript (mirrors params/model_parameters.yaml).
p.scenarios     = {'S1','S2','S3','S4'};
p.penetration   = [0.30 0.50 0.78 1.00];   % Penetration_k, Eq. (2)
p.D_annual      = 18000;                   % km/yr, Eq. (3)
p.eta           = 0.20;                    % kWh/km, Eq. (3)
p.alpha_public  = 0.35;                    % Eq. (4)
p.P             = [7.2 50];                % rated power [AC DC], kW, Eq. (5)
p.U             = [0.15 0.12];             % dimensionless power-utilisation factor
p.sigma         = [0.60 0.40];             % share of public energy by type, Eq. (6)
p.beta          = 1.0;                     % availability coefficient
p.hours         = 8760;
p.w             = [0.40 0.30 0.30];        % w1 (density), w2 (road proximity), w3 (typology), Eq. (8)
p.predominant   = {{'urban','peri-urban'}, {'highway','remote'}};   % AC, DC
p.cgi_bands     = [0.90 1.10];             % underserved < 0.90 <= adequate < 1.10 <= oversupplied
p.oat_delta     = 0.30;                    % one-at-a-time perturbation
end

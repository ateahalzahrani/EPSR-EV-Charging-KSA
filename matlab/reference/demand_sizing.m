function S = demand_sizing(R, p, k)
%DEMAND_SIZING Equations (2)-(7) for scenario index k (1..4). Returns per-region vectors.
S.ev        = R.vehicles * p.penetration(k);                  % Eq. (2)
S.E_annual  = S.ev * p.D_annual * p.eta;                      % Eq. (3), kWh/yr
S.E_public  = S.E_annual * p.alpha_public;                    % Eq. (4), kWh/yr
E_charger   = p.P .* p.U * p.beta * p.hours;                  % Eq. (5), kWh/yr per charger
S.E_charger = E_charger;
S.N_AC      = ceil(S.E_public * p.sigma(1) / E_charger(1) - 1e-9);   % Eq. (6)
S.N_DC      = ceil(S.E_public * p.sigma(2) / E_charger(2) - 1e-9);
S.N_total   = S.N_AC + S.N_DC;                                % Eq. (7)
end

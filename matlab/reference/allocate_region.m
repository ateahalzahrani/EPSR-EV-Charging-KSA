function n = allocate_region(w, is_pred, total)
%ALLOCATE_REGION Station-level allocation for one region and charger type (Section 3.2.4).
%   w       composite weights w_s of the stations in the region (Eq. 8)
%   is_pred logical, true where the station class is predominant for this charger type
%   total   regional total N_c,r,k from Eq. (6)
% Steps: proportional share (Eq. 9) -> round -> rebalance to the regional total by
% largest remainder -> minimum coverage (one unit to every predominant station left
% at zero, each unit taken from the station holding the most units). sum(n) == total.
w = w(:); is_pred = logical(is_pred(:)); ns = numel(w);
n = zeros(ns, 1);
if ns == 0 || total == 0, return; end
if sum(w) > 0, x = total * w / sum(w); else, x = total * ones(ns,1) / ns; end   % Eq. (9)
n = floor(x + 0.5);                                   % integer rounding
d = total - sum(n);  rem = x - n;                     % regional rebalancing
if d > 0
    [~, o] = sort(-rem); n(o(1:d)) = n(o(1:d)) + 1;
elseif d < 0
    c = find(n > 0); [~, o] = sort(rem(c)); n(c(o(1:-d))) = n(c(o(1:-d))) - 1;
end
need = find(is_pred & n == 0);                        % minimum coverage
[~, o] = sort(-w(need)); need = need(o);
for i = 1:numel(need)
    [mx, donor] = max(n);
    if mx <= 1, break; end
    n(donor) = n(donor) - 1; n(need(i)) = n(need(i)) + 1;
end
assert(sum(n) == total && all(n >= 0));
end

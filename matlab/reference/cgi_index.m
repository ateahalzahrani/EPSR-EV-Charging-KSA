function [cgi, status] = cgi_index(N_total, population, bands)
%CGI_INDEX Coverage Gap Index, Eq. (10), and classification bands (Section 3.2.5).
cgi = (N_total / sum(N_total)) ./ (population / sum(population));
status = repmat({'Adequate'}, size(cgi));
c = round(cgi * 100) / 100;
status(c <  bands(1)) = {'Underserved'};
status(c >= bands(2)) = {'Oversupplied'};
end

close all
clear all

k=7;

w = 15.1901; %change
Pdet = 0.262; %change
cfd = 0.04235;%change
%calculate area - subtract center 1.5 km



%w = 15.1901; 
%Pdet = 0.262; 
%cfd = 0.04235;

tab=readtable("All_call_ranges_interp_Brydes_dateedit.csv");
true_inds = ~isnan(tab.interp_range);
tab_true = tab(true_inds,:);
w_inds = find(tab.interp_range <= w);
tab_w =tab_true(w_inds,:);
tab_w.station_code = string(tab_w.station_code);
tab_w.month = string(tab_w.month);
stalist = unique(tab_w.station_code);




m_e = [1 (30/31) 1 (30/31) 1 1 (30/31) 1 (30/31) 1 1]

months =["March" "April" "May" "June" "July" "August" "September" "October" "November" "December" "January"];

n = []; %change

%n = [2250 780 530 221 1455 2975 3795 6613 5134 338 0]; %actual total n

totaldense = n.*(1-cfd)./(pi.*w.^2.*Pdet.*k.*m_e);

cv_pdet = [];%change

%cv_pdet = [0.006744882 0.006744882 0.006744882 0.006744882 0.006744882 0.006744882 0.006744882 0.006744882 0.006744882 0.006744882 0.006744882];

cv_encounter_rate = zeros(1,length(n))

n_mat = zeros(length(stalist),length(m_e))

for m = 1:11
    
    for sta = 1:length(stalist)
        n_sta_m_inds = find(tab_w.station_code == stalist(sta) & tab_w.month == months(m))
        n_mat(sta,m) = length(n_sta_m_inds)
        
    end
    
   
    cv_encounter_rate(m) = sqrt((k/(n(m).^2*(k-1)))*sum((n_mat(:,m) - n(m)/k).^2))
   
    
end


%%
%These values from r are incorrect because they are using the wrong number
%of transects! See summary statistics!
totaldense_r = [1.9847782 0.8216189 0.3541070 0.2004621 1.2026070 2.4376853...
    2.8757538 4.8858761 4.0811652 0.3386329 0].*(1-0.046); %not accurate due to effort! Doesnt count stations with no detections!

cv_encounterrate_r = [0.1497550 0.2552538 0.3720922 0.2341164 0.3828036 0.1500603...
    0.2460888 0.3091441 0.1988895 0.2451162 0];

cv_dense_r = [0.1240917 0.2711229 0.3176298 0.2395763 0.4029526 0.2296660...
    0.2416668 0.2743178 0.2314419 0.1927238 0];
%%

cv_dense_calc = sqrt(cv_pdet.^2 + cv_encounter_rate.^2);

se_dense = totaldense.*cv_dense_calc;
c= exp(1.96.*sqrt(log(1+(cv_dense_calc.^2))))
lcl = totaldense./c
ucl = totaldense.*c

figure(13)
hold on

redc = [0.8660 0.3290 0.0000];
yellowc = [0.9290 0.6940 0.1250];
bluec = [0 0.4470 0.7410];



scatter([1 2 3 4 5 6 7 8 9 10 11],totaldense,150,bluec,'filled',"square")


scatter([1 2 3 4 5 6 7 8 9 10 11],lcl,500, bluec,"Marker",'_',"Linewidth",2)
scatter([1 2 3 4 5 6 7 8 9 10 11],ucl,500,bluec,"Marker",'_',"Linewidth",2)

hold on

for j=1:11
    
    plot([j j],[lcl(j) ucl(j)],'k--',"Linewidth",2,"Color",bluec)
    
    
end

ax = gca;
ax.XTickLabel = {'Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan'};


set(gca,'ygrid','on')
set(gca,'fontsize',20);
ylabel("Density (Calls/km^2)")
xlabel("Month")

ylim([0 9])
xlim([0 12])

xticks([1 2 3 4 5 6 7 8 9 10 11]);
lgd = legend(["Model Estimate","95% confidence intervals"],'location','northwest')
%lgd.FontSize = 15






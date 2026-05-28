%make multi panelled histogram figure, one for each station
close all

tab=readtable('All_call_ranges_interp_Brydes.csv')
true_inds = ~isnan(tab.interp_range);
tab_true = tab(true_inds,:);
real_stas = find(tab_true.station_code ~= "B06");
tab_true = tab_true(real_stas,:);
unique_stas = unique(tab_true.station_code)

figure;

brewercolor = ["#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"];

for j=1:length(unique_stas)
    
    ax(j) = subplot(4,2,j);
    
    sta_inds = find(tab_true.station_code == string(unique_stas{j}));
    histogram(tab_true.interp_range(sta_inds),[0:1.5:25],"FaceColor",brewercolor(j),"FaceAlpha",1);
    ylim([0 1300])
    xlim([0 25])
    
    if j > 5
    xlabel('Range (km)')
    end
    
   
    if j/2 ~= floor(j/2)
        ylabel("Call Count")
    end
    
    
    
    set(gca,'ygrid','on')
    set(gca,'Fontsize',14)
    title(unique_stas(j));
    
    
    
end

%%

tab_true.month=month(tab_true.peak_time,'name');

unique_mon = ["March","April","May","June","July","August","September",...
    "October","November","December","January"];%unique(tab_true.month);
figure
brewercolor2 = ["#a6cee3","#1f78b4","#b2df8a","#33a02c","#fb9a99","#e31a1c","#ff7f00","#cab2d6","#6a3d9a","#ffff99","#fdbf6f"];


for k=1:length(unique_mon)
    
    ax(k) = subplot(4,3,k);
    m_inds = find(string(tab_true.month) == string(unique_mon(k)));
    
    h(k) = histogram(tab_true.interp_range(m_inds),[0:1.5:25],"FaceColor",brewercolor2(k),"FaceAlpha",1);
    
    set(gca,'ygrid','on')
    set(gca,'Fontsize',14)
    title(unique_mon(k));
    
    ylim([0 1400])
    xlim([0 25])
    
    if k > 8
    xlabel('Range (km)')
    end
    
    if ismember(k,[1 4 7 10])
        ylabel("Call Count")
    end
    
end

%writetable(tab_true,"All_call_ranges_interp_Brydes_dateedit.csv")

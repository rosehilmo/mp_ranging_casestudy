clear all;
close all;

%load raw autocorrelation ranging table
autotable = readtable('Marianas_auto_B19_v2.csv',Delimiter = ',');
inds = find(datetime(autotable.time,'InputFormat','yyyy-MM-dd HH:mm:ss.SSSSSS+00:00') > datetime(2012,3,1));
autotable = autotable(inds,:);


autotable.range_D_MP1(autotable.range_D_MP1 == 40) = nan; %get rid of calls that are all ranged at 40 km
autotable.range_MP1_MP2(autotable.range_MP1_MP2 == 40) = nan; 
autotable.range_MP2_MP3(autotable.range_MP2_MP3 == 40) = nan; 


autotable.groupnum = nan(height(autotable),1);
autotable.use_track = false(height(autotable),1);
autotable.supertrack = nan(height(autotable),1);
autotable.best_hypothesis = nan(height(autotable),1);

sum_calls = table2array(autotable(:,8)); %make new table for cleaned ranges
range_dmp1 = table2array(autotable(:,2));
range_dmp2 = table2array(autotable(:,3));
range_dmp3 = table2array(autotable(:,4));

count_inds = find(sum_calls >= 1);
rangeind = find(range_dmp1 < 25); %only look at D-MP1 ranges closer than 25km
%rangeind = find(range_dmp1 < 25 & range_dmp2 < 40 & range_dmp3 < 40);

verinds = intersect(count_inds, rangeind);

table_n10 = autotable(verinds,:);
range1 = table_n10(:,2);
range2 = table_n10(:,3);
range3 = table_n10(:,4);
amps = table_n10(:,7);
ncalls = table2array(table_n10(:,8));

r1=table2array(range1);
r2=table2array(range2);
r3=table2array(range3);
medamps=table2array(amps);






rangediff = r1(2:end) - r1(1:end-1); %find range differences between subsequent calls
%changeinds = find(rangediff < 3);

dates = table2array(table_n10(:,1));
fulldates = datetime(dates,'InputFormat','yyyy-MM-dd HH:mm:ss.SSSSSS+00:00');
datediff = fulldates(2:end) - fulldates(1:end-1);
%gaps = find(datediff < (datetime(1,1,2023,3,0,0)-datetime(1,1,2023,2,0,0)));

groupnum = 1;
grouparray = [1];

for j=1:length(rangediff)

    
    
    if abs(rangediff(j)) > 1.6 %if consecutive calls are more than 1.6 km apart (using D-MP1 range), make a new group
        groupnum = groupnum+1;
        grouparray = [grouparray; groupnum];
    elseif datediff(j) > (datetime(1,1,2023,3,0,0)-datetime(1,1,2023,2,0,0)) %If consecutive calls are more than 1 hour apart, make new group
        groupnum = groupnum+1;
        grouparray = [grouparray; groupnum];
    else
        grouparray = [grouparray; groupnum]; %if calls are within 1.6 km and less than 1 hour apart, group them together
    end



end



use_track = false(1,length(grouparray)).';

uniquetracks = unique(grouparray); %counts how many groups were formed

for k=1:length(uniquetracks) %checks groups for certain features

    trackinds = find(grouparray == uniquetracks(k));
    if length(trackinds) > 6 && length(find(r1(trackinds) == 0)) < .5*length(r1(trackinds)) && mean(ncalls(trackinds)) > 2 %if there are at least 6 calls in a group with an average of at least 2 calls included in each range
        use_track(trackinds) = true;                                                                                        %keep the group and search for surrounding groups to link with into tracks
    end


end


table_n10.groupnum = grouparray;
table_n10.use_track = use_track;
supertrack = nan(1,length(grouparray)).';
table_n10.supertrack = supertrack;
table_n10.best_hypothesis = nan(1,length(grouparray)).';

clustertrack = unique(grouparray(use_track)); %identify each large group that fits the parameters for linking into tracks



CM = lines(length(clustertrack));

startdist_r1 =[];
enddist_r1 = [];
startdist_r2 =[];
enddist_r2 = [];
startdist_r3 =[];
enddist_r3 = [];
starttime = [];
endtime = [];
tracknum = [];

figure(91)
clf
hold on
%plot all ranges in gray
scatter(fulldates,r1,80,[.5 .5 .5],'marker','o') 
scatter(fulldates,r2,80,[.7 .7 .7],'marker','p')
scatter(fulldates,r3,80,[.8 .8 .8],'marker','+')


%legend('MP1-D','MP2-MP1','MP3-MP2')

set(gca,'xgrid','on')
set(gca,'Fontsize',20);
set(gca,'ygrid','on')
set(gca,'LineWidth',4);
set(gca,'LineWidth',2);
ylim([0 40])
xlabel('Date')
ylabel('Range (km)')


for m=1:length(clustertrack) %find the start and end ranges of each track group

    scatterinds = find(grouparray == clustertrack(m));

    % plot(fulldates(scatterinds),r1(scatterinds),'color',CM(m,:),'marker','o')
    % plot(fulldates(scatterinds),r2(scatterinds),'color',CM(m,:),'marker','p')
    % plot(fulldates(scatterinds),r3(scatterinds),'color',CM(m,:),'marker','+')

    % plot(fulldates(scatterinds),r1(scatterinds),'color',[.8 .8 .8],'marker','o')
    % plot(fulldates(scatterinds),r2(scatterinds),'color',[.7 .7 .7],'marker','p')
    % plot(fulldates(scatterinds),r3(scatterinds),'color',[.5 .5 .5],'marker','+')

    % scatter(fulldates(scatterinds),r1(scatterinds),20,medamps(scatterinds),'marker','o')
    % scatter(fulldates(scatterinds),r2(scatterinds),20,medamps(scatterinds),'marker','p')
    % scatter(fulldates(scatterinds),r3(scatterinds),20,medamps(scatterinds),'marker','+')

    % non_nanr1 = find(~isnan(r1(scatterinds)));
    % non_nanr2 = find(~isnan(r2(scatterinds)));
    % non_nanr3 = find(~isnan(r3(scatterinds)));
    % 
    % 
    % 
    % startdist_r1 =[startdist_r1; r1(scatterinds(min(non_nanr1)))];
    % startdist_r2 =[startdist_r2; r2(scatterinds(min(non_nanr2)))];
    % startdist_r3 =[startdist_r3; r3(scatterinds(min(non_nanr3)))];
    % 
    % enddist_r1 = [enddist_r1; r1(scatterinds(max(non_nanr1)))];
    % enddist_r2 = [enddist_r2; r2(scatterinds(max(non_nanr2)))];
    % enddist_r3 = [enddist_r3; r3(scatterinds(max(non_nanr3)))];


    starttime = [starttime; fulldates(scatterinds(1))]; %make vector of start time of group
    endtime = [endtime; fulldates(scatterinds(end))];%make vector of end time of group


    startdist_r1 =[startdist_r1; median(r1(scatterinds(1:3)))]; %make vector of starting ranges of group
    startdist_r2 =[startdist_r2; median(r2(scatterinds(1:3)))];
    startdist_r3 =[startdist_r3; median(r3(scatterinds(1:3)))];

    enddist_r1 = [enddist_r1; median(r1(scatterinds(end-2:end)))]; %make vector of ending ranges of group
    enddist_r2 = [enddist_r2; median(r2(scatterinds(end-2:end)))];
    enddist_r3 = [enddist_r3; median(r3(scatterinds(end-2:end)))];
    % 
     tracknum = [tracknum; clustertrack(m)];

end


colormap jet
%colorbar





grouptimediff = starttime(2:end)-endtime(1:end-1); %find the time difference between the end of each group and start of the next one
gapinds = find(abs(grouptimediff) > (datetime(1,1,2023,5,0,0)-datetime(1,1,2023,3,0,0))); %find groups that have a larger than 2 hour difference

gapinds = [1; gapinds; length(tracknum)];

gaplengths = gapinds(2:end)- gapinds(1:end-1);

largegaps = find(gaplengths > 18); %find any very large tracks

a=0;

for g=1:length(largegaps) %Break up any very large tracks into sub-tracks to not overwhelm computation

    gapinds = [gapinds(1:largegaps(g)+a); round(mean([gapinds(largegaps(g)+a) gapinds(largegaps(g)+1+a)])); gapinds(largegaps(g)+1+a:end)];
    a=a+1;

end

%gapinds = [1; 3; 15; gapinds(3:end); length(tracknum)];
%gapinds = [1; 11; gapinds; length(tracknum)];

c=[];
h_array = [];
supertracknum = [];

for n=1:length(gapinds)-1 %for each track, test all combinations of multipath assumtions for each group and pick the combination that minimizes the root-mean-square distance between the end range of each group and start range of the next

    trackinds1=tracknum(gapinds(n):gapinds(n+1));
    startr11=startdist_r1(gapinds(n):gapinds(n+1));
    startr21=startdist_r2(gapinds(n):gapinds(n+1));
    startr31=startdist_r3(gapinds(n):gapinds(n+1));
    endr11=enddist_r1(gapinds(n):gapinds(n+1));
    endr21=enddist_r2(gapinds(n):gapinds(n+1));
    endr31=enddist_r3(gapinds(n):gapinds(n+1));

    if n == 1
        trackinds = trackinds1(1:end);
        startr1 = startr11(1:end);
        startr2 = startr21(1:end);
        startr3 = startr31(1:end);
        endr1 = endr11(1:end);
        endr2 = endr21(1:end);
        endr3 = endr31(1:end);

    else
        trackinds = trackinds1(2:end);
        startr1 = startr11(2:end);
        startr2 = startr21(2:end);
        startr3 = startr31(2:end);
        endr1 = endr11(2:end);
        endr2 = endr21(2:end);
        endr3 = endr31(2:end);

    end

    opts = [1; 2; 3];

    for y=1:length(trackinds)

        c(y).hypothesis = opts;
        c(y).start_ranges = [startr1(y); startr2(y); startr3(y)];
        c(y).end_ranges = [endr1(y); endr2(y); endr3(y)];

    end

    T_hype = combinations(c.hypothesis); %test all hypotheis and range combinations
    T_start = combinations(c.start_ranges);
    T_end = combinations(c.end_ranges);

    T_end_sub = T_end(:,1:end-1);
    T_start_sub = T_start(:,2:end);

    T_start_sub = renamevars(T_start_sub,T_start_sub.Properties.VariableNames,T_end_sub.Properties.VariableNames);

    sqrtable = (T_start_sub-T_end_sub).^2;
    %sqrtable = abs(T_start_sub-T_end_sub);

    %rmsval = table2array(median(sqrtable,2));
    rmsval = table2array(sqrt(sum(sqrtable,2)));

    [val,minind] = min(rmsval); %find combination with minimum root mean square distance between successive groups
    %[val,mininds] = sort(rmsval,"ascend");

    hypetable=T_hype(minind,:)

    if width(hypetable) == 1
        h_array=[h_array; nan]
    else

        h_array=[h_array; table2array(hypetable).']
    end

    supertracknum = [supertracknum; repmat(gapinds(n),width(hypetable),1)];


    n %distarray = nan(3^(length(trackinds)-1),length(trackinds)-1);


    clear c


end

h_array = [h_array];
supertracknum = [supertracknum];

for t = 1:length(tracknum)


table_n10.best_hypothesis(table_n10.groupnum == tracknum(t)) = h_array(t);
table_n10.supertrack(table_n10.groupnum == tracknum(t)) = supertracknum(t);


end

stracks = unique(supertracknum)



CM = lines(length(stracks));
CM1 = lines(600)

fullranges = [];

a=1;

for st = 1:length(stracks) %plot best group combinations estimated by rms in color on top of grays plotted earlier

plotinds1 = find((table_n10.supertrack == stracks(st) & table_n10.best_hypothesis == 1) == 1)
plotinds2 = find((table_n10.supertrack == stracks(st) & table_n10.best_hypothesis == 2) == 1)
plotinds3 = find((table_n10.supertrack == stracks(st) & table_n10.best_hypothesis == 3) == 1)


%plot(fulldates(plotinds1),r1(plotinds1),'color',CM(st,:),'marker','o')
%plot(fulldates(plotinds2),r2(plotinds2),'color',CM(st,:),'marker','p')
%plot(fulldates(plotinds3),r3(plotinds3),'color',CM(st,:),'marker','+')

scatter(fulldates(plotinds1),r1(plotinds1),100, CM1(a,:), 'marker','o')
scatter(fulldates(plotinds2),r2(plotinds2),100, CM1(a+2,:), 'marker','p')
scatter(fulldates(plotinds3),r3(plotinds3),100, CM1(a+1,:),'marker','+')

  %scatter(fulldates(plotinds1),r1(plotinds1),200,medamps(plotinds1),'filled','marker','o')
  %scatter(fulldates(plotinds2),r2(plotinds2),200,medamps(plotinds2),'filled','marker','p')
  %scatter(fulldates(plotinds3),r3(plotinds3),200,medamps(plotinds3),'marker','+','LineWidth',2)

 scatter(r1(plotinds1),medamps(plotinds1),'marker','o')
 scatter(r2(plotinds2),medamps(plotinds2),'marker','p')
 scatter(r3(plotinds3),medamps(plotinds3),'marker','+')

 fullranges = [fullranges; r1(plotinds1); r2(plotinds2); r3(plotinds3)];
 a=a+3

end

autotable(verinds,:) = table_n10; %save initial group estimates to new table, autotable
dates = table2array(autotable(:,1));
fulldates1 = datetime(dates,'InputFormat','yyyy-MM-dd HH:mm:ss.SSSSSS+00:00');
autotable.time = fulldates1;

%writetable(autotable,"B19_grouped_ranges.csv")



%%
%Verification of tracks
autotable_sub = [];


for tracknum = stracks.' %manually verify connected tracks make sense. The automated grouper makes mistakes, especially if there are non-whale signals or multiple singing whales
%If a likely set of groups is selected by the automated process, the
%selected hypothesis will be plotted with color representing median
%amplitudes. If there is only one group, or no likely hypothesis is
%selected, markers will all be gray and you will manually select the
%appropriate hypothesis.

    autotable_sub = autotable(autotable.supertrack == tracknum,:);
    tinds = find(autotable.supertrack == tracknum);

    groupnums = unique(autotable_sub.groupnum);

    for g = groupnums.' %check each group in the context of each larger track

        figure(65);
        clf;
        hold on;

        r1_sub = autotable_sub.range_D_MP1;
        r2_sub = autotable_sub.range_MP1_MP2;
        r3_sub = autotable_sub.range_MP2_MP3;
        datessub = autotable_sub.time;

        scatter(datessub,r1_sub,40,[.5 .5 .5],'marker','o')
        scatter(datessub,r2_sub,40,[.7 .7 .7],'marker','p')
        scatter(datessub,r3_sub,40,[.8 .8 .8],'marker','+')

        plotinds1 = find(autotable_sub.best_hypothesis == 1)
        plotinds2 = find(autotable_sub.best_hypothesis == 2)
        plotinds3 = find(autotable_sub.best_hypothesis == 3)


        scatter(datessub(plotinds1),r1_sub(plotinds1),80,medamps(plotinds1),'filled','marker','o')
        scatter(datessub(plotinds2),r2_sub(plotinds2),80,medamps(plotinds2),'filled','marker','p')
        scatter(datessub(plotinds3),r3_sub(plotinds3),80,medamps(plotinds3),'marker','+')
        colorbar

        ginds = find(autotable.groupnum == g);
        gtime = autotable.time(ginds);
        g1 = autotable.range_D_MP1(ginds);
        g2 = autotable.range_MP1_MP2(ginds);
        g3 = autotable.range_MP2_MP3(ginds);

        plot(gtime,g3,'y+-','MarkerSize',1)
        plot(gtime,g2,'mp-','MarkerSize',1)
        plot(gtime,g1,'ro-','MarkerSize',1)
        g

        figure(91)
        plot(gtime,g3,'y+-','MarkerSize',1)
        plot(gtime,g2,'mp-','MarkerSize',1)
        plot(gtime,g1,'ro-','MarkerSize',1)

        
        x = input("Is the selected hypothesis correct? 0 if yes, 1 if D-MP1, 2 if MP1-MP2, 3 if MP2-MP3, 9 if none are correct")
        if x == 0
            continue

        elseif x == 9
            autotable.best_hypothesis(ginds) = NaN;
            autotable.use_track(ginds) = false;
            autotable.supertrack(ginds) = NaN;
        else
            autotable.best_hypothesis(ginds) = x;

        end



    end


end

%writetable(autotable,"B19_grouped_ranges_corrected.csv")


%%

















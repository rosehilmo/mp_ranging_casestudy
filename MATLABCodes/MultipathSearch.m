clearvars;
close all;

%Specify Station and time:

autotable = readtable('B12_grouped_ranges_corrected.csv',Delimiter = ',');

date1 = datetime(2012,03,01);
date2 = datetime(2012,12,31);

%Filters between specified times and also for corrected ranges
searchinds = find(autotable.time > date1 & autotable.time < date2 & autotable.use_track == 1);

%Makes plot of x= time and y= ranges
redc = [0.8660 0.3290 0.0000];
yellowc = [0.9290 0.6940 0.1250];
bluec = [0 0.4470 0.7410];
blue2 = [0 0.5 1]
grayc = [.7 .7 .7];
blackc = [0 0 0]
cyan1 = [0 0.7 0.7];

hold on
scatter(autotable.time(searchinds), autotable.range_D_MP1(searchinds),80,blackc,'filled');
scatter(autotable.time(searchinds), autotable.range_MP1_MP2(searchinds),80,bluec,'filled', 'square');
scatter(autotable.time(searchinds), autotable.range_MP2_MP3(searchinds),80,cyan1,'filled', 'd');

%Modifies appearance of plot (using axes properties)
ax = gca;
ax.FontSize = 30;
ax.XGrid = "off";
ax.YGrid = "off";
ax.LineWidth = 2;
ax.YLim = [0,40];
xlabel('Date & Time')
ylabel('Range (km)')
%title('Multipath Ranges');
%Modifies appearance of data(dots)
%ax.XTickLabel = {'16:00','18:00','20:00','24:00','00:00','2:00'};

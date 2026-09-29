close all

grouped_ranges_1 = readtable('B20_grouped_ranges_corrected.csv');
grouped_ranges_1.time.TimeZone = "UTC";
grouped_ranges = grouped_ranges_1(grouped_ranges_1.use_track == 1,:);

grouped_ranges.true_range = repmat(nan,length(grouped_ranges.n_calls),1);

call_table = readtable('B20_mp.csv');
grouped_ranges_1.interp_range = repmat(nan,length(grouped_ranges_1.time),1);


call_table.end_time = datetime(call_table.end_time,'InputFormat',"yyyy-MM-dd'T'HH:mm:ss.SSSSSSZ",'TimeZone','UTC');
call_table.peak_time = datetime(call_table.peak_time,'InputFormat',"yyyy-MM-dd'T'HH:mm:ss.SSSSSSZ",'TimeZone','UTC');
call_table.start_time = datetime(call_table.start_time,'InputFormat',"yyyy-MM-dd'T'HH:mm:ss.SSSSSSZ",'TimeZone','UTC');
call_table.interp_range = repmat(nan,length(call_table.start_time),1);


plotinds1 = find(grouped_ranges.best_hypothesis == 1 & grouped_ranges.use_track == true);
plotinds2 = find(grouped_ranges.best_hypothesis == 2 & grouped_ranges.use_track == true);
plotinds3 = find(grouped_ranges.best_hypothesis == 3 & grouped_ranges.use_track == true);

grouped_ranges.true_range(plotinds1) = grouped_ranges.range_D_MP1(plotinds1);
grouped_ranges.true_range(plotinds2) = grouped_ranges.range_MP1_MP2(plotinds2);
grouped_ranges.true_range(plotinds3) = grouped_ranges.range_MP2_MP3(plotinds3);



supertrack_nums = unique(grouped_ranges.supertrack(~isnan(grouped_ranges.supertrack))).';

for j=supertrack_nums


subtable = grouped_ranges(grouped_ranges.supertrack == j,:);
   

sub_times = subtable.time;
sub_ranges = subtable.true_range;

start_time = min(sub_times);
end_time = max(sub_times);

call_inds = find(call_table.peak_time >= start_time & call_table.peak_time <= end_time);

interp_range = interp1(sub_times,sub_ranges, call_table.peak_time(call_inds)); 
 
call_table.interp_range(call_inds) = interp_range;

figure(70)
scatter(sub_times,sub_ranges,100,'filled')
hold on
scatter(call_table.peak_time(call_inds),interp_range,100,'.')


min_inds = find(grouped_ranges_1.time >= start_time & grouped_ranges_1.time <= end_time);
interp_range_min = interp1(sub_times,sub_ranges, grouped_ranges_1.time(min_inds)); 
grouped_ranges_1.interp_range(min_inds) = interp_range_min



end

%writetable(call_table,"B20_call_ranges_interp.csv")
%writetable(grouped_ranges_1,"B20_minute_ranges_interp.csv")

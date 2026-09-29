library(tidyverse)
library(Distance)

#Reads combined csv of interpolated ranges for all stations
calltable <-read.csv("All_stations_interp_call_ranges_add_april.csv")

#Filters out any calls with no ranges
calltable <- calltable %>% #not necessary for Bryde's, got rid of stations B06
  filter(station_code != 'B06')

calltable <- calltable%>% 
  drop_na(interp_range)


#makes a new table specifically for distance sampling
dist_table <- calltable %>% 
  select(peak_time,peak_signal,snr,db_amps,station_code,network_code,interp_range,ambient_snr)

#assigns key metrics to variable names used for fitting probability density function
Study.Area = rep("Marianas",each=length(dist_table$peak_time))
Effort = rep(1,each=length(dist_table$peak_time))
Area = rep(pi*40^2,each=length(dist_table$peak_time)) #Calculates area of circle, change value
CoveredArea = rep(pi*40^2,each=length(dist_table$peak_time)) #Value here should match previous

dist_table$Region.Label <- substring(dist_table$peak_time,4,6)
dist_table$Effort <- Effort
dist_table$Sample.Label <- dist_table$station_code
dist_table$Study.Area = Study.Area
dist_table$Region.Label = substring(dist_table$peak_time,4,6)
dist_table$Area <- Area

dist_table <- dist_table %>%
  filter(Region.Label != 'Feb') #gets rid of any ranges in february, which is when airguns interfered with ranging

#Assign effort to be days in month. You will need to add other months.
idx_m <- grep("Mar", dist_table$Region.Label);
idx_a <- grep("Apr", dist_table$Region.Label);
idx_d <- grep("Dec", dist_table$Region.Label);
idx_j <- grep("Jan", dist_table$Region.Label);

#scales effort by length of month
dist_table$Effort[idx_m] <- 1
dist_table$Effort[idx_a] <- (30/31)
dist_table$Effort[idx_d] <- 1
dist_table$Effort[idx_j] <- 1


#
dist_table <- dist_table %>% 
  rename(distance = interp_range) 


dist_table <- dist_table %>% 
  select(Study.Area,Region.Label,Sample.Label,Effort,distance,everything())

write.csv(dist_table, "FinDistance_test.csv", row.names=FALSE)


table_big35 <- dist_table %>%
  filter(distance > 35)

ggplot(dist_table, aes(x=log10(peak_signal), y=distance)) +
  geom_point(alpha=0.1, size=1.0, color = 'blue') +
  labs(x="Detection Score", y="Radial distance (km)") +
  scale_x_continuous(limits = c(min(log10(dist_table$peak_signal)), max(log10(dist_table$peak_signal))), expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, 40), expand = c(0, 0)) 


dist_table$db_amps <- scale(dist_table$db_amps)
dist_table$snr <- scale(dist_table$snr)
dist_table$peak_signal <- log10(dist_table$peak_signal)
dist_table$ambient_snr <- dist_table$ambient_snr/sd(dist_table$ambient_snr, na.rm=TRUE)
dist_table <- dist_table %>%
  filter(peak_signal < 6)

conv <- convert_units("kilometer", NULL, "square kilometer")

#This section does error estimates
dist_table_0 = dist_table %>%
  filter(distance < 5)
dist_table_1 = dist_table %>%
  filter(distance > 5 & distance < 20)
dist_table_2 = dist_table %>%
  filter(distance > 20 & distance < 30)
dist_table_3 = dist_table %>%
  filter(distance > 30 & distance < 40)


#further adjustment estimate
c_1 = seq(1,length(dist_table_1$distance),by=2)
c_2 = seq(1,length(dist_table_2$distance),by=2)
c_3 = seq(1,length(dist_table_3$distance),by=2)
dist_table_1_far <- dist_table_1 
dist_table_1_far$distance[c_1] = dist_table_1$distance[c_1]+3.4 
dist_table_2_far <- dist_table_2 
dist_table_2_far$distance[c_2] = dist_table_2$distance[c_2]+6
dist_table_3_far <- dist_table_3 
dist_table_3_far$distance[c_3] = dist_table_3$distance[c_3]+7.8

dist_table_far <- rbind(dist_table_0, dist_table_1_far, dist_table_2_far, dist_table_3_far)


#closer adjustment estimate
dist_table_1_close <- dist_table_1 
dist_table_1_close$distance[c_1] = dist_table_1$distance[c_1]-1.3 
dist_table_2_close <- dist_table_2 
dist_table_2_close$distance[c_2] = dist_table_2$distance[c_2]-2.5
dist_table_3_close <- dist_table_3 
dist_table_3_close$distance[c_3] = dist_table_3$distance[c_3]-3.5

dist_table_close <- rbind(dist_table_0, dist_table_1_close, dist_table_2_close, dist_table_3_close)


#hazard rate no adjustment
hr.model0 <- ds(dist_table, transect="point", key="hr", truncation=35,
                adjustment=NULL, convert_units = conv)
plot(hr.model0, nc=20, main="No covariates", pch='.', pdf=TRUE)
summary(hr.model0)

#hazard rate no adjustment - far uncertainty
hr.model0_far <- ds(dist_table_far, transect="point", key="hr", truncation=35,
                adjustment=NULL, convert_units = conv)
#plot(hr.model0_far, nc=20, main="No covariates", pch='.', pdf=TRUE)
#summary(hr.model0_far)

#hazard rate no adjustment - close uncertainty
hr.model0_close <- ds(dist_table_close, transect="point", key="hr", truncation=35,
                adjustment=NULL, convert_units = conv)
#plot(hr.model0_close, nc=20, main="No covariates", pch='.', pdf=TRUE)
#summary(hr.model0_close)


#sum_model_hr_un = summarize_ds_models(hr.model0, hr.model0_far, hr.model0_close)


#half normal no adjustment
hn.model0 <- ds(dist_table, transect="point", key="hn", truncation=35,
                adjustment=NULL, convert_units = conv)
#plot(hr.model0, nc=20, main="No covariates", pch='.', pdf=TRUE)

#additional models
#add adjustment terms, half normal with adjustment and covariates
#hn.adj_cos4 <- ds(dist_table, transect="point", key="hn",adjustment='cos', order=4,
#                 truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hn.adj_cos4, nc=20, main="covariate: None, Half-Normal, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hn.adj_cos4)

#hr.adj_cos4 <- ds(dist_table, transect="point", key="hr",adjustment='cos', order=4,
#                 truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hr.adj_cos4, nc=20, main="covariate: None, Hazard-Rate, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hr.adj_cos4)

#hn.adj_cos2 <- ds(dist_table, transect="point", key="hn",adjustment='cos', order=2,
#                 truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hn.adj_cos2, nc=20, main="covariate: None, Half-Normal, Cosine(2) adj", pch='.', pdf=TRUE)
#gof_ds(hn.adj_cos2)

#hr.adj_cos2 <- ds(dist_table, transect="point", key="hr",adjustment='cos', order=2,
#                 truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hr.adj_cos2, nc=20, main="covariate: None, Hazard-Rate, Cosine(2) adj", pch='.', pdf=TRUE)
#gof_ds(hr.adj_cos2)

#hn.adj_cos3 <- ds(dist_table, transect="point", key="hn",adjustment='cos', order=3,
#                  truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hn.adj_cos3, nc=20, main="covariate: None, Half-Normal, Cosine(3) adj", pch='.', pdf=TRUE)
#gof_ds(hn.adj_cos3)

#hr.adj_cos3 <- ds(dist_table, transect="point", key="hr",adjustment='cos', order=3,
#                  truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hr.adj_cos3, nc=20, main="covariate: None, Hazard-Rate, Cosine(3) adj", pch='.', pdf=TRUE)
#gof_ds(hr.adj_cos3)

hn.station_cos4 <- ds(dist_table, transect="point", key="hn", truncation=35,
                      formula=~station_code,adjustment="cos",order=4, convert_units = conv)
#plot(hn.station_cos4, nc=20, main="covariate: Station, Half-Normal, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hn.station_cos4)

hr.station_cos4 <- ds(dist_table, transect="point", key="hr", truncation=35,
                      formula=~station_code,adjustment="cos",order=4, convert_units = conv)
#plot(hr.station_cos4, nc=20, main="covariate: Station, Hazard-Rate, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hr.station_cos4)

hr.station_cos4_close <- ds(dist_table_close, transect="point", key="hr", truncation=35,
                      formula=~station_code,adjustment="cos",order=4, convert_units = conv)
#plot(hr.station_cos4, nc=20, main="covariate: Station, Hazard-Rate, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hr.station_cos4)

hr.station_cos4_far <- ds(dist_table_far, transect="point", key="hr", truncation=35,
                      formula=~station_code,adjustment="cos",order=4, convert_units = conv)
#plot(hr.station_cos4, nc=20, main="covariate: Station, Hazard-Rate, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hr.station_cos4)

#hn.station_cos3 <- ds(dist_table, transect="point", key="hn", truncation=35,
#                      formula=~station_code,adjustment="cos",order=3, convert_units = conv)
#plot(hn.station_cos4, nc=20, main="covariate: Station, Half-Normal, Cosine(3) adj", pch='.', pdf=TRUE)
#gof_ds(hn.station_cos4)


#hr.station_cos3 <- ds(dist_table, transect="point", key="hr", truncation=35,
#                      formula=~station_code,adjustment="cos",order=3, convert_units = conv)
#plot(hr.station_cos3, nc=20, main="covariate: Station, Hazard-Rate, Cosine(3) adj", pch='.', pdf=TRUE)
#gof_ds(hr.station_cos3)

#hn.station_cos2 <- ds(dist_table, transect="point", key="hn", truncation=35,
#                      formula=~station_code,adjustment="cos",order=2, convert_units = conv)
#plot(hn.station_cos2, nc=20, main="covariate: Station, Half-Normal, Cosine(2) adj", pch='.', pdf=TRUE)
#gof_ds(hn.station_cos2)

#hr.station_cos2 <- ds(dist_table, transect="point", key="hr", truncation=35,
#                      formula=~station_code,adjustment="cos",order=2, convert_units = conv)
#plot(hr.station_cos2, nc=20, main="covariate: Station, Hazard-Rate, Cosine(2) adj", pch='.', pdf=TRUE)
#gof_ds(hr.station_cos2)

#sum_model0cos2 = summarize_ds_models(hr.model0, hn.model0, hn.adj_cos2, hr.adj_cos2)



#make plots
#HR cos4 sta
pdf("hr_cos4_sta_func.pdf",width=7,height=6)
plot(hr.station_cos4, nc=20, main="Model with OBS covariate, cos(4) adjustment", cex=0.5, pdf=FALSE, lwd=2, showpoints=FALSE)
add_df_covar_line(hr.station_cos4, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("black","black","black","black","black","black","black"), lty=1,pdf=FALSE)

add_df_covar_line(hr.station_cos4, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lty=2, lwd=2, pdf=FALSE)

legend("topright", legend=c("B01","B02","B09","B12","B18","B19","B20"),
       col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lwd=2)
dev.off()

#HR cos3 sta
plot(hr.station_cos3, nc=20, main="Model with OBS covariate, cos(3) adjustment", cex=0.5, pdf=TRUE, lwd=2, showpoints=FALSE)
add_df_covar_line(hr.station_cos3, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("black","black","black","black","black","black","black"), lty=1,pdf=TRUE)

add_df_covar_line(hr.station_cos3, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lty=2, lwd=2, pdf=TRUE)

legend("topright", legend=c("B01","B02","B09","B12","B18","B19","B20"),
       col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lwd=2)


pdf("hr_cos4_sta_0.pdf",width=7,height=6)
plot(hr.station_cos4, ylim = c(0, 0.07), nc=20, main="Model with OBS covariate, cos(4) adjustment", cex=0.5, pdf=TRUE, lwd=2, showpoints=FALSE)
dev.off()

pdf("hr_cos4_sta_close.pdf",width=7,height=6)
plot(hr.station_cos4_close, ylim = c(0, 0.07), nc=20, main="Model with OBS covariate, cos(4) adjustment, close", cex=0.5, pdf=TRUE, lwd=2, showpoints=FALSE)
dev.off() 

pdf("hr_cos4_sta_far.pdf",width=7,height=6)
plot(hr.station_cos4_far, ylim = c(0, 0.07), nc=20, main="Model with OBS covariate, cos(4) adjustment, far", cex=0.5, pdf=TRUE, lwd=2, showpoints=FALSE)
dev.off()

pdf("hr_model0_pdf.pdf",width=7,height=6)
plot(hr.model0,ylim = c(0, 1.5),nc=20,main = "HR Model 0", showpoints=FALSE)
dev.off()

pdf("hn_model0_pdf.pdf",width=7,height=6)
plot(hn.model0,ylim = c(0, 1.5),nc=20,main = "HN Model 0",showpoints=FALSE)
dev.off()

pdf("hr_cos4_sta_0_pdf.pdf",width=7,height=6)
plot(hr.station_cos4,ylim = c(0, 1.5),nc=20,main = "HR with OBS covariate, cos(4) adjustment",showpoints=FALSE)
dev.off()

pdf("hn_cos4_sta_0_pdf.pdf",width=7,height=6)
plot(hn.station_cos4,ylim = c(0, 1.5),nc=20,main = "HN with OBS covariate, cos(4) adjustment",showpoints=FALSE)
dev.off()

pdf("hr_cos4_pdf.pdf",width=7,height=6)
plot(hr.adj_cos4,ylim = c(0, 1.5),nc=20,main="HR cos(4) adjustment",showpoints=FALSE)
dev.off()




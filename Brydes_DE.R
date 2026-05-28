library(tidyverse)
library(Distance)

#Reads combined csv of interpolated ranges for all stations
calltable <-read.csv("/Users/ryan.homer/Documents/MATLAB/Interp_Ranges/All_call_ranges_interp_Brydes.csv")

#Filters out any calls with no ranges
calltable <- calltable %>% #not necessary for Bryde's, got rid of stations B06
  filter(interp_range < 25)

calltable <- calltable%>% 
  drop_na(interp_range)


#makes a new table specifically for distance sampling
dist_table <- calltable %>% 
  select(peak_time,peak_signal,snr,db_amps,station_code,network_code,interp_range,ambient_snr)

#assigns key metrics to variable names used for fitting probability density function
Study.Area = rep("Marianas",each=length(dist_table$peak_time))
Effort = rep(1,each=length(dist_table$peak_time))
Area = rep(1,each=length(dist_table$peak_time)) #Calculates area of circle, change value
CoveredArea = rep(1,each=length(dist_table$peak_time)) #Value here should match previous

dist_table$Region.Label <- substring(dist_table$peak_time,4,6)
dist_table$Effort <- Effort
dist_table$Sample.Label <- dist_table$station_code
dist_table$Study.Area = Study.Area
dist_table$Region.Label = substring(dist_table$peak_time,4,6)
dist_table$Area <- Area

dist_table <- dist_table %>%
  filter(Region.Label != 'Feb') #gets rid of any ranges in february, which is when airguns interfered with ranging

#Assign effort to be days in month. You will need to add other months.
idx_mar <- grep("Mar", dist_table$Region.Label);
idx_apr <- grep("Apr", dist_table$Region.Label);
idx_may <- grep("May", dist_table$Region.Label);
idx_jun <- grep("Jun", dist_table$Region.Label);
idx_jul <- grep("Jul", dist_table$Region.Label);
idx_aug <- grep("Aug", dist_table$Region.Label);
idx_sep <- grep("Sep", dist_table$Region.Label);
idx_oct <- grep("Oct", dist_table$Region.Label);
idx_nov <- grep("Nov", dist_table$Region.Label);
idx_dec <- grep("Dec", dist_table$Region.Label);
idx_jan <- grep("Jan", dist_table$Region.Label);

#scales effort by length of month
dist_table$Effort[idx_mar] <- 1
dist_table$Effort[idx_apr] <- (30/31)
dist_table$Effort[idx_may] <- 1
dist_table$Effort[idx_jun] <- (30/31)
dist_table$Effort[idx_jul] <- 1
dist_table$Effort[idx_aug] <- 1
dist_table$Effort[idx_sep] <- (30/31)
dist_table$Effort[idx_oct] <- 1
dist_table$Effort[idx_nov] <- (30/31)
dist_table$Effort[idx_dec] <- 1
dist_table$Effort[idx_jan] <- 1


#Sets up table for distance sampling
dist_table <- dist_table %>% 
  rename(distance = interp_range) 


dist_table <- dist_table %>% 
  select(Study.Area,Region.Label,Sample.Label,Effort,distance,everything())

write.csv(dist_table, "BrydesDistance_test.csv", row.names=FALSE)

#plots changes in detection score with distance
ggplot(dist_table, aes(x=distance, y=log10(peak_signal))) +
  geom_point(alpha=0.1, size=1.0, color = 'blue') +
  labs(x="Radial distance (km)", y="Detection Score") +
  scale_y_continuous(limits = c(min(log10(dist_table$peak_signal)), max(log10(dist_table$peak_signal))), expand = c(0, 0)) +
  scale_x_continuous(limits = c(0, 25), expand = c(0, 0)) 

ggplot(dist_table, aes(x=distance, y=db_amps)) +
  geom_point(alpha=0.1, size=1.0, color='purple') +
  labs(x="Radial distance (km)", y="dB Amplitudes") +
  scale_y_continuous(limits = c(min(dist_table$db_amps), max(dist_table$db_amps)-30), expand = c(0, 0)) +
  scale_x_continuous(limits = c(0, 25), expand = c(0, 0)) 

ggplot(dist_table, aes(x=distance, y=snr)) +
  geom_point(alpha=0.1, size=1.0, color = 'red') +
  labs(x="Radial distance (km)", y="SNR") +
  scale_y_continuous(limits = c(min(dist_table$snr), max(dist_table$snr)), expand = c(0, 0)) +
  scale_x_continuous(limits = c(0, 25), expand = c(0, 0)) 

dist_table$db_amps <- scale(dist_table$db_amps)
dist_table$snr <- scale(dist_table$snr)
dist_table$peak_signal <- log10(dist_table$peak_signal)
dist_table$ambient_snr <- dist_table$ambient_snr/sd(dist_table$ambient_snr, na.rm=TRUE)

#dist_table <- dist_table %>%
#  filter(peak_signal < 6)

conv <- convert_units("kilometer", NULL, "square kilometer")

#STARTS DISTANCE SAMPLING MODELS
#TRIES HALF NORMAL, HAZARD RATE, OBS COVARIATES, AND DIFFERENT ORDERS OF 
#COSINE ADJUSTMENTS TO EACH MODEL
#Goal is to fit distribution without overfitting
#Select model with lowest AIC and well-fitting Q-Q plot

#hazard rate no adjustment
#hr.model0 <- ds(dist_table, transect="point", key="hr", truncation="5%",
               # adjustment=NULL, convert_units = conv)
#plot(hr.model0, nc=12, main="No covariates", pch='.', pdf=TRUE)
#summary(hr.model0)

#half normal no adjustment
hn.model0 <- ds(dist_table, transect="point", key="hn", truncation="5%",
                adjustment=NULL, convert_units = conv)
plot(hn.model0, nc=12, main="No covariates", pch='.', pdf=TRUE)
summary(hn.model0)

#additional models
#add adjustment terms, half normal with adjustment and covariates
#hn.adj_cos4 <- ds(dist_table, transect="point", key="hn",adjustment='cos', order=4,
#                 truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hn.adj_cos4, nc=12, main="covariate: None, Half-Normal, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hn.adj_cos4)

#hr.adj_cos4 <- ds(dist_table, transect="point", key="hr",adjustment='cos', order=4,
#                 truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hr.adj_cos4, nc=12, main="covariate: None, Hazard-Rate, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hr.adj_cos4)

hn.adj_cos2 <- ds(dist_table, transect="point", key="hn",adjustment='cos', order=2,
                 truncation="5%", convert_units = conv,monotonicity=FALSE)
plot(hn.adj_cos2, nc=12, main="covariate: None, Half-Normal, Cosine(2) adj", pch='.', pdf=TRUE)
gof_ds(hn.adj_cos2)

hr.adj_cos2 <- ds(dist_table, transect="point", key="hr",adjustment='cos', order=2,
                 truncation="5%", convert_units = conv,monotonicity=FALSE)
plot(hr.adj_cos2, nc=12, main="covariate: None, Hazard-Rate, Cosine(2) adj", pch='.', pdf=TRUE)
gof_ds(hr.adj_cos2)

hn.station <- ds(dist_table, transect="point", key="hn", truncation="5%",
                      formula=~station_code,adjustment=NULL, convert_units = conv)
plot(hn.station, nc=12, main="covariate: Station, Half-Normal", pch='.', pdf=TRUE)
gof_ds(hn.station)

#THE CHOSEN ONE (for Bryde's whale call density)
hr.station <- ds(dist_table, transect="point", key="hr", truncation="5%",
                      formula=~station_code,adjustment=NULL, convert_units = conv)
plot(hr.station, nc=12, main="covariate: Station, Hazard-Rate", pch='.', pdf=TRUE)
gof_ds(hr.station)


hr.station_leftTrunc <- ds(dist_table, transect="point", key="hr", truncation= list(left=1.5,right="5%"),
                      formula=~station_code,adjustment=NULL, convert_units = conv)
plot(hr.station_leftTrunc, nc=12, main="covariate: Station, Hazard-Rate, 1.5km left truncation", pch='.', pdf=TRUE)
gof_ds(hr.station_leftTrunc)


#hn.adj_cos3 <- ds(dist_table, transect="point", key="hn",adjustment='cos', order=3,
#                  truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hn.adj_cos3, nc=12, main="covariate: None, Half-Normal, Cosine(3) adj", pch='.', pdf=TRUE)
#gof_ds(hn.adj_cos3)

#hr.adj_cos3 <- ds(dist_table, transect="point", key="hr",adjustment='cos', order=3,
#                  truncation=35, convert_units = conv,monotonicity=FALSE)
#plot(hr.adj_cos3, nc=12, main="covariate: None, Hazard-Rate, Cosine(3) adj", pch='.', pdf=TRUE)
#gof_ds(hr.adj_cos3)

#hn.station_cos4 <- ds(dist_table, transect="point", key="hn", truncation="5%",
#                      formula=~station_code,adjustment="cos",order=4, convert_units = conv)
#plot(hn.station_cos4, nc=12, main="covariate: Station, Half-Normal, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hn.station_cos4)

#hr.station_cos4 <- ds(dist_table, transect="point", key="hr", truncation="5%",
#                      formula=~station_code,adjustment="cos",order=4, convert_units = conv)
#plot(hr.station_cos4, nc=12, main="covariate: Station, Hazard-Rate, Cosine(4) adj", pch='.', pdf=TRUE)
#gof_ds(hr.station_cos4)

hn.station_cos3 <- ds(dist_table, transect="point", key="hn", truncation="5%",
                      formula=~station_code,adjustment="cos",order=3, convert_units = conv)
plot(hn.station_cos3, nc=12, main="covariate: Station, Half-Normal, Cosine(3) adj", pch='.', pdf=TRUE)
gof_ds(hn.station_cos3)


hr.station_cos3 <- ds(dist_table, transect="point", key="hr", truncation="5%",
                      formula=~station_code,adjustment="cos",order=3, convert_units = conv)
plot(hr.station_cos3, nc=12, main="covariate: Station, Hazard-Rate, Cosine(3) adj", pch='.', pdf=TRUE)
gof_ds(hr.station_cos3)

hn.station_cos2 <- ds(dist_table, transect="point", key="hn", truncation="5%",
                      formula=~station_code,adjustment="cos",order=2, convert_units = conv)
plot(hn.station_cos2, nc=12, main="covariate: Station, Half-Normal, Cosine(2) adj", pch='.', pdf=TRUE)
gof_ds(hn.station_cos2)

hr.station_cos2 <- ds(dist_table, transect="point", key="hr", truncation="5%",
                      formula=~station_code,adjustment="cos",order=2, convert_units = conv)
plot(hr.station_cos2, nc=12, main="covariate: Station, Hazard-Rate, Cosine(2) adj", pch='.', pdf=TRUE)
gof_ds(hr.station_cos2)

#Trying diff adjustments for models:

hr.herm <- ds(dist_table, transect="point", key="hr", truncation="5%",
                      adjustment="herm", convert_units = conv)
plot(hr.herm, nc=12, main="Hazard Rate, Hermite Adjustment", pch='.', pdf=TRUE)
gof_ds(hr.herm)

hr.poly <- ds(dist_table, transect="point", key="hr", truncation="5%",
                      adjustment="poly", convert_units = conv)
plot(hr.poly, nc=12, main="Hazard Rate Polynomial Adjustment", pch='.', pdf=TRUE)
gof_ds(hr.poly)


hn.herm <- ds(dist_table, transect="point", key="hn", truncation="5%",
              adjustment="herm", convert_units = conv)
plot(hn.herm, nc=12, main="Half-normal, Hermite Adjustment", pch='.', pdf=TRUE)
gof_ds(hn.herm)

hn.poly <- ds(dist_table, transect="point", key="hn", truncation="5%",
              adjustment="poly", convert_units = conv)
plot(hn.poly, nc=12, main="Half-normal, Polynomial Adjustment", pch='.', pdf=TRUE)
gof_ds(hn.poly)


#Use summarize_ds_models to compare fit of different model types
sum_model0cos2 = summarize_ds_models(hn.station, hn.station_cos2, hr.station, hr.station_cos2, hr.station_cos3)



#MAKES DISTANCE SAMPLING PLOTS

#HR station covariate
pdf(hr_stplot(hr.station, nc=12, main= "Model with OBS covariate, NULL adjustment", cex=0.5, pdf=TRUE, lwd=2, showpoints=FALSE)
add_df_covar_line(hr.station, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("black","black","black","black","black","black","black"), lty=1,pdf=TRUE)

add_df_covar_line(hr.station, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lty=2, lwd=2, pdf=TRUE)

legend("topright", legend=c("B01","B02","B09","B12","B18","B19","B20"),
       col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lwd=2)ation.pdf,width=7,height=6)
plot(hr.station, nc=12, main="Model with OBS covariate, NULL adjustment", cex=0.5, pdf=TRUE, lwd=2, showpoints=FALSE)
add_df_covar_line(hr.station, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("black","black","black","black","black","black","black"), lty=1,pdf=TRUE)

add_df_covar_line(hr.station, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lty=2, lwd=2, pdf=TRUE)

legend("topright", legend=c("B01","B02","B09","B12","B18","B19","B20"),
       col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lwd=2)
dev.off()

#HR cos2 sta
pdf("hr_cos2_sta_func.pdf",width=7,height=6)
plot(hr.station_cos2, nc=12, main="Model with OBS covariate, cos(2) adjustment", cex=0.5, pdf=FALSE, lwd=2, showpoints=FALSE)
add_df_covar_line(hr.station_cos2, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("black","black","black","black","black","black","black"), lty=1,pdf=FALSE)

add_df_covar_line(hr.station_cos2, data.frame(station_code=c("B01","B02","B09","B12","B18","B19","B20")),
                  col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lty=2, lwd=2, pdf=FALSE)

legend("topright", legend=c("B01","B02","B09","B12","B18","B19","B20"),
       col=c("#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69"), lwd=2)
dev.off()

plot(hr.station_cos4, ylim = c(0, 0.07), nc=12, main="Model with OBS covariate, cos(4) adjustment", cex=0.5, pdf=TRUE, lwd=2, showpoints=FALSE)
dev.off()

pdf("hr_model0_pdf.pdf",width=7,height=6)
plot(hr.model0,ylim = c(0, 1.5),nc=12,main = "HR Model 0", showpoints=FALSE)
dev.off()

pdf("hn_model0_pdf.pdf",width=7,height=6)
plot(hn.model0,ylim = c(0, 1.5),nc=12,main = "HN Model 0",showpoints=FALSE)
dev.off()


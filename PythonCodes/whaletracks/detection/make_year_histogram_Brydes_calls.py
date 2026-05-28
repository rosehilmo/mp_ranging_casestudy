"""
Created on Wed Jun 4, 2025

Reads Bryde's whale detection file for station B19 and plots histogram of detections over a certain strength for the deployment year

@author: rhilmo
"""

import pandas as pd
import matplotlib.pyplot as plt

detection_threshold = 5000 #minimum detection threshold for histogram



df_calls=pd.read_csv('B12_mp_Brydes_Year_LongCall.csv') #reads table using pandas
df_calls['peak_time']=pd.to_datetime(df_calls['peak_time']) #converts detection times from datestrings to datetimes

df_calls1=df_calls.loc[(df_calls['peak_signal'] >= detection_threshold)] #Makes new dataframe with only calls with higher deteciton scores than detection_threshold
plt.hist(df_calls1.peak_time,bins=350) #makes histogram with 350 bins
plt.xlabel('Date')
plt.ylabel('Count')
plt.show() #displays histogram
#Use zoom tools on plot to look at specific days




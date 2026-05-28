"""Constants used in the whale project."""

import collections
import os
import sys

# tablename in whaletracks.db
# filename in data
Schema = collections.namedtuple("Schema",
    "tablename columns csv_path")

class SchemaContainer(object):
    def __init__(self):
        self.schemas = []
        
    def append(self, tablename, columns, csv_path=None):
        schema = Schema(tablename=tablename, columns=columns, csv_path=csv_path)
        self.schemas.append(schema)
        
SCHEMA = SchemaContainer()
        
        

PROJECT_NAME = "whaletracks"

# PATHS
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
  PROJECT_DIR = os.path.dirname(PROJECT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
PROJECT_CODE = os.path.join(PROJECT_DIR, PROJECT_NAME)
BLUE_DETECTION_FILE = os.path.join(DATA_DIR,
    "detections.csv")
DB_PTH = os.path.join(DATA_DIR, "whaletracks.db")

# Add search paths
sys.path.insert(0, PROJECT_CODE)


# Columns
# Columns ended in _EPOCH populated automatically in db_builder
AZIMUTH = "azimuth"
CHANNEL = "channel"
CHANNEL_CODE = "channel_code"
CHANNEL_ID = "channel_id"  # NETWORK_CODE.STATION_CODE.CHANNEL_CODE
CHANNEL_TYPES = "channel_types"
CODE = "code"
CREATION_EPOCH = "creation_epoch" # Float for days since 1-1-1970
CREATION_TIME = "creation_time"  # UTC datetime
DIP = "dip"
DURATION = "duration"
ELEVATION  = 'elevation'
END_EPOCH  = 'end_epoch'  # Float for days since 1-1-1970
END_TIME  = 'end_time'  # UTC datetime
END_FREQUENCY = "end_frequency"
END_FREQUENCY_STD = "end_frequency_std"
EVENT = "event"
GAIN = "gain"
LATITUDE  = 'latitude'
LONGITUDE  = 'longitude'
MIN_SIGNAL = "min_signal"
NETWORK = "network"
NETWORK_CODE = "network_code"  # str
PEAK_FREQUECNY = "peak_frequency" #Frequency with most energy at peak det time
PEAK_FREQUENCY_STD = "peak_frequency_std" #Spread of frequency
PEAK_SIGNAL = "peak_signal"
PEAK_EPOCH = "peak_epoch"  # Float for days since 1-1-1970
PEAK_TIME = "peak_time"  # UTC datetime
POLES = "poles"  # semicolon separated values of immaginary numbers
SENSITIVITY_FREQUENCY = "sensitivity_frequency"
SENSITIVITY_VALUE = "sensitivity_value"
SENSOR = "sensor"
SNR = "snr"
SNR_AMBIENT = "ambient_snr"
SNR_EQ = "eq_snr"
START_EPOCH = "start_epoch" # Float for days since 1-1-1970
START_TIME = "start_time"  #UTC datetime
START_FREQUENCY = "start_frequency"
START_FREQUENCY_STD = "start_frequency_std"
STATION_CODE = "station_code"  # str
STATION_ID = "station_id"  # NETWORK_CODE.STATION_CODE
THRESHOLD = "threshold"
TERMINATION_EPOCH = 'termination_epoch' # Float for days since 1-1-1970
TERMINATION_TIME  = 'termination_time'  # UTC datetime
TOTAL_NUMBER_OF_CHANNELS  = 'total_number_of_channels'
VALUE = "value"
ZEROES = "zeroes" # semicolon separated values of immaginary numbers
ARRIVAL_1 = "arrival_1"
ARRIVAL_2 = "arrival_2"
ARRIVAL_3 = "arrival_3"
ARRIVAL_4 = "arrival_4"
ARRIVAL_5 = "arrival_5"
AMP_1 = "amp_1"
AMP_2 = "amp_2"
AMP_3 = "amp_3"
AMP_4 = "amp_4"
AMP_5 = "amp_5"
ERR_1 = "err_1"
ERR_2 = "err_2"
ERR_3 = "err_3"
ERR_4 = "err_4"
ERR_5 = "err_5"

# Table schemas

SCM_MULTIPATHS = Schema(tablename="multipaths",
    columns=[ARRIVAL_1, ARRIVAL_2, ARRIVAL_3, ARRIVAL_4, ARRIVAL_5,
    AMP_1, AMP_2, AMP_3, AMP_4, AMP_5, ERR_1, ERR_2, ERR_3, ERR_4, ERR_5],
    csv_path=None)
SCHEMA.append(SCM_MULTIPATHS.tablename, SCM_MULTIPATHS.columns)

SCM_DETECTION = Schema(tablename="detections",
    columns=[DURATION,
    END_EPOCH, END_TIME, MIN_SIGNAL, PEAK_SIGNAL,
    PEAK_EPOCH, PEAK_TIME, START_EPOCH, START_TIME,
    SNR, THRESHOLD, STATION_CODE, NETWORK_CODE,
    SNR_AMBIENT, SNR_EQ],
    csv_path=os.path.join(DATA_DIR, 'detections.csv'))
SCHEMA.append(SCM_DETECTION.tablename, SCM_DETECTION.columns, csv_path=SCM_DETECTION.csv_path)

SCHEMA.append("peaks",
    [NETWORK_CODE, STATION_CODE,
    START_EPOCH, START_TIME, END_EPOCH, END_TIME, VALUE, EVENT])
SCHEMA.append("station_quality",
    [NETWORK_CODE, STATION_CODE, START_EPOCH, START_TIME, END_EPOCH, END_TIME])

SCMS = SCHEMA.schemas
TABLES = [s.tablename for s in SCMS]

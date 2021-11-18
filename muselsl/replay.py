from time import time, sleep

import pandas as pd
import numpy as np
from numpy import NaN
from pylsl import StreamInfo, StreamOutlet
from functools import partial
import pygatt
import subprocess
from sys import platform
from . import helper
from .muse import Muse
from .constants import MUSE_SCAN_TIMEOUT, AUTO_DISCONNECT_DELAY,  \
    MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, LSL_EEG_CHUNK,  \
    MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE, LSL_PPG_CHUNK, \
    MUSE_NB_ACC_CHANNELS, MUSE_SAMPLING_ACC_RATE, LSL_ACC_CHUNK, \
    MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE, LSL_GYRO_CHUNK



def replay(filename, acc_enabled=False, gyro_enabled=False):
    # load and prepare data from csv
    timestamp_csv = "TimeStamp"
    eeg_channels_csv = ["RAW_TP9", "RAW_AF7", "RAW_AF8", "RAW_TP10", "AUX_RIGHT"]
    acc_channels_csv = ["Accelerometer_X", "Accelerometer_Y", "Accelerometer_Z"]
    gyro_channels_csv = ["Gyro_X", "Gyro_Y", "Gyro_Z"]
    
    selected_csv_columns = []

    data = pd.read_csv(filename)
    data = drop_events(data)
    data = data.set_index(timestamp_csv)
    
    selected_csv_columns += eeg_channels_csv
    eeg_info = StreamInfo('Muse', 'EEG', MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, 'float32',
                            'Muse')
    eeg_info.desc().append_child_value("manufacturer", "Muse")
    eeg_channels = eeg_info.desc().append_child("channels")

    for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
        eeg_channels.append_child("channel") \
            .append_child_value("label", c) \
            .append_child_value("unit", "microvolts") \
            .append_child_value("type", "EEG")

    eeg_outlet = StreamOutlet(eeg_info, LSL_EEG_CHUNK)

    # convert everything to floats
    data = data[selected_csv_columns].astype(float)
    
    print("Replay started...")
    for x in data.itertuples():
        timestamp, *data = tuple(x)
        # convert timestamp to unix-time
        timestamp = pd.to_datetime(timestamp).timestamp()
        # print(data)
        eeg_outlet.push_sample(data, timestamp)

    print("Replay finished.")


def drop_events(dataframe: "pd.DataFrame") -> "pd.DataFrame":
    return dataframe[dataframe["Elements"].isna()]


if __name__ == "__main__":
    replay("data/mindMonitor_2021-06-11--13-39-08.csv")
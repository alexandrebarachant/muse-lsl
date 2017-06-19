#!/usr/bin/env python
import numpy as np
import pandas as pd
from time import time, strftime, gmtime
from optparse import OptionParser
from pylsl import StreamInlet, resolve_byprop
from sklearn.linear_model import LinearRegression

default_fname = ("data_%s.csv" % strftime("%Y-%m-%d-%H.%M.%S", gmtime()))
parser = OptionParser()
parser.add_option("-d", "--duration",
                  dest="duration", type='int', default=60,
                  help="duration of the recording in seconds.")
parser.add_option("-f", "--filename",
                  dest="filename", type='str', default=default_fname,
                  help="Name of the recording file.")

# dejitter timestamps
dejitter = False

(options, args) = parser.parse_args()


print("looking for an EEG stream...")
streams = resolve_byprop('type', 'EEG', timeout=2)

if len(streams) == 0:
    raise(RuntimeError, "Cant find EEG stream")

print("Start aquiring data")
inlet = StreamInlet(streams[0], max_chunklen=12)
eeg_time_correction = inlet.time_correction()

print("looking for a Markers stream...")
marker_streams = resolve_byprop('name', 'Markers', timeout=2)

if marker_streams:
    inlet_marker = StreamInlet(marker_streams[0])
    marker_time_correction = inlet_marker.time_correction()
else:
    inlet_marker = False
    print("Cant find Markers stream")

info = inlet.info()
description = info.desc()

freq = info.nominal_srate()
Nchan = info.channel_count()

ch = description.child('channels').first_child()
ch_names = [ch.child_value('label')]
for i in range(1, Nchan):
    ch = ch.next_sibling()
    ch_names.append(ch.child_value('label'))

res = []
timestamps = []
markers = []
t_init = time()
time_correction = inlet.time_correction()
print(time_correction)
print('Start recording at time t=%.3f' % t_init)
while (time() - t_init) < options.duration:
    try:
        data, timestamp = inlet.pull_chunk(timeout=1.0,
                                           max_samples=12)
        if timestamp:
            res.append(data)
            timestamps.extend(timestamp)
        if inlet_marker:
            marker, timestamp = inlet_marker.pull_sample(timeout=0.0)
            if timestamp:
                markers.append([marker, timestamp])
    except KeyboardInterrupt:
        break

time_correction = inlet.time_correction()
print(time_correction)

res = np.concatenate(res, axis=0)
timestamps = np.array(timestamps) + time_correction

if dejitter:
    y = timestamps
    X = np.atleast_2d(np.arange(0, len(y))).T
    lr = LinearRegression()
    lr.fit(X, y)
    timestamps = lr.predict(X)

res = np.c_[timestamps, res]
data = pd.DataFrame(data=res, columns=['timestamps'] + ch_names)

n_markers = len(markers[0][0])
for ii in range(n_markers):
    data['Marker%d' % ii] = 0
# process markers:
for marker in markers:
    # find index of margers
    ix = np.argmin(np.abs(marker[1] - timestamps))
    val = timestamps[ix]
    for ii in range(n_markers):
        data.loc[ix, 'Marker%d' % ii] = marker[0][ii]


data.to_csv(options.filename, float_format='%.3f', index=False)

print('Done !')

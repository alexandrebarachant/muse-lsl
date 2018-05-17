import numpy as np
import pandas as pd
from pylsl import StreamInlet, resolve_byprop
from sklearn.linear_model import LinearRegression
from time import time, sleep, strftime, gmtime
from .stream import find_muse
from .muse import Muse


def record(duration, filename=None, dejitter=False):
    if not filename:
        filename = ("recording_%s.csv" %
                    strftime("%Y-%m-%d-%H.%M.%S", gmtime()))

    print("looking for an EEG stream...")
    streams = resolve_byprop('type', 'EEG', timeout=2)

    if len(streams) == 0:
        raise(RuntimeError, "Can't find EEG stream")

    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=12)
    # eeg_time_correction = inlet.time_correction()

    print("looking for a Markers stream...")
    marker_streams = resolve_byprop('name', 'Markers', timeout=2)

    if marker_streams:
        inlet_marker = StreamInlet(marker_streams[0])
        # marker_time_correction = inlet_marker.time_correction()
    else:
        inlet_marker = False
        print("Can't find Markers stream")

    info = inlet.info()
    description = info.desc()

    # freq = info.nominal_srate()
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
    print('Start recording at time t=%.3f' % t_init)
    print('Time correction: ', time_correction)
    while (time() - t_init) < duration:

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
    print('Time correction: ', time_correction)

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

    if inlet_marker:
        n_markers = len(markers[0][0])
        for ii in range(n_markers):
            data['Marker%d' % ii] = 0
        # process markers:
        for marker in markers:
            # find index of markers
            ix = np.argmin(np.abs(marker[1] - timestamps))
            for ii in range(n_markers):
                data.loc[ix, 'Marker%d' % ii] = marker[0][ii]

    data.to_csv(filename, float_format='%.3f', index=False)

    print('Done!')


def record_direct(address, backend, interface, name, filename):


if backend == 'bluemuse':
    raise(NotImplementedError(
        'Direct record not supported with BlueMuse backend. Use lslrecord instead.'))

if not address:
    found_muse = find_muse(name)
    if not found_muse:
        print('Muse could not be found')
        return
    else:
        address = found_muse['address']
        name = found_muse['name']
    print('Connecting to %s : %s...' %
          (name if name else 'Muse', address))

if not filename:
    filename = ("recording_%s.csv" %
                strftime("%Y-%m-%d-%H.%M.%S", gmtime()))

eeg_samples = []
timestamps = []


def save_eeg(new_samples, new_timestamps):
    eeg_samples.append(new_samples)
    timestamps.append(new_timestamps)


muse = Muse(address, save_eeg)

muse.connect()
muse.start()

print('Start recording at time t=%.3f' % time())

while 1:
    try:
        sleep(1)
    except:
        break

muse.stop()
muse.disconnect()

timestamps = np.concatenate(timestamps)
eeg_samples = np.concatenate(eeg_samples, 1).T
recording = pd.DataFrame(data=eeg_samples,
                         columns=['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX'])

recording['timestamps'] = timestamps
recording.to_csv(filename, float_format='%.3f')

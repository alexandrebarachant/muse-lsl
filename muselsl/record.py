import csv
import os
from pathlib import Path
from time import time, sleep, strftime, gmtime

import numpy as np
import pandas as pd
from pylsl import StreamInlet, resolve_byprop

from .constants import LSL_SCAN_TIMEOUT, ChunkLength
from .muse import Muse
from .stream import find_muse


def record(filename, data_source="EEG", abort=None, source_id=None):
    """Records a fixed duration of EEG data from an LSL stream into a CSV file"""

    float_precision = 3

    directory = Path(filename).parent
    directory.mkdir(parents=True, exist_ok=True)

    csv_file = Path(filename).open("w")
    writer = csv.writer(csv_file, lineterminator="\n")

    chunk_length = ChunkLength[data_source]

    print("Looking for a {data_source} stream...")
    streams = resolve_byprop('type', data_source, timeout=LSL_SCAN_TIMEOUT)

    if len(streams) == 0:
        print(f"Can't find {data_source} stream.")
        return

    if source_id is not None:
        streams = [s for s in streams if s.source_id() == 'Muse%s' % source_id]
        assert len(
            streams) == 1, f"Expected to find exactly one stream with source_id: {'Muse%s' % source_id}, but found {len(streams)}"

    inlet = StreamInlet(streams[0], max_chunklen=chunk_length)
    print("Started acquiring data.")

    info = inlet.info()
    description = info.desc()

    ch = description.child('channels').first_child()
    ch_names = [ch.child_value('label')]
    for i in range(1, info.channel_count()):
        ch = ch.next_sibling()
        ch_names.append(ch.child_value('label'))

    columns = ['timestamps'] + ch_names
    writer.writerow(columns)

    first_iteration = True

    while not abort.is_set():
        data, timestamp = inlet.pull_chunk(timeout=1.0,
                                           max_samples=chunk_length)
        ts = np.array(timestamp) + inlet.time_correction()
        if timestamp:
            tmp = np.c_[ts, data]
            formatted = [[f"{x:.{float_precision}f}" for x in row] for row in tmp]
            writer.writerows(formatted)

        if first_iteration:
            first_iteration = False
            print(f"[Success] Started recording of {data_source}")

    print(f"[Success] Stopped recording of {data_source}")


def record_direct(duration, address, filename=None, backend='auto', interface=None, name=None):
    """Rercord directly from a Muse without the use of LSL"""
    if backend == 'bluemuse':
        raise (NotImplementedError(
            'Direct record not supported with BlueMuse backend. Use record after starting stream instead.'))

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
        filename = os.path.join(os.getcwd(), ("recording_%s.csv" %
                                              strftime("%Y-%m-%d-%H.%M.%S", gmtime())))

    eeg_samples = []
    timestamps = []

    def save_eeg(new_samples, new_timestamps):
        eeg_samples.append(new_samples)
        timestamps.append(new_timestamps)

    muse = Muse(address, save_eeg)
    muse.connect()
    muse.start()

    t_init = time()
    print('Start recording at time t=%.3f' % t_init)

    while (time() - t_init) < duration:
        try:
            sleep(1)
        except KeyboardInterrupt:
            break

    muse.stop()
    muse.disconnect()

    timestamps = np.concatenate(timestamps)
    eeg_samples = np.concatenate(eeg_samples, 1).T
    recording = pd.DataFrame(data=eeg_samples,
                             columns=['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX'])

    recording['timestamps'] = timestamps

    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)

    recording.to_csv(filename, float_format='%.3f')
    print('Done - wrote file: ' + filename + '.')

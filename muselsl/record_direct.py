from .stream import find_muse
from .muse import Muse
from time import time, sleep, strftime, gmtime
import numpy as np
import pandas as pd


def record(address, backend, interface, name, filename):
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

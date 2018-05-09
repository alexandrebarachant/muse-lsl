from muse import Muse
from time import sleep
import numpy as np
import pandas as pd


def record(address, backend, interface, name, filename):
    if backend == 'bluemuse':
        raise(NotImplementedError(
            'Direct record not supported with BlueMuse backend. Use lslrecord instead.'))

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

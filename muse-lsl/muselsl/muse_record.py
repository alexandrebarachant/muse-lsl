from muse import Muse
from time import sleep
import numpy as np
import pandas as pd

full_time = []
full_data = []

def __process__(data, timestamps):
    full_time.append(timestamps)
    full_data.append(data)

def record(address):
    muse = Muse(address, process)

    muse.connect()
    muse.start()

    while 1:
        try:
            sleep(1)
        except:
            break

    muse.stop()
    muse.disconnect()

    full_time = np.concatenate(full_time)
    full_data = np.concatenate(full_data, 1).T
    res = pd.DataFrame(data=full_data,
                       columns=['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX'])

    res['timestamps'] = full_time
    res.to_csv('dump.csv', float_format='%.3f')

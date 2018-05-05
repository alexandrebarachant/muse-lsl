from muse import Muse
from time import sleep
from pylsl import StreamInfo, StreamOutlet, local_clock
from optparse import OptionParser

def process(data, timestamps):
        for ii in range(12):
            outlet.push_sample(data[:, ii], timestamps[ii])

def stream(address, backend, interface, name):
    info = info = StreamInfo('Muse', 'EEG', 5, 256, 'float32',
                         'Muse%s' % address)

    info.desc().append_child_value("manufacturer", "Muse")
    channels = info.desc().append_child("channels")

    for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
        channels.append_child("channel") \
            .append_child_value("label", c) \
            .append_child_value("unit", "microvolts") \
            .append_child_value("type", "EEG")
    outlet = StreamOutlet(info, 12, 360)
    muse = Muse(address=address, callback_eeg=process,
                backend=backend, time_func=local_clock,
                interface=interface, name=name)

    muse.connect()
    print('Connected')
    muse.start()
    print('Streaming')

    while 1:
        try:
            sleep(1)
        except:
            break

    muse.stop()
    muse.disconnect()
    print('Disonnected')

"""
Command-line utility to connect to a Muse 2016 headband and stream the data
with the Lab Streaming Layer (LSL).
"""

from time import sleep
from optparse import OptionParser
from functools import partial

from pylsl import StreamInfo, StreamOutlet

from muse import Muse


parser = OptionParser()
parser.add_option("-a", "--address",
                  dest="address", type='string', default=None,
                  help="device mac address.")
parser.add_option("-n", "--name",
                  dest="name", type='string', default=None,
                  help="name of the device.")
parser.add_option("-b", "--backend",
                  dest="backend", type='string', default="auto",
                  help="pygatt backend to use. can be auto, gatt or bgapi")
parser.add_option("-i", "--interface",
                  dest="interface", type='string', default=None,
                  help="The interface to use, 'hci0' for gatt or a COM port for bgapi")

(options, args) = parser.parse_args()

# Set up EEG stream
info = StreamInfo('Muse', 'EEG', 5, 256, 'float32',
                  'Muse%s' % options.address)

info.desc().append_child_value("manufacturer", "Muse")
channels = info.desc().append_child("channels")

for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
    channels.append_child("channel") \
        .append_child_value("label", c) \
        .append_child_value("unit", "microvolts") \
        .append_child_value("type", "EEG")
outlet_eeg = StreamOutlet(info, 12, 360)

# Set up accelerometer stream
info = StreamInfo('Muse', 'ACC', 3, 52, 'float32',
                  'Muse%s' % options.address)

info.desc().append_child_value("manufacturer", "Muse")
channels = info.desc().append_child("channels")

for c in ['X', 'Y', 'Z']:
    channels.append_child("channel") \
        .append_child_value("label", c) \
        .append_child_value("unit", "g") \
        .append_child_value("type", "accelerometer")
outlet_acc = StreamOutlet(info, 1, 360)

# Set up gyroscope stream
info = StreamInfo('Muse', 'GYRO', 3, 52, 'float32',
                  'Muse%s' % options.address)

info.desc().append_child_value("manufacturer", "Muse")
channels = info.desc().append_child("channels")

for c in ['X', 'Y', 'Z']:
    channels.append_child("channel") \
        .append_child_value("label", c) \
        .append_child_value("unit", "dps") \
        .append_child_value("type", "gyroscope")
outlet_gyro = StreamOutlet(info, 1, 360)


def process(timestamps, data, outlet):
    for ii in range(data.shape[1]):
        outlet.push_sample(data[:, ii], timestamps[ii])


process_eeg = partial(process, outlet=outlet_eeg)
process_acc = partial(process, outlet=outlet_acc)
process_gyro = partial(process, outlet=outlet_gyro)

muse = Muse(address=options.address, callback_eeg=process_eeg,
            callback_control=None, callback_telemetry=None,
            callback_acc=process_acc, callback_gyro=process_gyro,
            backend=options.backend, interface=options.interface,
            name=options.name)

muse.connect()
print('Connected')
muse.start()
print('Streaming')

while 1:
    try:
        sleep(1)
    except Exception as e:
        break

muse.stop()
muse.disconnect()
print('Disconnected')

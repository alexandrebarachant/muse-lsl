from muse import Muse
from time import sleep
from pylsl import StreamInfo, StreamOutlet, local_clock
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-a", "--address",
                  dest="address", type='string', default=None,
                  help="device mac adress.")
parser.add_option("-n", "--name",
                  dest="name", type='string', default=None,
                  help="name of the device.")
parser.add_option("-b", "--backend",
                  dest="backend", type='string', default="auto",
                  help="pygatt backend to use. can be auto, gatt or bgapi")
parser.add_option("-i", "--interface",
                  dest="interface", type='string', default=None,
                  help="The interface to use, 'hci0' for gatt or a com port for bgapi")

(options, args) = parser.parse_args()

info = info = StreamInfo('Muse', 'EEG', 5, 256, 'float32',
                         'Muse%s' % options.address)

info.desc().append_child_value("manufacturer", "Muse")
channels = info.desc().append_child("channels")

for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
    channels.append_child("channel") \
        .append_child_value("label", c) \
        .append_child_value("unit", "microvolts") \
        .append_child_value("type", "EEG")
outlet = StreamOutlet(info, 12, 360)


def process(data, timestamps):
    for ii in range(12):
        outlet.push_sample(data[:, ii], timestamps[ii])

muse = Muse(address=options.address, callback=process,
            backend=options.backend, time_func=local_clock,
            interface=options.interface, name=options.name)

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

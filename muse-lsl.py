from muse import Muse
from time import sleep
from pylsl import StreamInfo, StreamOutlet
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-a", "--address",
                  dest="address", type='string', default="00:55:DA:B0:06:D6",
                  help="device mac adress.")

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

muse = Muse(address=options.address, callback=process)

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

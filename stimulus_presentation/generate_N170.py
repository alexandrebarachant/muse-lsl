"""
Generate N170
=============

Face vs. house paradigm stimulus presentation for evoking N170.

"""

from time import time
from optparse import OptionParser
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event
from pylsl import StreamInfo, StreamOutlet, local_clock

parser = OptionParser()
parser.add_option("-d", "--duration",
                  dest="duration", type='int', default=400,
                  help="duration of the recording in seconds.")

(options, args) = parser.parse_args()

# Create markers stream outlet
info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'myuidw43536')
outlet = StreamOutlet(info)

markernames = [1, 2]
start = time()

# Set up trial parameters
n_trials = 2010
iti = 0.3
soa = 0.2
jitter = 0.2
record_duration = np.float32(options.duration)

# Setup trial list
image_type = np.random.binomial(1, 0.5, n_trials)
trials = DataFrame(dict(image_type=image_type,
                        timestamp=np.zeros(n_trials)))


# Setup graphics
def load_image(filename):
    return visual.ImageStim(win=mywin, image=filename)


mywin = visual.Window([1920, 1080], monitor='testMonitor', units='deg',
                      fullscr=True)
faces = map(load_image, glob('stimulus_presentation/stim/face_house/faces/*_3.jpg'))
houses = map(load_image, glob('stimulus_presentation/stim/face_house/houses/*.3.jpg'))

for ii, trial in trials.iterrows():
    # Intertrial interval
    core.wait(iti + np.random.rand() * jitter)

    # Select and display image
    label = trials['image_type'].iloc[ii]
    image = choice(faces if label == 1 else houses)
    image.draw()

    # Send marker
    timestamp = local_clock()
    outlet.push_sample([markernames[label]], timestamp)
    mywin.flip()

    # offset
    core.wait(soa)
    mywin.flip()
    if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        break
    event.clearEvents()

# Cleanup
mywin.close()

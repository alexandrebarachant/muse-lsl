"""
Generate spatial gratings
=========================

Stimulus presentation based on gratings of different spatial frequencies
for generating ERPs, high frequency oscillations, and alpha reset.

Inspired from:

> Hermes, Dora, K. J. Miller, B. A. Wandell, and Jonathan Winawer. "Stimulus
dependence of gamma oscillations in human visual cortex." Cerebral Cortex 25,
no. 9 (2015): 2951-2959.

"""

from time import time
from optparse import OptionParser

import numpy as np
import pandas as pd
from psychopy import visual, core, event
from pylsl import StreamInfo, StreamOutlet, local_clock


parser = OptionParser()
parser.add_option("-d", "--duration",
                  dest="duration", type='int', default=400,
                  help="duration of the recording in seconds.")

(options, args) = parser.parse_args()

# Create markers stream outlet
info = StreamInfo('Markers', 'Markers', 3, 0, 'float32', 'myuidw43536')
channels = info.desc().append_child("channels")

for c in ['Frequency', 'Contrast', 'Orientation']:
    channels.append_child("channel") \
        .append_child_value("label", c)

outlet = StreamOutlet(info)

start = time()

# Set up trial parameters
n_trials = 2010
iti = 1.0
soa = 1.5
jitter = 0.5
record_duration = np.float32(options.duration)

# Setup trial list
frequency = np.random.binomial(1, 0.5, n_trials)
contrast = np.ones(n_trials, dtype=int)
orientation = np.random.randint(0, 4, n_trials) * 45

trials = pd.DataFrame(dict(frequency=frequency,
                           contrast=contrast,
                           orientation=orientation))

# graphics
mywin = visual.Window([1920, 1080], monitor="testMonitor", units="deg",
                      fullscr=True)
grating = visual.GratingStim(win=mywin, mask='circle', size=40, sf=4)
fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0,
                              rgb=[1, 0, 0])

rs = np.random.RandomState(42)

core.wait(2)

for ii, trial in trials.iterrows():

    # onset
    fre = trials['frequency'].iloc[ii]
    contrast = trials['contrast'].iloc[ii]
    ori = trials['orientation'].iloc[ii]
    grating.sf = 4 * fre + 0.1
    grating.ori = ori
    grating.contrast = contrast
    grating.draw()
    fixation.draw()

    # Send marker
    outlet.push_sample([fre + 1, contrast, ori], local_clock())
    mywin.flip()

    # offset
    core.wait(soa)
    fixation.draw()
    outlet.push_sample([fre + 3, contrast, ori], local_clock())
    mywin.flip()

    if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        break
    event.clearEvents()

    # Intertrial interval
    core.wait(iti + np.random.rand() * jitter)

# Cleanup
mywin.close()

"""
Generate spatial gratings
=========================

Stimulus presentation based on gratings of different spatial frequencies
for generating ERPs, high frequency oscillations, and alpha reset.

Inspired by ??? (iEEG paper)

TODO:
    - Add reference
    - Add CSV file inside final directory

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

# create
info = StreamInfo('Markers', 'Markers', 3, 0, 'float32', 'myuidw43536')
channels = info.desc().append_child("channels")

for c in ['Frequency', 'Contrast', 'Orientation']:
    channels.append_child("channel") \
        .append_child_value("label", c)

# next make an outlet
outlet = StreamOutlet(info)

trials = pd.read_csv('/home/hubert/Downloads/electrode-benchmark 2/stimulus.csv',
                     index_col=0)

start = time()

n_trials = len(trials)
record_duration = np.float32(options.duration)


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
    fre = trials['Frequency'].iloc[ii]
    contrast = trials['Contrast'].iloc[ii]
    ori = trials['Orientation'].iloc[ii]
    grating.sf = 4 * fre + 0.1
    grating.ori = ori
    grating.contrast = contrast
    grating.draw()
    fixation.draw()

    # Send marker
    outlet.push_sample([fre + 1, contrast, ori], local_clock())
    mywin.flip()

    # offset
    core.wait(trials['Duration'].iloc[ii])
    fixation.draw()
    outlet.push_sample([fre + 3, contrast, ori], local_clock())
    mywin.flip()

    if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        break
    event.clearEvents()

    # inter-trial interval
    w = trials['Duration'].iloc[ii] + trials['Interval'].iloc[ii]
    core.wait(w)

# Cleanup
mywin.close()

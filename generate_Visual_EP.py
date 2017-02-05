import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event
from time import time, strftime, gmtime
from optparse import OptionParser
from pylsl import StreamInfo, StreamOutlet

parser = OptionParser()
parser.add_option("-d", "--duration",
                  dest="duration", type='int', default=400,
                  help="duration of the recording in seconds.")

(options, args) = parser.parse_args()

# create
info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'myuidw43536')

# next make an outlet
outlet = StreamOutlet(info)

markernames = [1, 2]

start = time()

n_trials = 2000
iti = .2
jitter = .1
soa = 0.2
record_duration = np.float32(options.duration)

# Setup log
position = np.random.randint(0, 2, n_trials)
trials = DataFrame(dict(position=position,
                        timestamp=np.zeros(n_trials)))

# graphics
mywin = visual.Window([1920, 1080], monitor="testMonitor", units="deg",
                      fullscr=True)
grating = visual.GratingStim(win=mywin, mask='circle', size=20, sf=4)
fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0,
                              rgb=[1, 0, 0])

for ii, trial in trials.iterrows():
    # inter trial interval
    core.wait(iti + np.random.rand() * jitter)

    # onset
    grating.phase += np.random.rand()
    pos = trials['position'].iloc[ii]
    grating.pos = [25*(pos-0.5), 0]
    grating.draw()
    fixation.draw()
    outlet.push_sample([markernames[pos]], time())
    mywin.flip()

    # offset
    core.wait(soa)
    fixation.draw()
    mywin.flip()
    if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        break
    event.clearEvents()
# Cleanup
mywin.close()

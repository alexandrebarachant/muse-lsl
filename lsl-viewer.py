#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from time import time
from pylsl import StreamInlet, resolve_byprop
import seaborn as sns
sns.set(style="whitegrid")

from optparse import OptionParser

parser = OptionParser()

parser.add_option("-w", "--window",
                  dest="window", type='float', default=5.,
                  help="window lenght to display in seconds.")
parser.add_option("-s", "--scale",
                  dest="scale", type='float', default=100,
                  help="scale in uV")
parser.add_option("-r", "--refresh",
                  dest="refresh", type='float', default=0.2,
                  help="refresh rate in seconds.")
parser.add_option("-f", "--figure",
                  dest="figure", type='string', default="15x6",
                  help="window size.")
parser.add_option("-a", "--avgref",
                  dest="avgref", action="store_false", default=False,
                  help="Activate average reference.")

filt = True
subsample = 2
buf = 12

(options, args) = parser.parse_args()

figsize = np.int16(options.figure.split('x'))

print("looking for an EEG stream...")
streams = resolve_byprop('type', 'EEG', timeout=2)

if len(streams) == 0:
    raise(RuntimeError, "Cant find EEG stream")
print("Start aquiring data")

inlet = StreamInlet(streams[0], max_chunklen=buf)

info = inlet.info()
description = info.desc()

freq = info.nominal_srate()
Nchan = info.channel_count()

ch = description.child('channels').first_child()
ch_names = [ch.child_value('label')]
for i in range(Nchan):
    ch = ch.next_sibling()
    ch_names.append(ch.child_value('label'))

picks = range(Nchan)
# create a new inlet to read from the stream

frs = np.fft.fftfreq(n=128, d=1.0/freq)

ix_noise = (frs > 55) & (frs < 65)
ix_signal = (frs > 25) & (frs < 35)

to_read = int(options.window * (freq / buf))
Nchan_plot = len(ch_names)

res = []
t_init = time()
k = 0
while k < to_read:
    data, timestamps = inlet.pull_chunk(timeout=1.0, max_samples=buf)
    if timestamps:
        res.append(data)
        k += 1
dur = time() - t_init
data = np.concatenate(res, axis=0)

if options.avgref:
    data -= np.atleast_2d(data.mean(1)).T
ffts = np.abs(np.fft.fft(data[:, 0:], n=128, axis=0))
dur = data[-1, 0] - data[0, 0]

bf, af = butter(4, np.array([1, 40])/(freq/2.), 'bandpass')

# You probably won't need this if you're embedding things in a tkinter plot...
plt.ion()

fig, axes = plt.subplots(1, 1, figsize=figsize,
                         sharex=True)
sns.despine(left=True)


time = np.arange(len(data))/freq

lines = []
impedances = np.log(ffts[ix_noise].mean(0)) / np.log(ffts[ix_signal].mean(0))

for i, ix in enumerate(picks):
    line, = axes.plot(time[::subsample],
                      data[::subsample, ix] - (i * options.scale * 2),
                      lw=1)
    lines.append(line)
vmin = 0
vmax = 0
axes.set_ylim(-len(picks) * options.scale * 2,
              2 * options.scale)
ticks = np.arange(0, -Nchan * options.scale * 2, -options.scale * 2)

axes.set_yticks(ticks)
axes.get_xaxis().set_visible(False)

ticks_labels = ['%s - %.1f' % (ch_names[i], impedances[i])
                for i in picks]
axes.set_yticklabels(ticks_labels)
plt.show()

display_every = int(options.refresh / (buf/freq))
k = 0
while 1:
    try:
        data, timestamps = inlet.pull_chunk(timeout=1.0, max_samples=buf)
        if timestamps:
            res.append(data)
            res.pop(0)
            k += 1
            if k == display_every:
                data = np.concatenate(res, axis=0)
                if options.avgref:
                    data -= np.atleast_2d(data.mean(1)).T
                #ffts = np.abs(np.fft.fft(data[:, 1:], n=128, axis=0))

                if filt:
                    data = filtfilt(bf, af, data, axis=0)
                for i, ix in enumerate(picks):
                    lines[i].set_ydata(data[::subsample, ix] -
                                       (i * options.scale * 2))
                    # axes.relim()
                    # axes.autoscale_view()
                #impedances = (np.log(ffts[ix_noise].mean(0)) /
                #              np.log(ffts[ix_signal].mean(0)))
                impedances = np.std(data[:, 0:], 0)
                ticks_labels = ['%s - %.2f' % (ch_names[i], impedances[i])
                                for i in picks]
                axes.set_yticklabels(ticks_labels)
                fig.canvas.draw()
                k = 0
    except KeyboardInterrupt:
        break

import numpy as np
import matplotlib
from scipy.signal import lfilter, lfilter_zi, firwin
from time import sleep
from pylsl import StreamInlet, resolve_byprop
import seaborn as sns
from threading import Thread
from .constants import VIEW_BUFFER, VIEW_SUBSAMPLE, LSL_SCAN_TIMEOUT, LSL_EEG_CHUNK


def view(window, scale, refresh, figure, backend, version=1):
    matplotlib.use(backend)
    sns.set(style="whitegrid")

    figsize = np.int16(figure.split('x'))

    print("Looking for an EEG stream...")
    streams = resolve_byprop('type', 'EEG', timeout=LSL_SCAN_TIMEOUT)

    if len(streams) == 0:
        raise(RuntimeError("Can't find EEG stream."))
    print("Start acquiring data.")

    fig, axes = matplotlib.pyplot.subplots(1, 1, figsize=figsize, sharex=True)
    lslv = LSLViewer(streams[0], fig, axes, window, scale)
    fig.canvas.mpl_connect('close_event', lslv.stop)

    help_str = """
                toggle filter : d
                toogle full screen : f
                zoom out : /
                zoom in : *
                increase time scale : -
                decrease time scale : +
               """
    print(help_str)
    lslv.start()
    matplotlib.pyplot.show()


class LSLViewer():
    def __init__(self, stream, fig, axes, window, scale, dejitter=True):
        """Init"""
        self.stream = stream
        self.window = window
        self.scale = scale
        self.dejitter = dejitter
        self.inlet = StreamInlet(stream, max_chunklen=LSL_EEG_CHUNK)
        self.filt = True
        self.subsample = VIEW_SUBSAMPLE

        info = self.inlet.info()
        description = info.desc()

        self.sfreq = info.nominal_srate()
        self.n_samples = int(self.sfreq * self.window)
        self.n_chan = info.channel_count()

        ch = description.child('channels').first_child()
        ch_names = [ch.child_value('label')]

        for i in range(self.n_chan):
            ch = ch.next_sibling()
            ch_names.append(ch.child_value('label'))

        self.ch_names = ch_names

        fig.canvas.mpl_connect('key_press_event', self.OnKeypress)
        fig.canvas.mpl_connect('button_press_event', self.onclick)

        self.fig = fig
        self.axes = axes

        sns.despine(left=True)

        self.data = np.zeros((self.n_samples, self.n_chan))
        self.times = np.arange(-self.window, 0, 1. / self.sfreq)
        impedances = np.std(self.data, axis=0)
        lines = []

        for ii in range(self.n_chan):
            line, = axes.plot(self.times[::self.subsample],
                              self.data[::self.subsample, ii] - ii, lw=1)
            lines.append(line)
        self.lines = lines

        axes.set_ylim(-self.n_chan + 0.5, 0.5)
        ticks = np.arange(0, -self.n_chan, -1)

        axes.set_xlabel('Time (s)')
        axes.xaxis.grid(False)
        axes.set_yticks(ticks)

        ticks_labels = ['%s - %.1f' % (ch_names[ii], impedances[ii])
                        for ii in range(self.n_chan)]
        axes.set_yticklabels(ticks_labels)

        self.display_every = int(0.2 / (12 / self.sfreq))

        self.bf = firwin(32, np.array([1, 40]) / (self.sfreq / 2.), width=0.05,
                         pass_zero=False)
        self.af = [1.0]

        zi = lfilter_zi(self.bf, self.af)
        self.filt_state = np.tile(zi, (self.n_chan, 1)).transpose()
        self.data_f = np.zeros((self.n_samples, self.n_chan))

    def update_plot(self):
        k = 0
        try:
            while self.started:
                samples, timestamps = self.inlet.pull_chunk(timeout=1.0,
                                                            max_samples=LSL_EEG_CHUNK)

                if timestamps:
                    if self.dejitter:
                        timestamps = np.float64(np.arange(len(timestamps)))
                        timestamps /= self.sfreq
                        timestamps += self.times[-1] + 1. / self.sfreq
                    self.times = np.concatenate([self.times, timestamps])
                    self.n_samples = int(self.sfreq * self.window)
                    self.times = self.times[-self.n_samples:]
                    self.data = np.vstack([self.data, samples])
                    self.data = self.data[-self.n_samples:]
                    filt_samples, self.filt_state = lfilter(
                        self.bf, self.af,
                        samples,
                        axis=0, zi=self.filt_state)
                    self.data_f = np.vstack([self.data_f, filt_samples])
                    self.data_f = self.data_f[-self.n_samples:]
                    k += 1
                    if k == self.display_every:

                        if self.filt:
                            plot_data = self.data_f
                        elif not self.filt:
                            plot_data = self.data - self.data.mean(axis=0)
                        for ii in range(self.n_chan):
                            self.lines[ii].set_xdata(self.times[::self.subsample] -
                                                     self.times[-1])
                            self.lines[ii].set_ydata(plot_data[::self.subsample, ii] /
                                                     self.scale - ii)
                            impedances = np.std(plot_data, axis=0)

                        ticks_labels = ['%s - %.2f' % (self.ch_names[ii],
                                                       impedances[ii])
                                        for ii in range(self.n_chan)]
                        self.axes.set_yticklabels(ticks_labels)
                        self.axes.set_xlim(-self.window, 0)
                        self.fig.canvas.draw()
                        k = 0
                else:
                    sleep(0.2)
        except RuntimeError as e:
            raise

    def onclick(self, event):
        print((event.button, event.x, event.y, event.xdata, event.ydata))

    def OnKeypress(self, event):
        if event.key == '/':
            self.scale *= 1.2
        elif event.key == '*':
            self.scale /= 1.2
        elif event.key == '+':
            self.window += 1
        elif event.key == '-':
            if self.window > 1:
                self.window -= 1
        elif event.key == 'd':
            self.filt = not(self.filt)

    def start(self):
        self.started = True
        self.thread = Thread(target=self.update_plot)
        self.thread.daemon = True
        self.thread.start()

    def stop(self, close_event):
        self.started = False

import argparse
import math, time
import numpy

from pythonosc import dispatcher
from pythonosc import osc_server

class Muse_2014():
    """Muse 2014 headband"""

    def __init__(self):
        """Initialize muse 2014"""
        # connection start time (needed for time-stamping)
        print("Initializing Muse 2014 Devices")
        #Device is initially not connected
        self.connected = False
        #Initialize port number and ip
        self.ip = "127.0.0.1"
        self.port = 5000
        #Initialize server
        self.server = None
        #Initialize timestamp array
        self.timestamps = []
        self.perfect_freq = []
        self.samples = 0
        #frequency
        self.freq_mult = 1. / 220
        #Initailize a dispatcher
        self._dispatcher = dispatcher.Dispatcher()
        self._dispatcher.map("/debug", print)
        self._dispatcher.map("/muse/eeg", self.eeg_handler,self)

    def connect(self):
        """Connect to the Muse headset, but no stream"""
        self.server = osc_server.ThreadingOSCUDPServer(
                (self.ip, self.port), self._dispatcher)
        print("Serving on {}".format(self.server.server_address))

    def start(self):
        """Start streaming data"""
        print("Starting to stream data\n")
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop streaming data"""
        self.server.shutdown()
        perc_avg_sum = 0
        perc_avg = 0
        for count in range(len(self.timestamps)):
            print(str(count)+'\n')
            diff = self.timestamps[count] - (self.timestamps[0]+self.freq_mult*count)
            self.perfect_freq.append((diff/self.timestamps[count]) * 100)
            perc_avg_sum += self.perfect_freq[count]
        perc_avg = perc_avg_sum/(len(self.timestamps))
        self.perfect_freq.append(perc_avg)
        save_file = numpy.asarray(self.perfect_freq)
        numpy.savetxt("timestamps.csv", save_file, delimiter=",")

    def eeg_handler(self,unusedAddr, args, ch1, ch2, ch3, ch4):
        """Print the Voltage values of each channel"""
        self.timestamps.append(time.time())

if __name__ == "__main__":
    muse_2014 = Muse_2014()
    muse_2014.connect()
    muse_2014.start()
    time.sleep(5000)
    muse_2014.stop()

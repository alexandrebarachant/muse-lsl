import argparse
import math
import time
import numpy
from pythonosc import dispatcher, osc_server
import subprocess


class Muse2014:
    """
    Function: Provides helper functions for Muse 2014 headband

    Methods:
    - Connect: Connects to the Muse 2014 headband
    - Start: Starts streaming the data
    - Stop: Stops streaming the data
    - Resume: Resumes streaming the data
    - Pause: Pauses streaming the data
    - Close(to be implemented): Closes the connection with the device

    Other Methods:
    - eeg_handler: Timestamps and transforms the data
    """

    def __init__(self, address, ip="127.0.0.1", port=5000, time_func=time.time, callback_eeg=None, name=None):
        """
        Function: Initializes muse 2014
        Args:
            - ip and port: ip and port to use for Streaming
            - time_func: user's function for Timestamping
            - callback_eeg:
        Returns: None
        """
        print("Initializing Muse 2014 Devices")
        # Device is initially not connected
        self.connected = False
        self.muse_io = None
        self.address = address
        self.name = name
        # Initialize port number and ip
        self.ip = ip
        self.port = port
        # Initialize server
        self.server = None
        # Initialize timestamp array
        self.timestamps = []
        # Initialize time function and callback_eeg
        self.time_func = time_func
        self.callback_eeg = callback_eeg
        # Initialize data
        self.data = []
        # Initialize a dispatcher
        self._dispatcher = dispatcher.Dispatcher()
        self._dispatcher.map("/debug", print)
        self._dispatcher.map("/muse/eeg", self.eeg_handler, self)

    def connect(self):
        """
        Function: Connect to the Muse headset, but no streaming is done yet
        Returns: None
        """
        print('Connecting to %s : %s...' % (self.name if self.name else 'Muse', self.address))
        self.muse_io = subprocess.Popen('exec ./connect_muse_2014.sh {} {}'.format(self.address, self.port), shell=True)
        if self.connected:
            print("Sorry, headset already connected")
        else:
            self.server = osc_server.ThreadingOSCUDPServer(
                    (self.ip, self.port), self._dispatcher)
            print("Serving on {}".format(self.server.server_address))

    def start(self):
        """
        Function: Start streaming data
        Returns: None
        """
        print("Starting to stream data\n")
        self.resume()

    def stop(self):
        """
        Function: Stop streaming data, but connection not closed
                  This means that you can start streaming data again using the start method
        Returns: None
        """
        # Stops Streaming the data
        self.server.shutdown()

    def resume(self):
        """
        Function: Resumes streaming the data
        Returns: None
        """
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            # Stops streaming on keyboard interrupt
            self.stop()

    def disconnect(self):
        """disconnect."""
        if self.muse_io:
            self.muse_io.kill()

    def eeg_handler(self, unusedAddr, args, ch1, ch2, ch3, ch4):
        """
        Function: Does real time timestamping. Any other minor data manipulation must be done here
        Args:
            - ch1, ch2, ch3, ch4 -> Indicates channels streamed from the EEGs on the device
        Returns: None
        """
        current_time = self.time_func()
        self.timestamps.append(current_time)
        self.callback_eeg(ch1, ch2, ch3, ch4, current_time)


""" FOR TESTING PURPOSES ONLY """
# Please uncomment this part if you want to test the code
# Trigger a keyboard interrupt if you would like to stop the code
# if __name__ == "__main__":
#     muse_2014 = Muse2014()
#     muse_2014.connect()
#     muse_2014.start()

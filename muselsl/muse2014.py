import argparse
import math, time
import numpy

from pythonosc import dispatcher
from pythonosc import osc_server

class Muse_2014():
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


    def __init__(self, ip="127.0.0.1", port=5000, time_func = time.time(), callback_eeg=None):
        """
        Function: Initializes muse 2014
        Args:
            - ip and port: ip and port to use for Streaming
            - time_func: user's function for Timestamping
            - callback_eeg:
        Returns: None
        """
        print("Initializing Muse 2014 Devices")
        #Device is initially not connected
        self.connected = False
        #Initialize port number and ip
        self.ip = ip
        self.port = port
        #Initialize server
        self.server = None
        #Initialize timestamp array
        self.timestamps = []
        #Intialize time fucntion and callback_eeg
        self.time_func = time_func
        self.callback_eeg = callback_eeg
        #Intialize data
        self.data = []
        #Initailize a dispatcher
        self._dispatcher = dispatcher.Dispatcher()
        self._dispatcher.map("/debug", print)
        self._dispatcher.map("/muse/eeg", self.eeg_handler,self)


    def connect(self):
        """
        Function: Connect to the Muse headset, but no streaming is done yet
        Returns: None
        """
        if(self.connected == True): print("Sorry, headset already connected")
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
        try:
            self.server.serve_forever()
        except KeyboardInterrupt: #Stops streaming on keyboard interrupt
            self.stop()


    def stop(self):
        """
        Function: Stop streaming data, but connection not closed
                  This means that you can start streaming data again using the start method
        Returns: None
        """
        self.server.shutdown() #Stops Streaming the data


    def resume(self):
        """
        Function: Resumes streaming the data
        Returns: None
        """
        self.start()


    def eeg_handler(self,unusedAddr, args, ch1, ch2, ch3, ch4):
        """
        Function: Does real time timestamping. Any other minor data manipulation must be done here
        Args:
            - ch1, ch2, ch3, ch4 -> Indicates channels streamed from the EEGs on the device
        Returns: None
        """
        self.timestamps.append(self.time_func())
        self.callback_eeg(ch1, ch2, ch3, ch4, self.timestamps)


""" FOR TESTING PURPOSES ONLY """
#Please uncomment this part if you want to test the code
#Trigger a keyboard interrup if you would like to stop the code
# if __name__ == "__main__":
#     muse_2014 = Muse_2014()
#     muse_2014.connect()
#     muse_2014.start()

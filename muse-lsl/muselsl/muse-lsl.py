#!/usr/bin/python
import sys
import getopt
import argparse
import re
import os
import subprocess
import configparser
from time import time, strftime, gmtime

class Program:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='muse-lsl can be used to stream and visualize EEG data from the Muse 2016 headset.',
            usage='''muse-lsl <command> [<args>]
    These are the commands:
    list        List available Muse devices. 
    stream      Start an LSL stream from Muse headset.
    record      Start LSL stream and record data from Muse headset.
    lslview     Visualize EEG data from an LSL stream.
    lslrecord   Record EEG data from an LSL stream.
        ''')

        parser.add_argument('command', help='Command to run.')

        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Incorrect usage. See help below.')
            parser.print_help()
            exit(1)

        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def list():
        parser = argparse.ArgumentParser(description='List available Muse devices.')
        import muse_stream
        muse_stream.list_devices()

    def stream(self):
        parser = argparse.ArgumentParser(description='Start an LSL stream from Muse headset.')
        parser.add_argument("-a", "--address",
                  dest="address", type=str, default=None,
                  help="device mac address.")
        parser.add_argument("-n", "--name",
                  dest="name", type=str, default=None,
                  help="name of the device.")
        parser.add_argument("-b", "--backend",
                  dest="backend", type=str, default="auto",
                  help="pygatt backend to use. can be auto, gatt or bgapi")
        parser.add_argument("-i", "--interface",
                  dest="interface", type=str, default=None,
                  help="The interface to use, 'hci0' for gatt or a com port for bgapi")
        args = parser.parse_args(sys.argv[2:])
        import muse_stream
        muse_stream.stream(args.address, args.backend, args.interface, args.name)

    def record(self):
        parser = argparse.ArgumentParser(description='Start LSL stream and record data from Muse headset.')
        parser.add_argument("-a", "--address",
                  dest="address", type=str, default="00:55:DA:B0:06:D6",
                  help="device mac address.")
        args = parser.parse_args(sys.argv[2:])
        import muse_record
        muse_record.record(args.address)

    def lsl_view(self):
        parser = argparse.ArgumentParser(description='Start viewing EEG data from an LSL stream.')
        parser.add_argument("-w", "--window",
                  dest="window", type=float, default=5.,
                  help="window length to display in seconds.")
        parser.add_argument("-s", "--scale",
                  dest="scale", type=float, default=100,
                  help="scale in uV")
        parser.add_argument("-r", "--refresh",
                  dest="refresh", type=float, default=0.2,
                  help="refresh rate in seconds.")
        parser.add_argument("-f", "--figure",
                  dest="figure", type=str, default="15x6",
                  help="window size.")
        parser.add_argument("-v", "--version",
                  dest="version", type=int, default=1,
                  help="viewer version (1 or 2) - 1 is the default stable version, 2 is in development (and takes no arguments).")
        args = parser.parse_args(sys.argv[2:])
        if args.version == 2:
            import lsl_viewer_V2
            lsl_viewer_V2.view()
        else:
            import lsl_viewer
            lsl_viewer.view(args.window, args.scale, args.refresh, args.figure)

    def lsl_record(self):
        parser = argparse.ArgumentParser(description='Record data from Muse.')
        default_fname = ("data_%s.csv" % strftime("%Y-%m-%d-%H.%M.%S", gmtime()))
        parser.add_argument("-d", "--duration",
                dest="duration", type=int, default=60,
                help="duration of the recording in seconds.")
        parser.add_argument("-f", "--filename",
                dest="filename", type=str, default=default_fname,
                help="Name of the recording file.")
        args = parser.parse_args(sys.argv[2:])
        import lsl_record
        lsl_record.record(args.duration, args.filename)

if __name__ == '__main__':
    Program()

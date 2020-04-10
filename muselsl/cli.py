#!/usr/bin/python
import sys
import argparse


class CLI:
    def __init__(self, command):
        # use dispatch pattern to invoke method with same name
        getattr(self, command)()

    def list(self):
        parser = argparse.ArgumentParser(
            description='List available Muse devices.')
        parser.add_argument("-b", "--backend",
                            dest="backend", type=str, default="auto",
                            help="BLE backend to use. Can be auto, bluemuse, gatt or bgapi.")
        parser.add_argument("-i", "--interface",
                            dest="interface", type=str, default=None,
                            help="The interface to use, 'hci0' for gatt or a com port for bgapi. WIll auto-detect if not specified")
        args = parser.parse_args(sys.argv[2:])
        from . import list_muses
        list_muses(args.backend, args.interface)

    def stream(self):
        parser = argparse.ArgumentParser(
            description='Start an LSL stream from Muse headset.')
        parser.add_argument("-a", "--address",
                            dest="address", type=str, default=None,
                            help="Device MAC address.")
        parser.add_argument("-n", "--name",
                            dest="name", type=str, default=None,
                            help="Name of the device.")
        parser.add_argument("-b", "--backend",
                            dest="backend", type=str, default="auto",
                            help="BLE backend to use. Can be auto, bluemuse, gatt or bgapi.")
        parser.add_argument("-i", "--interface",
                            dest="interface", type=str, default=None,
                            help="The interface to use, 'hci0' for gatt or a com port for bgapi.")
        parser.add_argument("-p", "--ppg",
                            default=False, action="store_true", help="Include PPG data")
        parser.add_argument("-c", "--acc",
                            default=False, action="store_true", help="Include accelerometer data")
        parser.add_argument("-g", "--gyro",
                            default=False, action="store_true", help="Include gyroscope data")
        parser.add_argument('-d', '--disable-eeg', dest='disable_eeg',
                            action='store_true', help="Disable EEG data")
        args = parser.parse_args(sys.argv[2:])
        from . import stream

        stream(args.address, args.backend,
               args.interface, args.name, args.ppg, args.acc, args.gyro, args.disable_eeg)

    def record(self):
        from .run_experiment import ExperimentalRun

        parser = argparse.ArgumentParser(
            description='Start recording of an experiment.')
        parser.add_argument("-d", "--directory",
                            dest="data_root", type=str, required=True,
                            help="Root-directory to store recorded data in.")
        parser.add_argument("-n", "--participants",
                            dest="num_participants", type=int, required=True,
                            help="The number of participants in this run.")
        parser.add_argument("-i", "--trial-id",
                            dest="trial_id", type=str, default=None,
                            help="The id of this trial. Data is stored in a subdirectory with this name."
                                 + "If no id is provided, the current timestamp is used instead.")
        args = parser.parse_args(sys.argv[2:])

        experiment = ExperimentalRun(data_root=args.data_root,
                                     num_participants=args.num_participants, trial_id=args.trial_id)
        experiment.start()

    def view(self):
        parser = argparse.ArgumentParser(
            description='View data from an LSL stream.')
        parser.add_argument("-t", "--type", type=str, default="EEG", dest="data_type",
                            help="Data type to view. Either EEG, PPG, ACC, or GYRO.")
        parser.add_argument("-w", "--window",
                            dest="window", type=float, default=5.,
                            help="Window length to display in seconds.")
        parser.add_argument("-s", "--scale",
                            dest="scale", type=float, default=100,
                            help="Scale in uV.")
        parser.add_argument("-r", "--refresh",
                            dest="refresh", type=float, default=0.2,
                            help="Refresh rate in seconds.")
        parser.add_argument("-f", "--figure",
                            dest="figure", type=str, default="15x6",
                            help="Window size.")
        parser.add_argument("-v", "--version",
                            dest="version", type=int, default=1,
                            help="Viewer version (1 or 2) - 1 is the default stable version, 2 is in development (and takes no arguments).")
        parser.add_argument("-b", "--backend",
                            dest="backend", type=str, default='TkAgg',
                            help="Matplotlib backend to use. Default: %(default)s")
        parser.add_argument("-a", "--address",
                            dest="source_id", type=str, default=None,
                            help="Device MAC address.")
        args = parser.parse_args(sys.argv[2:])
        from . import view
        view(args.window, args.scale, args.refresh,
             args.figure, args.version, args.backend, args.data_type, args.source_id)

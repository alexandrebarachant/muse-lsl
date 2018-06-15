#!/usr/bin/python
import sys
import argparse


class main:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Python package for streaming, recording, and visualizing EEG data from the Muse 2016 headset.',
            usage='''muselsl <command> [<args>]
    Available commands:
    list        List available Muse devices.
                -b --backend    BLE backend to use. can be auto, bluemuse, gatt or bgapi.
                -i --interface  The interface to use, 'hci0' for gatt or a com port for bgapi.

    stream      Start an LSL stream from Muse headset.
                -a --address    Device MAC address.
                -n --name       Device name (e.g. Muse-41D2).
                -b --backend    BLE backend to use. can be auto, bluemuse, gatt or bgapi.
                -i --interface  The interface to use, 'hci0' for gatt or a com port for bgapi.

    view     Visualize EEG data from an LSL stream.
                -w --window     Window length to display in seconds.
                -s --scale      Scale in uV.
                -r --refresh    Refresh rate in seconds.
                -f --figure     Window size.
                -v --version    Viewer version (1 or 2) - 1 is the default stable version, 2 is in development (and takes no arguments).

    record   Record EEG data from an LSL stream.
                -d --duration   Duration of the recording in seconds.
                -f --filename   Name of the recording file.
                -dj --dejitter  Whether to apply dejitter correction to timestamps.

    record_direct      Record data directly from Muse headset (no LSL).
                -a --address    Device MAC address.
                -n --name       Device name (e.g. Muse-41D2).
                -b --backend    BLE backend to use. can be auto, bluemuse, gatt or bgapi.
                -i --interface  The interface to use, 'hci0' for gatt or a com port for bgapi.
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
        args = parser.parse_args(sys.argv[2:])
        from . import stream
        stream(args.address, args.backend,
               args.interface, args.name)

    def record(self):
        parser = argparse.ArgumentParser(
            description='Record data from an LSL stream.')
        parser.add_argument("-d", "--duration",
                            dest="duration", type=int, default=60,
                            help="Duration of the recording in seconds.")
        parser.add_argument("-f", "--filename",
                            dest="filename", type=str, default=None,
                            help="Name of the recording file.")
        parser.add_argument("-dj", "--dejitter",
                            dest="dejitter", type=bool, default=True,
                            help="Whether to apply dejitter correction to timestamps.")
        args = parser.parse_args(sys.argv[2:])
        from . import record
        record(args.duration, args.filename, args.dejitter)

    def record_direct(self):
        parser = argparse.ArgumentParser(
            description='Record directly from Muse without LSL.')
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
        parser.add_argument("-d", "--duration",
                            dest="duration", type=int, default=60,
                            help="Duration of the recording in seconds.")
        parser.add_argument("-f", "--filename",
                            dest="filename", type=str, default=None,
                            help="Name of the recording file.")
        args = parser.parse_args(sys.argv[2:])
        from . import record_direct
        record_direct(args.address, args.backend,
                      args.interface, args.name, args.duration, args.filename)

    def view(self):
        parser = argparse.ArgumentParser(
            description='View EEG data from an LSL stream.')
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
        args = parser.parse_args(sys.argv[2:])
        from . import view
        view(args.window, args.scale, args.refresh, args.figure, args.version)

import argparse
import sys
from .cli import CLI


def main():
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
                -p --ppg        Include PPG data
                -c --acc        Include accelerometer data
                -g --gyro       Include gyroscope data
                --disable-eeg   Disable EEG data

    view     Visualize EEG data from an LSL stream.
                -w --window     Window length to display in seconds.
                -s --scale      Scale in uV.
                -r --refresh    Refresh rate in seconds.
                -f --figure     Window size.
                -v --version    Viewer version (1 or 2) - 1 is the default stable version, 2 is in development (and takes no arguments).
                -b --backend    Matplotlib backend to use. Default: TkAgg
    record   Recording an experiment.
                -d --directory      Root-directory to store recorded data in.
                -n --participants   The number of participants in this run.
                -i --trial-id       The id of this trial. Data is stored in a subdirectory with this name.
                                    If no id is provided, the current timestamp is used instead.
    
    replay   Replay data from a recorded CSV file into a new LSL stream.
                -f --filename   Name of the recording file.
        ''')

    parser.add_argument('command', help='Command to run.')

    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = parser.parse_args(sys.argv[1:2])

    if not hasattr(CLI, args.command):
        print('Incorrect usage. See help below.')
        parser.print_help()
        exit(1)

    cli = CLI(args.command)


if __name__ == '__main__':
    main()

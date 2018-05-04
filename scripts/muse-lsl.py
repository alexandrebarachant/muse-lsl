#!/usr/bin/python
import sys
import getopt
import argparse
import re
import os
import subprocess
import configparser

class Program:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='muse-lsl can be used to stream and visualize EEG data from the Muse 2016 headset.',
            usage='''muse-lsl <command> [<args>]
    These are the commands:
    stream    Start an LSL stream from Muse headset.
    view      Start viewing EEG data from LSL stream.
    record    Record data from Muse.
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

    def stream(self):
        parser = argparse.ArgumentParser(description='Start an LSL stream from Muse headset.')
        run('../muse-lsl.py', ' '.join(sys.argv[2:]))

    def view(self):
        parser = argparse.ArgumentParser(description='Start viewing EEG data from LSL stream.')
        run('../lsl-viewer.py', ' '.join(sys.argv[2:]))

    def record(self):
        parser = argparse.ArgumentParser(description='Record data from Muse.')
        run('../lsl-record.py', ' '.join(sys.argv[2:]))

def run(scriptPath, args):
    cmd = 'python ' + scriptPath + ' ' + args
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate() 
    result = out.split('\n')
    for lin in result:
        if not lin.startswith('#'):
            print(lin)

if __name__ == '__main__':
    Program()

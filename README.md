# Muse LSL

This is a collection of python script to use the muse 2016 BLE headset with LSL.

![Blinks](blinks.png)

## Requirements

The code rely on [pygatt](https://github.com/peplin/pygatt) for the BLE communication.
pygatt works on linux and OSX, and should work on window provided that you have a BLED112 dongle.

You will also need to find the mac address of you Muse headset

## Usage

to stream data with lsl

`python muse-lsl.py --address YOUR_DEVICE_ADDRESS`

Once the stream is up and running, you can visualize stream with

`python lsl-viewer.py`

## Run the P300 experiment

First, you have to run the muse lsl script as above.

In another terminal, run

`python generate_Visual_P300.py -d 120 & python lsl-record.py -d 120`

this will launch the P300 paradigm and record data for 2 minutes.

The task is to count the amount of time you see an stimulus with horizontal stripes.

For the data analysis, check [this notebook](notebooks/P300 with Muse.ipynb)

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

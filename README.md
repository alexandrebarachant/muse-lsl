# Muse LSL

This is a collection of python script to use the muse 2016 BLE headset with LSL.

![Blinks](blinks.png)

## Requirements

The code rely on [pygatt](https://github.com/peplin/pygatt) for the BLE communication.
pygatt works on linux and should work on window and OSX provided that you have a BLED112 dongle.
You have to use the development version of pygatt, that can be installed with pip using :

`pip install git+https://github.com/peplin/pygatt`

You will also need to find the mac address of you Muse headset. **This code is
only compatible with the 2016 version of the muse headset**

Finally, the code is for streaming and recording data is compatible with python
2.7 and python 3.x. However, the code for generating P300 stimulus rely on
psychopy and is only working with python 2.7. 

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

The task is to count the number of cat images that you see. You can add new jpg images inside the [stim](stim/) directory: use the `target-` prefix for cat images, and `nontarget-` for dog images.

For the data analysis, check [this notebook](https://github.com/alexandrebarachant/muse-lsl/blob/master/notebooks/P300%20with%20Muse.ipynb)

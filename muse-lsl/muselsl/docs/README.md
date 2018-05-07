# Muse LSL

This is a Python package for streaming and visualizing EEG data from the Muse 2016 headset.

![Blinks](blinks.png)

## Requirements

The code relies on [pygatt](https://github.com/peplin/pygatt) for the BLE communication. pygatt works on Linux and should work on Windows and macOS provided that you have a BLED112 Bluetooth dongle.

*Note: Another option for connecting to a Muse on Windows is via [BlueMuse](https://github.com/kowalej/BlueMuse/tree/master/Dist) which will output the same LSL stream format as muse-lsl.

You will need to find the MAC address or name of your Muse headset. 

**This code is only compatible with the 2016 version of the Muse headset.**

## Usage

*Everything can be run using muse-lsl.py or you may integrate into other packages.

To stream data with LSL:

`python muse-lsl.py stream`

The script will auto detect and connect to the first Muse device. In case you want
a specific device or if the detection fails, find the name of the device and pass it to the script:

`python muse-lsl.py stream --name YOUR_DEVICE_NAME`

You can also directly pass the MAC address (this option is also faster at startup):

`python muse-lsl.py stream --address YOUR_DEVICE_ADDRESS`

Once the stream is up and running, from another prompt, you can visualize it with:

`python muse-lsl.py lslview`

## Common issues

1. `pygatt.exceptions.BLEError: Unexpected error when scanning: Set scan parameters failed: Operation not permitted` (Linux)
 - This is an issue with pygatt requiring root privileges to run a scan. Make sure you have `libcap` installed and run ```sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool` ```


2. `pygatt.exceptions.BLEError: No characteristic found matching 273e0003-4c4d-454d-96be-f03bac821358` (Linux)
 - There is a problem with the most recent version of pygatt. Work around this by downgrading to 3.1.1: `pip install pygatt==3.1.1`

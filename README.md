# Muse LSL

This is a Python package for streaming and visualizing EEG data from the Muse 2016 headset.

![Blinks](blinks.png)

## Requirements

The code relies on [pygatt](https://github.com/peplin/pygatt) for the BLE communication. pygatt works on Linux and should work on Windows and macOS provided that you have a BLED112 Bluetooth dongle.

*Note: Another option for connecting to a Muse on Windows is via [BlueMuse](https://github.com/kowalej/BlueMuse/tree/master/Dist) which will output the same LSL stream format as muselsl.*

You will need to find the MAC address or name of your Muse headset. 

Compatible with Python 2.7 and Python 3.x.
 
**This code is only compatible with the 2016 version of the Muse headset.**

## Usage

Install with pip

`pip install muselsl`

*Everything can be run directly from the command line*

To print a list of available muses:

`muselsl list`

To stream data with LSL:

`muselsl stream`

The script will auto detect and connect to the first Muse device. In case you want
a specific device or if the detection fails, find the name of the device and pass it to the script:

`muselsl stream --name YOUR_DEVICE_NAME`

You can also directly pass the MAC address (this option is also faster at startup):

`muselsl stream --address YOUR_DEVICE_ADDRESS`

Once a stream is up and running, you now have access to the following commands in another prompt:

To view data 

`muselsl view`

To record data into a CSV file

`muselsl record`

Alternatively, you can record data directly without using LSL with the following command:

`muselsl record_direct`

### Backends
You can choose between gatt, bgapi, and bluemuse backends.

* gatt - used on unix systems, interfaces with native Bluetooth stack.
* bgapi - used with BLED112 dongle.
* bluemuse - used on Windows 10, native Bluetooth stack, requires [BlueMuse](https://github.com/kowalej/BlueMuse/tree/master/Dist) installation. 

### Integration into other packages
If you want to integrate Muse LSL into your own Python project, you can import and use its functions as you would any Python package. Examples are available in the `examples` folder.

ex:
```Python
from muselsl import stream

muses = stream.list_muses()
stream.stream(muses[0]['address'])

# Note: Streaming is synchronous, so code here will not execute until after the stream has been closed
print('Stream has ended')
```

## Common issues

1. `pygatt.exceptions.BLEError: Unexpected error when scanning: Set scan parameters failed: Operation not permitted` (Linux)
 - This is an issue with pygatt requiring root privileges to run a scan. Make sure you have `libcap` installed and run ```sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool` ```


2. `pygatt.exceptions.BLEError: No characteristic found matching 273e0003-4c4d-454d-96be-f03bac821358` (Linux)
 - There is a problem with the most recent version of pygatt. Work around this by downgrading to 3.1.1: `pip install pygatt==3.1.1`
 
 
3. Connection issues with BLED112 dongle (Windows):
 - You may need to use the --interface argument to provide the appropriate COM port value for the BLED112 device. The default value is COM9. To setup or view the device's COM port go to:
 `Control Panel\Hardware and Sound\Devices and Printers > Right Click > Bluetooth settings > COM Ports > (Add > Incoming)`
 

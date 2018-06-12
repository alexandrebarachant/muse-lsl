# Muse LSL

A Python package for streaming, visualizing, and recording EEG data from the Muse 2016 headband.

![Blinks](blinks.png)

## Requirements

The code relies on [pygatt](https://github.com/peplin/pygatt) or [BlueMuse](https://github.com/kowalej/BlueMuse/tree/master/Dist) for BLE communication and works differently on differnt operating systems.

- Windows: On Windows 10, we recommend installing [BlueMuse](https://github.com/kowalej/BlueMuse/tree/master/Dist) and specifying it as the  backend when using Muse LSL (i.e. `$ muselsl stream -b bluemuse`). Alternatively, if you have a BLED112 dongle you can try the bgapi backend (default option in CLI).
- Mac: __BLED112 dongle required__. Use the bgapi backend (default option)
- Linux: No dongle or separate install required. Use the pygatt backend (default option on Linux)


Compatible with Python 2.7 and Python 3.x.
 
**This code is only compatible with the 2016 version of the Muse headset.**

## Getting Started

### Installation

Install Muse LSL with pip

`pip install muselsl`

### Setting Up a Stream

The easiest way to get Muse data is to use Muse LSL directly from the command line. Use the `-h` flag to get a comprehensive list of all commands and options.

*Note: if you run into any issues, first check out out [Common Issues](#common-issues) and then the [Issues](https://github.com/alexandrebarachant/muse-lsl/issues) section of this repository*

To print a list of available muses:

    $ muselsl list

To stream data with LSL:

    $ muselsl stream  

The script will auto detect and connect to the first Muse device. In case you want
a specific device or if the detection fails, find the name of the device and pass it to the script:

    $ muselsl stream --name YOUR_DEVICE_NAME

You can also directly pass the MAC address (this option is also faster at startup):

    $ muselsl stream --address YOUR_DEVICE_ADDRESS


### Working with Streaming Data
Once a stream is up and running, you now have access to the following commands in another prompt:

To view data:

    $ muselsl view    

To record EEG data into a CSV:

    $ muselsl record  

*Note: this command will also save data from any LSL stream containing 'Markers' data, such as from the stimulus presentation scripts in [EEG Notebooks](https://github.com/neurotechx/eeg-notebooks)*

Alternatively, you can record data directly without using LSL through the following command:

    $ muselsl record_direct

*Note: direct recording does not allow 'Markers' data to be recorded*

## Running Experiments

Muse LSL was designed so that the Muse could be used to run a number of classic EEG experiments, including the [P300 event-related potential](http://alexandre.barachant.org/blog/2017/02/05/P300-with-muse.html) and the SSVEP and SSAEP evoked potentials.

The code to perform these experiments is still available, but is now maintained in the [EEG Notebooks](https://github.com/neurotechx/eeg-notebooks) repository by the [NeuroTechX](https://neurotechx.com) community

## Integration into other packages
If you want to integrate Muse LSL into your own Python project, you can import and use its functions as you would any Python package. Examples are available in the `examples` folder:

```Python
from muselsl import stream

muses = stream.list_muses()
stream.stream(muses[0]['address'])

# Note: Streaming is synchronous, so code here will not execute until after the stream has been closed
print('Stream has ended')
```

## Common Issues

1. `pygatt.exceptions.BLEError: Unexpected error when scanning: Set scan parameters failed: Operation not permitted` (Linux)
 - This is an issue with pygatt requiring root privileges to run a scan. Make sure you have `libcap` installed and run ```sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool` ```


2. `pygatt.exceptions.BLEError: No characteristic found matching 273e0003-4c4d-454d-96be-f03bac821358` (Linux)
 - There is a problem with the most recent version of pygatt. Work around this by downgrading to 3.1.1: `pip install pygatt==3.1.1`
 
 
3. Connection issues with BLED112 dongle (Windows):
 - You may need to use the --interface argument to provide the appropriate COM port value for the BLED112 device. The default value is COM9. To setup or view the device's COM port go to:
 `Control Panel\Hardware and Sound\Devices and Printers > Right Click > Bluetooth settings > COM Ports > (Add > Incoming)`

4. `pygatt.exceptions.BLEError: No BLE adapter found`
- Make sure your computer's Bluetooth is turned on.

5. `pygatt.exceptions.BLEError: Unexpected error when scanning: Set scan parameters failed: Connection timed out`
- This seems to be due to a OS-level Bluetooth crash. Try turning your computer's bluetooth off and on again

 

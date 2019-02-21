# Muse LSL

A Python package for streaming, visualizing, and recording EEG data from the Muse 2016 headband.

![Blinks](blinks.png)

## Requirements

The code relies on [pygatt](https://github.com/peplin/pygatt) or [BlueMuse](https://github.com/kowalej/BlueMuse/tree/master/Dist) for BLE communication and works differently on different operating systems.

- Windows: On Windows 10, we recommend installing [BlueMuse](https://github.com/kowalej/BlueMuse/tree/master/Dist) and using its GUI to find and start streaming from Muses. Alternatively, if you have a BLED112 dongle you can try Muse LSL's bgapi backend (i.e. `$ muselsl stream -b bgapi`).
- Mac: **BLED112 dongle required**. Use the bgapi backend (default option on Mac)
- Linux: No dongle or separate install required. Use the pygatt backend (default option on Linux) and make sure to read the [Common Issues](#linux) 

**Compatible with Python 2.7 and Python 3.x**

**Only compatible with the 2016 model of the Muse headband**

_Note: if you run into any issues, first check out out [Common Issues](#common-issues) and then the [Issues](https://github.com/alexandrebarachant/muse-lsl/issues) section of this repository_

## Getting Started

### Installation

Install Muse LSL with pip

`pip install muselsl`

### Setting Up a Stream

On Windows 10, we recommend using the [BlueMuse](https://github.com/kowalej/BlueMuse/tree/master/Dist) GUI to set up an LSL stream. On Mac and Linux, the easiest way to get Muse data is to use Muse LSL directly from the command line. Use the `-h` flag to get a comprehensive list of all commands and options.

To print a list of available muses:

    $ muselsl list

To begin an LSL stream from the first available Muse:

    $ muselsl stream  

In order to connect to a specific Muse, pass the name of the device as an argument. The name of the Muse can be found on the inside of the left earpiece (e.g. Muse-41D2)

    $ muselsl stream --name YOUR_DEVICE_NAME

You can also directly pass the MAC address of your Muse (this is the fastest and most reliable way):

    $ muselsl stream --address YOUR_DEVICE_ADDRESS

### Working with Streaming Data

Once a stream is up and running, you now have access to the following commands in another prompt:

To view data:

    $ muselsl view

If the visualization freezes or is laggy, you can also try the alternate version 2 of the viewer. *Note: this will require the additional [vispy](https://github.com/vispy/vispy) and [mne](https://github.com/mne-tools/mne-python) dependencies*

    $ muselsl view --version 2

To record EEG data into a CSV:

    $ muselsl record --duration 60  

_Note: this command will also save data from any LSL stream containing 'Markers' data, such as from the stimulus presentation scripts in [EEG Notebooks](https://github.com/neurotechx/eeg-notebooks)_

Alternatively, you can record data directly without using LSL through the following command:

    $ muselsl record_direct --duration 60

_Note: direct recording does not allow 'Markers' data to be recorded_

## Running Experiments

Muse LSL was designed so that the Muse could be used to run a number of classic EEG experiments, including the [P300 event-related potential](http://alexandre.barachant.org/blog/2017/02/05/P300-with-muse.html) and the SSVEP and SSAEP evoked potentials.

The code to perform these experiments is still available, but is now maintained in the [EEG Notebooks](https://github.com/neurotechx/eeg-notebooks) repository by the [NeuroTechX](https://neurotechx.com) community.

## Integration into other projects

If you want to integrate Muse LSL into your own Python project, you can import and use its functions as you would any Python package. Examples are available in the `examples` folder:

```Python
from muselsl import stream

muses = stream.list_muses()
stream.stream(muses[0]['address'])

# Note: Streaming is synchronous, so code here will not execute until after the stream has been closed
print('Stream has ended')
```

## What is LSL?

Lab Streaming Layer or LSL is a system designed to unify the collection of time series data for research experiments. It has become standard in the field of EEG-based brain-computer interfaces for its ability to make seperate streams of data available on a network with time synchronization and near real-time access. For more information, check out this [lecture from Modern Brain-Computer Interface Design](https://www.youtube.com/watch?v=Y1at7yrcFW0) or the [LSL repository](https://github.com/sccn/labstreaminglayer)

## Common Issues

### Mac and Windows

1.  Connection issues with BLED112 dongle:

- You may need to use the `--interface` argument to provide the appropriate COM port value for the BLED112 device. The default value is COM9. To setup or view the device's COM port go to your OS's system settings

### Linux

1.  `pygatt.exceptions.BLEError: Unexpected error when scanning: Set scan parameters failed: Operation not permitted` (Linux)

- This is an issue with pygatt requiring root privileges to run a scan. Make sure you [have `libcap` installed](https://askubuntu.com/questions/347788/how-can-i-install-libpcap-header-files-on-ubuntu-12-04) and run `` sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool` ``

2.  `pygatt.exceptions.BLEError: No characteristic found matching 273e0003-4c4d-454d-96be-f03bac821358` (Linux)

- There is a problem with the most recent version of pygatt. Work around this by downgrading to 3.1.1: `pip install pygatt==3.1.1`

3.  `pygatt.exceptions.BLEError: No BLE adapter found` (Linux)

- Make sure your computer's Bluetooth is turned on.

4.  `pygatt.exceptions.BLEError: Unexpected error when scanning: Set scan parameters failed: Connection timed out` (Linux)

- This seems to be due to a OS-level Bluetooth crash. Try turning your computer's bluetooth off and on again

5.  `'RuntimeError: could not create stream outlet'` (Linux)

- This appears to be due to Linux-specific issues with the newest version of pylsl. Ensure that you have pylsl 10.1.5 installed in the environment in which you are trying to run Muse LSL

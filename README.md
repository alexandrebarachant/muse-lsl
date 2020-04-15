


# Muse LSL - Experiment

This repo is forked from [https://github.com/alexandrebarachant/muse-lsl](https://github.com/alexandrebarachant/muse-lsl) [1].

The original code was modified and extended to allow streaming and recording of two or more muses simultaneously.

## Installation

Install this repository as a pip package with

    pip3 install .
    
or just install the dependencies using:

    pip3 install -r requirements.txt

If you *did not* install the repo as a pip package, you need to replace `muselsl` with
`python3 -m muselsl` in all following examples.

## Hardware Setup

We tested different hardware setups for multiple streams.
The most reliable setup, which allowed streaming of all data-streams from two muses was the following:

- Two Muses
- Two Laptops (We used a MacBook with `BLED112 dongle` and a linux machine with integrated Bluetooth.)
- Wireless (or wired) network with peer to peer traffic allowed (HPI network might not work, we made a WIFI hotspot using an android phone)

One of the laptops acts as a *stream source*, while the other *records* its own stream and the stream from the stream source, which is sent over
the network.

## Stream Source

The stream source is started before the recorder and must run until after the recorder has stopped.
If the stream source crashes it should be restarted, the recorder can recover only if the stream source is restarted, otherwise the recorder will
crash, when attempting to stop the recording.

The stream source is started with the following command:

     muselsl stream -pcg -a <MAC-ADRESS-OF-MUSE>

Where `<MAC-ADRESS-OF-MUSE>` must be replaced with the mac-address of one of the muses.
To find the mac addresses of your muses, you can turn on your muses and run

    muselsl list

to get a list of the available headsets.
The last four letters (two bytes) of the MAC address are printed on each Muse headset.

In our setup one stream source is started on the *stream source* machine and one is started
for the other muse, on the *recording* machine.


## View

Before starting the recording, make sure all streams are coming through, and are of decent quality.
This can be done using the viewer.

    muselsl view -v 2 -a <MAC-ADRESS-OF-MUSE> -t <DATA-TYPE>
    
Where data-type can be any of:
- PPG
- EEG
- ACC
- GYRO

You can zoom in and out by holding your left mouse button and moving your mouse up or down.

> It is also a good idea, to at least monitor the EEG streams of all participant during the
> experiment, to be able to detect artifacts early and fix them (eg. loose electrodes, muscle noise, etc.).

## Recorder

When the stream source is running, the recorder script can be started with the following command:

    muselsl record -d <data-path> -n <number-of-participants> [-i <trial-id>]

The script will ask for the `MUSE-ID` of each participant, which is written on each muse device.
The `MUSE-ID` are the last two bytes (four letters) of the mac address.

After all IDs are set, the recording starts automatically.
During the recording, timestamps can be saved, by typing any text as a label and pressing enter.
These timestamps can be used to mark when different parts of the experiment begin, or when the experiment has ended.

The recording will continue, until it is stopped by pressing `CTRL` `+` `C`.

All recordings are saved in the specified directory.
If no `trial-id` is provided, the current timestamp is used instead to create a new subdirectory,
in which all data is stored.
This directory contains the recorded markers, which are stored in `markers.csv` and a subdirectory for each participant.

Each participant directory contains the following files:


| File | Description |
|------|-------------|
|ACC.csv | Data from the Accelerometer |
|EEG.csv| EEG Data|
|GYRO.csv | Gyroscope Data |
|PPG.csv | Heart rate measured with PPG |

## other Setups

We tried using Raspberry Pi's as stream source, however 
even the newest model 4 with a `BLED112 dongle`
was not able to stream reliable for more than 10 minutes.
It might be possible, though to use Raspberry Pi's, if not all data
streams are enabled (eg. if only recording ppg).
See [this github issue](https://github.com/alexandrebarachant/muse-lsl/issues/55) for more information.


[1]
> Alexandre Barachant, Dano Morrison, Hubert Banville, Jason Kowaleski, Uri Shaked, Sylvain Chevallier, & Juan Jesús Torre Tresols. (2019, May 25). muse-lsl (Version v2.0.2). Zenodo. http://doi.org/10.5281/zenodo.3228861
[![DOI](https://zenodo.org/badge/80209610.svg)](https://zenodo.org/badge/latestdoi/80209610) 



# Muse LSL - Experiment

This repo is forked from [https://github.com/alexandrebarachant/muse-lsl](https://github.com/alexandrebarachant/muse-lsl) [1].

The original code was modified and extended to allow streaming and recording of two or more muses, simultaniously.

## Hardware Setup

We tested different hardware setups for multiple streams.
The most reliable setup, which allowed streaming of all datastreams from two muses was the following:

- Two Muses
- Two Laptops (We used a Macbook with `BLED112 dongle` and a linux machine with integraded bluetooth.)
- Wireless (or wired) Network with peer to peer trafic allowed (HPI network might not work, we made a hotspot using an anrdoid phone)

One of the laptops acts as a *stream source*, while the other *records* its own stream and the stream from the stream source, which is sent over
the network.

### Stream Source

The stream source is started before the recorder and must run until after the recorder has stopped.
If the stream source crashes it should be restarted, the recorder can recover only if the stream source is restarted, otherwise the recorder will
crash, when attempting to stop the recording.

The stream source is started with the following command:

     muselsl stream -pcg -a <MAC-ADRESS-OF-MUSE>

Where `<MAC-ADRESS-OF-MUSE>` must be replaced with the mac-address of one of the muses.

### Recorder

When the stream source is running, the recorder script can be started with the following command:

    python3 -m muselsl.run_experiment

It should be run from the root directory of this repository.
The script will ask for the `MUSE-ID` of each participant, which is written on each muse device.
The `MUSE-ID` are the last two bytes (four letters) of the mac address.

After all ids are set, the recording starts automatically.
During the recording, timestamps can be saved, by typing any text as a label and pressing enter.
These timestamps can be used to mark when different parts of the experiment begin, or when the experiment has ended.

The recording will continue, until it is stopped by pressing `CTRL` `+` `C`.

All recordings are saved in the directory `recordings`.
Every time when running the `run_experiment` script a new subdirectory with the current timestamp is created.
This direcrory contains the recorded markers, which are stored in `markers.csv` and a subdirectory for each participant.

Each participant directory contains the following files:


| File | Description |
|------|-------------|
|ACC.csv | Data from the Accelerometer |
| EEG.csv| EEG Data|
|GYRO.csv | Gyroscop Data |
|PPG.csv | Hear rate measured with PPG |

## other Setups

We tried using rapsberry pis as stream source, however 
even the newest modell 4 with a `BLED112 dongle`
was not able to stream reliale for more than 10 minutes.
It might be possible, though to use raspberry pis if not all data
streams are enabled (eg. if only recording ppg).


[1]
> Alexandre Barachant, Dano Morrison, Hubert Banville, Jason Kowaleski, Uri Shaked, Sylvain Chevallier, & Juan Jesús Torre Tresols. (2019, May 25). muse-lsl (Version v2.0.2). Zenodo. http://doi.org/10.5281/zenodo.3228861
[![DOI](https://zenodo.org/badge/80209610.svg)](https://zenodo.org/badge/latestdoi/80209610) 
#!/bin/bash

MAC=$1
PORT=$2
muse-io --device ${MAC} --osc osc.udp://localhost:${PORT}
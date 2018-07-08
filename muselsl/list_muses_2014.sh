#!/bin/bash

muses=$(hcitool scan | grep Muse | while read -r line ; do
    MAC="$(echo $line | grep -o '[[:xdigit:]:]\{11,17\}')"
    NAME="$(echo $line | grep -o '\<[Muse].*\>')"
    muse-io --device $MAC --osc osc.udp://localhost:5000 | {
        while IFS= read -r line
        do
	    if [[ $line =~ "Connection failure" ]]
	    then
		    exit 1
	    fi
	    if [[ $line =~ "Connected." ]]
	    then
		    exit 0
	    fi
        done
    }
    if [[ $? == 0 ]]
    then
	    echo "{\"name\":\"$NAME\",\"address\":\"$MAC\"}"
    fi
done
)
echo ${muses[@]}


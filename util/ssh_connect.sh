#!/bin/bash
# ssh_connect.sh - script to connect to a PI given its label (A,B,C)
# by finding its IP address. Labels are not case sensitive.

declare -A mac
mac["A"]="b8:27:eb:28:65:ca"
mac["B"]="b8:27:eb:7b:d9:70"
mac["C"]="b8:27:eb:ef:9b:60"

pi=${1^^}
addr=${mac[$pi]}

echo Connecting to Pi Zero $pi at MAC address $addr
ssh pi@$(sudo arp-scan --local | grep $addr | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")

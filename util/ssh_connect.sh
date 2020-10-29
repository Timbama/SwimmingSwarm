ssh pi@$(sudo arp-scan --local | grep $1 | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")

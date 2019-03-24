ssh pi@$(sudo arp-scan --local | grep b8:27:eb:fd:1d:17 | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")

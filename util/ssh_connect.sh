ssh pi@$(sudo arp-scan --local | grep b8:27:eb:20:36:a0 | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")

ssh pi@$(sudo arp-scan --local | grep b8:27:eb:b9:7f:3a | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")

ssh pi@$(sudo arp-scan --local | grep b8:27:eb:ef:9b:60 | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")

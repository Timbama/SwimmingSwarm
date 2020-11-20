<<<<<<< HEAD
ssh pi@$(sudo arp-scan --local | grep $1 | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")
=======
ssh pi@$(sudo arp-scan --local | grep b8:27:eb:ef:9b:60 | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")
>>>>>>> dca026148281862bb0672ac0285d20a6fb50a5a8

sudo mount -t cifs //192.168.178.100/movies /mnt/movies \
  -o username=edsharood,password=As-12345699

sudo mount -t cifs //192.168.178.100/complete /mnt/complete \
  -o username=edsharood,password=As-12345699

sudo hostnamectl set-hostname homeserver
sudo sed -i 's/raspberrypi/homeserver/g' /etc/hosts
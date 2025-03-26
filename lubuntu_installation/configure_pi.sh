sudo mount -t cifs //192.168.178.100/movies /mnt/movies \
  -o username=edsharood,password=As-12345699

sudo mount -t cifs //192.168.178.100/complete /mnt/complete \
  -o username=edsharood,password=As-12345699

sudo mount -t cifs //192.168.178.100/incomplete /mnt/incomplete \
  -o username=edsharood,password=As-12345699

sudo mount -t cifs //192.168.178.100/raspberry-drive /mnt/raspberry-drive \
  -o username=edsharood,password=As-12345699  


sudo hostnamectl set-hostname homeserver
sudo sed -i 's/raspberrypi/homeserver/g' /etc/hosts
export N8N_SECURE_COOKIE=false
export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true


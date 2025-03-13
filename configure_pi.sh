echo "As-12345699" | sudo sshfs -o password_stdin,idmap=user,allow_other,default_permissions 
edsharood@192.168.178.100:"D:/sandbox/movies" /mnt/movies
echo "As-12345699" | sudo sshfs -o password_stdin,idmap=user,allow_other,default_permissions 
edsharood@192.168.178.100:"D:\docker-folder\complete" /mnt/complete
sudo hostnamectl set-hostname homeserver
sudo sed -i 's/raspberrypi/homeserver/g' /etc/hosts
git config --global user.name "ed"
git config --global user.email "ed.s.sharood@gmail.com"
sudo apt update && sudo apt upgrade -y
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g n8n
sudo apt install qbittorrent-nox -y

sudo apt-get install sshfs
sudo apt-get install sshpass
sudo apt install vlc -y
#sudo apt install mpv -y
#sudo apt install celluloid -y
sudo apt install kodi -y



chmod +x configure_pi.sh
chmod +x run_firefox_docker
chmod +x stop_firefox_docker
sudo mkdir /mnt/movies
sudo mkdir /mnt/complete
sudo mkdir /mnt/incomplete
sudo mkdir /mnt/raspberry-drive


sudo apt install qbittorrent-nox -y


cat <<EOF | sudo tee /etc/systemd/system/n8n.service
[Unit]
Description=n8n workflow automation tool
After=network.target

[Service]
ExecStart=/usr/bin/n8n
Restart=always
User=pi
Environment=PATH=/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=NODE_ENV=production
Environment=N8N_SECURE_COOKIE=false
Environment=N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
Environment=N8N_RUNNERS_ENABLED=true
WorkingDirectory=/home/pi

[Install]
WantedBy=multi-user.target
EOF'

sudo bash -c 'cat > /etc/systemd/system/qbittorrent-nox.service <<EOF
[Unit]
Description=qBittorrent-nox (Headless Torrent Client)
After=network.target

[Service]
User=pi
Group=pi
ExecStart=/usr/bin/qbittorrent-nox --webui-port=8080
Restart=on-failure
LimitNOFILE=65536
ExecStop=/usr/bin/pkill -f qbittorrent-nox

[Install]
WantedBy=multi-user.target
EOF'




sudo systemctl daemon-reload
sudo systemctl enable qbittorrent-nox
sudo systemctl start qbittorrent-nox

sudo systemctl enable n8n
sudo systemctl start n8n

sudo systemctl restart qbittorrent-nox


# Install Docker
sudo apt install -y docker.io

# Start Docker and enable at boot
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to the Docker group to avoid using sudo
sudo usermod -aG docker $USER

# Log out and log back in for group changes to take effect
# (Or run the command below to apply changes to current session)
newgrp docker

docker pull lscr.io/linuxserver/firefox
mkdir -p ~/firefox-config

docker run -d \
  --name=firefox \
  --security-opt seccomp=unconfined \
  -p 3011:3000 \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/London \
  -v ~/firefox-config:/config \
  --shm-size=256m \
  lscr.io/linuxserver/firefox

node -v
npm -v
n8n -v
docker --version


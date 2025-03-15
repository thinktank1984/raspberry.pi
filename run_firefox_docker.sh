docker run -d \
  --name=firefox \
  --security-opt seccomp=unconfined \
  -p 3000:3000 \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/London \
  -v ~/firefox-config:/config \
  --shm-size=256m \
  --restart unless-stopped \
  lscr.io/linuxserver/firefox
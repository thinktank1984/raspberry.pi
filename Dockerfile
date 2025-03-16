FROM lscr.io/linuxserver/qbittorrent

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install cifs-utils using apk (Alpine's package manager)
RUN apk update && apk add --no-cache cifs-utils

# Create the entrypoint script inside the container using cat
RUN apk update && apk add --no-cache qbittorrent-nox sshfs sshpass
#RUN WINDOWS_USER="edsharood" 
#RUN WINDOWS_HOST="192.168.178.100" 
#RUN MOVIES_PATH="D:/sandbox/movies" 
#RUN COMPLETE_PATH="D:/docker-folder/complete" 
#RUN MOUNT_MOVIES="/mnt/movies" 
#RUN MOUNT_COMPLETE="/mnt/complete" 
RUN mkdir -p $MOUNT_MOVIES $MOUNT_COMPLETE 
RUN mount -t cifs //192.168.178.100/movies /mnt/movies \
-o username=edsharood,password=As-12345699
RUN mount -t cifs //192.168.178.100/complete /mnt/complete \
-o username=edsharood,password=As-12345699
RUN mount -t cifs //192.168.178.100/incomplete /mnt/incomplete \
-o username=edsharood,password=As-12345699
RUN mount -t cifs //192.168.178.100/raspberry-drive /mnt/raspberry-drive \
-o username=edsharood,password=As-12345699  
RUN qbittorrent-nox --confirm-legal-notice
RUN exec tail -f /dev/null

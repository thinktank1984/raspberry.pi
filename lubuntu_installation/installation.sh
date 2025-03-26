#!/bin/bash

# Update package lists
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y curl wget apt-transport-https ca-certificates gnupg lsb-release

# --- Install Ngrok ---
echo "Installing Ngrok..."
wget -qO ngrok.zip https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.zip
unzip ngrok.zip
sudo mv ngrok /usr/local/bin/
rm ngrok.zip
echo "Ngrok installed successfully!"

# --- Install Docker ---
echo "Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER  # Allow running Docker without sudo
echo "Docker installed successfully! Please log out and log back in to apply group changes."

# --- Install VLC ---
echo "Installing VLC..."
sudo apt install -y vlc
echo "VLC installed successfully!"

# --- Install Kodi ---
echo "Installing Kodi..."
sudo apt install -y kodi
echo "Kodi installed successfully!"

echo "Installation completed!"
#!/bin/bash

# Update package lists
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y curl wget apt-transport-https ca-certificates gnupg lsb-release

# --- Install Ngrok ---
echo "Installing Ngrok..."
wget -qO ngrok.zip https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.zip
unzip ngrok.zip
sudo mv ngrok /usr/local/bin/
rm ngrok.zip
echo "Ngrok installed successfully!"

# --- Install Docker ---
echo "Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER  # Allow running Docker without sudo
echo "Docker installed successfully! Please log out and log back in to apply group changes."

echo "Installation completed!"

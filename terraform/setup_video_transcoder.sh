#!/bin/bash
# /usr/local/bin/setup_video_transcoder.sh
# Usage: sudo /usr/local/bin/setup_video_transcoder.sh
set -euo pipefail
LOGFILE="/var/log/video_transcoder_setup.log"
exec > >(tee -a "$LOGFILE") 2>&1

REPO_SSH="git@github.com:srimanjary123/video-transcoder-assesment-2.git"
REPO_HTTPS="https://github.com/srimanjary123/video-transcoder-assesment-2.git"
TARGET_DIR="/home/ubuntu/video-transcoder-assesment-2"
VENV_DIR="$TARGET_DIR/.venv"
WRAPPER="/usr/local/bin/video-transcoder"
USER="ubuntu"

echo "Starting Video Transcoder setup - $(date)"
echo "Target dir: $TARGET_DIR"
echo

# 1) Ensure apt update + basic packages
echo "Updating apt and installing base packages..."
apt-get update -y
apt-get install -y git python3-venv python3-pip unzip ffmpeg

# 2) Ensure docker (simple install if missing)
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Installing docker.io..."
  apt-get install -y docker.io
  systemctl enable --now docker
else
  echo "Docker already installed - skipping docker install."
fi

# 3) Ensure we can run docker as ubuntu user
if ! id -nG "$USER" | grep -qw docker; then
  echo "Adding $USER to docker group..."
  usermod -aG docker "$USER" || true
fi

# 4) Prepare target directory (clone repo)
if [ -d "$TARGET_DIR" ]; then
  echo "Removing existing $TARGET_DIR"
  rm -rf "$TARGET_DIR"
fi

# Try SSH clone first (fast if keys are set), fallback to HTTPS
echo "Cloning repository..."
if sudo -u "$SUDO_USER" -n true 2>/dev/null; then
  # If run under sudo, attempt to run git as the original user
  if sudo -u "$USER" git clone "$REPO_SSH" "$TARGET_DIR" 2>/dev/null; then
    echo "Cloned repo via SSH."
  else
    echo "SSH clone failed — falling back to HTTPS clone."
    sudo -u "$USER" git clone "$REPO_HTTPS" "$TARGET_DIR"
  fi
else
  # running directly as root or non-sudo context
  if git clone "$REPO_SSH" "$TARGET_DIR" 2>/dev/null; then
    echo "Cloned repo via SSH."
  else
    echo "SSH clone failed — falling back to HTTPS clone."
    git clone "$REPO_HTTPS" "$TARGET_DIR"
  fi
fi

# 5) Create python venv, install pip packages
echo "Creating virtual environment and installing python dependencies..."
python3 -m venv "$VENV_DIR"
chown -R "$USER":"$USER" "$TARGET_DIR"
# Activate and pip install as ubuntu user to keep file ownership clean
sudo -u "$USER" bash -lc "source '$VENV_DIR/bin/activate' && pip install --upgrade pip wheel && pip install -r '$TARGET_DIR/requirements.txt'"

# 6) Install/additional packages you requested explicitly
echo "Installing boto3 and PyJWT[crypto]==2.8.0 and cryptography in venv..."
sudo -u "$USER" bash -lc "source '$VENV_DIR/bin/activate' && pip install boto3 'PyJWT[crypto]==2.8.0' cryptography"

# 7) Build docker image (run as ubuntu to ensure access to repo files)
echo "Building Docker image 'video-transcoder-assesment-2:latest'..."
sudo -u "$USER" bash -lc "cd '$TARGET_DIR' && docker build -t video-transcoder-assesment-2:latest ."

# 8) Create a simple wrapper executable to run the app with venv
echo "Creating wrapper executable at $WRAPPER ..."
cat > "$WRAPPER" <<'EOF'
#!/bin/bash
# wrapper to run the video-transcoder app inside its venv
TARGET_DIR="/home/ubuntu/video-transcoder-assesment-2"
VENV_DIR="$TARGET_DIR/.venv"

if [ ! -d "$TARGET_DIR" ]; then
  echo "ERROR: target directory $TARGET_DIR does not exist"
  exit 1
fi

if [ ! -f "$VENV_DIR/bin/activate" ]; then
  echo "ERROR: virtualenv not found in $VENV_DIR"
  exit 1
fi

cd "$TARGET_DIR"
# activate venv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# run app.py (same command you specified)
python app.py
EOF

chmod +x "$WRAPPER"
chown "$USER":"$USER" "$WRAPPER"

# 9) Make the cloned project and venv owned by ubuntu
chown -R "$USER":"$USER" "$TARGET_DIR"
chmod -R u+rwX "$TARGET_DIR"

echo
echo "Setup finished. Log file: $LOGFILE"
echo "To run the app as the 'ubuntu' user:"
echo "  sudo -i -u ubuntu $WRAPPER"
echo "Or switch to ubuntu and run:"
echo "  sudo su - ubuntu"
echo "  $WRAPPER"
echo
echo "Notes:"
echo "- If the SSH clone failed and you need SSH access to private repo, ensure /home/ubuntu/.ssh contains your private key and the public key is added to GitHub."
echo "- If you prefer to clone via SSH but still see permission issues, run the clone manually as 'ubuntu' after adding the key."
echo "- Docker group membership was added to '$USER'; the change takes effect after the next login (or re-login)."
echo
exit 0

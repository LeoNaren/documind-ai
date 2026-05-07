#!/bin/bash
# =============================================================================
# DocuMind AI — EC2 Setup Script
# Run this once on a fresh Ubuntu 24.04 EC2 instance
# Usage: bash setup.sh
# Or with custom values:
#   POSTGRES_PASSWORD='strong-pwd' GEMINI_API_KEY='xxx' bash setup.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()   { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

: "${POSTGRES_PASSWORD:=changeme}"
: "${GEMINI_API_KEY:=your_gemini_api_key_here}"
: "${DEEPGRAM_API_KEY:=your_deepgram_api_key_here}"
: "${FIREBASE_PROJECT_ID:=your_project_id}"
: "${FIREBASE_CLIENT_EMAIL:=your_client_email}"
: "${FIREBASE_PRIVATE_KEY:=your_private_key}"
: "${VITE_FIREBASE_API_KEY:=your_firebase_api_key}"
: "${VITE_FIREBASE_AUTH_DOMAIN:=your_project.firebaseapp.com}"
: "${VITE_FIREBASE_PROJECT_ID:=your_project_id}"

log "Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y

if command -v docker &>/dev/null; then
  warn "Docker already installed, skipping..."
else
  log "Installing Docker..."
  sudo apt-get install -y ca-certificates curl gnupg lsb-release

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

  sudo usermod -aG docker "$USER"
  log "Docker installed successfully."
fi

REPO_DIR="$HOME/documind-ai"

if [ -d "$REPO_DIR" ]; then
  warn "Repo already exists at $REPO_DIR. Pulling latest changes..."
  cd "$REPO_DIR" && git pull
else
  log "Cloning repository..."
  git clone https://github.com/LeoNaren/documind-ai.git "$REPO_DIR"
  cd "$REPO_DIR"
fi

log "Setting up environment variables..."

EC2_PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)
log "Detected EC2 public IP: $EC2_PUBLIC_IP"

if [ ! -f "$REPO_DIR/.env" ]; then
  cat > "$REPO_DIR/.env" <<EOF
# Database
POSTGRES_USER=documind
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=documind
DATABASE_URL=postgresql+psycopg2://documind:${POSTGRES_PASSWORD}@db:5432/documind

# Redis
REDIS_URL=redis://redis:6379

# AI
GEMINI_API_KEY=${GEMINI_API_KEY}
DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}

# Firebase (backend)
FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}
FIREBASE_CLIENT_EMAIL=${FIREBASE_CLIENT_EMAIL}
FIREBASE_PRIVATE_KEY=${FIREBASE_PRIVATE_KEY}
ALLOW_MOCK_AUTH=false

# Frontend
VITE_API_BASE_URL=http://${EC2_PUBLIC_IP}:8000/api
VITE_FIREBASE_API_KEY=${VITE_FIREBASE_API_KEY}
VITE_FIREBASE_AUTH_DOMAIN=${VITE_FIREBASE_AUTH_DOMAIN}
VITE_FIREBASE_PROJECT_ID=${VITE_FIREBASE_PROJECT_ID}
EOF
  warn "Created .env — update with your real API keys before starting the app."
else
  warn ".env already exists, skipping. Delete it to regenerate: rm -f .env"
fi

log "Configuring firewall rules..."
sudo apt-get install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 8000/tcp
sudo ufw allow 5173/tcp
sudo ufw --force enable
log "Firewall configured."

log "Building and starting Docker containers..."
cd "$REPO_DIR"

sudo docker compose up -d --build

log "Waiting for services to become healthy..."
sleep 10


log "Running health check..."

HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health || true)

if [ "$HEALTH" = "200" ]; then
  log "Backend is healthy!"
else
  warn "Backend health check returned HTTP $HEALTH — check logs with: docker compose logs backend"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  DocuMind AI deployed successfully! ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  Frontend : http://${EC2_PUBLIC_IP}:5173"
echo -e "  Backend  : http://${EC2_PUBLIC_IP}:8000"
echo -e "  API Docs : http://${EC2_PUBLIC_IP}:8000/docs"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Fill in your real API keys in .env, then restart:"
echo "     nano .env"
echo "     docker compose up -d --build"
echo ""
echo "  2. To pass keys directly when running the script:"
echo "     POSTGRES_PASSWORD='strong-pwd' \\"
echo "     GEMINI_API_KEY='xxx' \\"
echo "     DEEPGRAM_API_KEY='yyy' \\"
echo "     FIREBASE_PROJECT_ID='zzz' \\"
echo "     FIREBASE_CLIENT_EMAIL='aaa' \\"
echo "     FIREBASE_PRIVATE_KEY='bbb' \\"
echo "     VITE_FIREBASE_API_KEY='ccc' \\"
echo "     VITE_FIREBASE_AUTH_DOMAIN='ddd' \\"
echo "     VITE_FIREBASE_PROJECT_ID='eee' \\"
echo "     bash setup.sh"
echo ""
echo "  3. Make sure ports 5173 and 8000 are open in your EC2 Security Group"
echo ""
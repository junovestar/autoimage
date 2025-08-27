#!/bin/bash

# ========================================
# QUICK DEPLOY SCRIPT - CHO NGƯỜI DÙNG CÓ KINH NGHIỆM
# ========================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Quick Deploy Gemini AI Image Generator${NC}"

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <domain> <email> [deploy-type]"
    echo "  deploy-type: traditional (default) or docker"
    echo "Example: $0 example.com your@email.com docker"
    exit 1
fi

DOMAIN_NAME=$1
EMAIL_ADDRESS=$2
DEPLOY_TYPE=${3:-traditional}

echo -e "${GREEN}Deploying with domain: $DOMAIN_NAME${NC}"
echo -e "${GREEN}Email: $EMAIL_ADDRESS${NC}"
echo -e "${GREEN}Deploy type: $DEPLOY_TYPE${NC}"

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install basic packages
echo "Installing packages..."
sudo apt install -y curl wget git unzip software-properties-common

# Install Python 3.11
echo "Installing Python 3.11..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js 18.x
echo "Installing Node.js 18.x..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx and Certbot
echo "Installing Nginx and Certbot..."
sudo apt install -y nginx certbot python3-certbot-nginx

# Create project directory
PROJECT_DIR="/home/$USER/gemini-image-generator"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install flask flask-cors google-generativeai pillow requests werkzeug

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
cd frontend
npm install
npm run build
cd ..

# Create systemd services
echo "Creating systemd services..."

# Backend service
sudo tee /etc/systemd/system/gemini-backend.service > /dev/null <<EOF
[Unit]
Description=Gemini AI Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
sudo tee /etc/systemd/system/gemini-frontend.service > /dev/null <<EOF
[Unit]
Description=Gemini AI Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
echo "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/$DOMAIN_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    location /api/images/ {
        alias $PROJECT_DIR/backend/images/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/$DOMAIN_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
echo "Getting SSL certificate..."
sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --email $EMAIL_ADDRESS --agree-tos --non-interactive

# Enable and start services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable gemini-backend
sudo systemctl enable gemini-frontend
sudo systemctl start gemini-backend
sudo systemctl start gemini-frontend

# Setup firewall
echo "Setting up firewall..."
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create cron job for SSL renewal
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Create management scripts
echo "Creating management scripts..."

# Update script
cat > deploy-update.sh << 'EOF'
#!/bin/bash
cd /home/$USER/gemini-image-generator
git pull origin main
source venv/bin/activate
pip install -r backend/requirements.txt
cd frontend
npm install
npm run build
cd ..
sudo systemctl restart gemini-backend
sudo systemctl restart gemini-frontend
echo "Deploy completed!"
EOF

# Monitor script
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== Gemini AI Image Generator Status ==="
echo "Backend: $(sudo systemctl is-active gemini-backend)"
echo "Frontend: $(sudo systemctl is-active gemini-frontend)"
echo "Nginx: $(sudo systemctl is-active nginx)"
echo ""
echo "=== System Resources ==="
df -h /home/$USER/gemini-image-generator
free -h
EOF

chmod +x deploy-update.sh monitor.sh

# Final check
echo "Performing final checks..."
sleep 5

echo ""
echo "=========================================="
echo -e "${GREEN}QUICK DEPLOY COMPLETED!${NC}"
echo "=========================================="
echo ""
echo "🌐 Website: https://$DOMAIN_NAME"
echo "📧 Email: $EMAIL_ADDRESS"
echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo "🔧 Backend service: gemini-backend"
echo "🎨 Frontend service: gemini-frontend"
echo ""
echo "📋 Quick commands:"
echo "  - Monitor: $PROJECT_DIR/monitor.sh"
echo "  - Update: $PROJECT_DIR/deploy-update.sh"
echo "  - Restart: sudo systemctl restart gemini-backend gemini-frontend"
echo "  - Logs: sudo journalctl -u gemini-backend -f"
echo ""
echo -e "${GREEN}Project is ready to use!${NC}"

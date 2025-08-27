#!/bin/bash

# ========================================
# SCRIPT DEPLOY GEMINI AI IMAGE GENERATOR
# ========================================

set -e  # Dừng script nếu có lỗi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "Script này không nên chạy với quyền root"
   exit 1
fi

# Configuration variables
PROJECT_NAME="gemini-image-generator"
PROJECT_DIR="/home/$USER/$PROJECT_NAME"
BACKEND_PORT=5000
FRONTEND_PORT=3000
NGINX_PORT=80
NGINX_SSL_PORT=443

# Get domain name from user
echo "=========================================="
echo "DEPLOY GEMINI AI IMAGE GENERATOR"
echo "=========================================="
echo ""

read -p "Nhập tên miền của bạn (ví dụ: example.com): " DOMAIN_NAME
read -p "Nhập email của bạn (cho SSL certificate): " EMAIL_ADDRESS

if [ -z "$DOMAIN_NAME" ]; then
    print_error "Tên miền không được để trống!"
    exit 1
fi

if [ -z "$EMAIL_ADDRESS" ]; then
    print_error "Email không được để trống!"
    exit 1
fi

print_status "Bắt đầu deploy với domain: $DOMAIN_NAME"

# Update system
print_status "Cập nhật hệ thống..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
print_status "Cài đặt các package cần thiết..."
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Python 3.11
print_status "Cài đặt Python 3.11..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js 18.x
print_status "Cài đặt Node.js 18.x..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
print_status "Cài đặt Nginx..."
sudo apt install -y nginx

# Install Certbot for SSL
print_status "Cài đặt Certbot cho SSL..."
sudo apt install -y certbot python3-certbot-nginx

# Install PM2 for process management
print_status "Cài đặt PM2..."
sudo npm install -g pm2
sudo npm install -g pm2-logrotate

# Configure PM2
print_status "Cấu hình PM2..."
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
pm2 set pm2-logrotate:dateFormat YYYY-MM-DD_HH-mm-ss

# Create project directory
print_status "Tạo thư mục dự án..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone or copy project files
if [ -d ".git" ]; then
    print_status "Cập nhật code từ git..."
    git pull origin main
else
    print_status "Tạo cấu trúc dự án..."
    mkdir -p backend frontend
fi

# Create virtual environment for Python
print_status "Tạo Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Cài đặt Python dependencies..."
pip install --upgrade pip
pip install flask flask-cors google-generativeai pillow requests werkzeug

# Install Node.js dependencies
print_status "Cài đặt Node.js dependencies..."
cd frontend
npm install
npm run build
cd ..

# Create systemd service for backend
print_status "Tạo systemd service cho backend..."
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

# Create PM2 ecosystem file
print_status "Tạo PM2 ecosystem file..."
tee $PROJECT_DIR/ecosystem.config.js > /dev/null <<EOF
module.exports = {
  apps: [
    {
      name: 'gemini-backend',
      script: 'app.py',
      cwd: '$PROJECT_DIR/backend',
      interpreter: '$PROJECT_DIR/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: $BACKEND_PORT
      },
      error_file: '$PROJECT_DIR/logs/backend-error.log',
      out_file: '$PROJECT_DIR/logs/backend-out.log',
      log_file: '$PROJECT_DIR/logs/backend-combined.log',
      time: true
    },
    {
      name: 'gemini-frontend',
      script: 'npm',
      args: 'start',
      cwd: '$PROJECT_DIR/frontend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: $FRONTEND_PORT
      },
      error_file: '$PROJECT_DIR/logs/frontend-error.log',
      out_file: '$PROJECT_DIR/logs/frontend-out.log',
      log_file: '$PROJECT_DIR/logs/frontend-combined.log',
      time: true
    }
  ]
};
EOF

# Create logs directory
mkdir -p $PROJECT_DIR/logs

# Create Nginx configuration
print_status "Tạo cấu hình Nginx..."
sudo tee /etc/nginx/sites-available/$DOMAIN_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    # SSL configuration will be added by Certbot
    
    # Frontend
    location / {
        proxy_pass http://localhost:$FRONTEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Static files
    location /static/ {
        alias $PROJECT_DIR/frontend/build/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Images
    location /api/images/ {
        alias $PROJECT_DIR/backend/images/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Security headers
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

# Test Nginx configuration
print_status "Kiểm tra cấu hình Nginx..."
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Get SSL certificate
print_status "Lấy SSL certificate từ Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --email $EMAIL_ADDRESS --agree-tos --non-interactive

# Start applications with PM2
print_status "Khởi động ứng dụng với PM2..."
cd $PROJECT_DIR
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Wait for applications to start
print_status "Chờ ứng dụng khởi động..."
sleep 10

# Check PM2 status
print_status "Kiểm tra trạng thái PM2..."
pm2 status

# Create deployment script
print_status "Tạo script deploy tự động..."
tee $PROJECT_DIR/deploy-update.sh > /dev/null <<EOF
#!/bin/bash
cd $PROJECT_DIR
git pull origin main
source venv/bin/activate
pip install -r backend/requirements.txt
cd frontend
npm install
npm run build
cd ..
pm2 restart all
echo "Deploy completed!"
EOF

chmod +x $PROJECT_DIR/deploy-update.sh

# Create backup script
print_status "Tạo script backup..."
tee $PROJECT_DIR/backup.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

# Backup database and config files
tar -czf \$BACKUP_DIR/gemini_backup_\$DATE.tar.gz \\
    $PROJECT_DIR/backend/config.json \\
    $PROJECT_DIR/backend/tasks.json \\
    $PROJECT_DIR/backend/images/ \\
    $PROJECT_DIR/backend/input_images/

echo "Backup completed: \$BACKUP_DIR/gemini_backup_\$DATE.tar.gz"
EOF

chmod +x $PROJECT_DIR/backup.sh

# Create monitoring script
print_status "Tạo script monitoring..."
tee $PROJECT_DIR/monitor.sh > /dev/null <<EOF
#!/bin/bash
echo "=== Gemini AI Image Generator Status ==="
echo "PM2 Status:"
pm2 status
echo ""
echo "Nginx: \$(sudo systemctl is-active nginx)"
echo ""
echo "=== Disk Usage ==="
df -h $PROJECT_DIR
echo ""
echo "=== Memory Usage ==="
free -h
echo ""
echo "=== Recent PM2 Logs ==="
pm2 logs --lines 20
echo ""
echo "=== Nginx Error Logs ==="
sudo tail -n 10 /var/log/nginx/error.log
EOF

chmod +x $PROJECT_DIR/monitor.sh

# Setup firewall
print_status "Cấu hình firewall..."
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create cron job for SSL renewal
print_status "Tạo cron job cho SSL renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Final status check
print_status "Kiểm tra trạng thái cuối cùng..."
sleep 5

echo ""
echo "=========================================="
print_success "DEPLOY HOÀN THÀNH!"
echo "=========================================="
echo ""
echo "🌐 Website: https://$DOMAIN_NAME"
echo "📧 Email: $EMAIL_ADDRESS"
echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo "🔧 Backend app: gemini-backend (PM2)"
echo "🎨 Frontend app: gemini-frontend (PM2)"
echo ""
echo "📋 Các lệnh hữu ích:"
echo "  - Kiểm tra status: $PROJECT_DIR/monitor.sh"
echo "  - Backup dữ liệu: $PROJECT_DIR/backup.sh"
echo "  - Update code: $PROJECT_DIR/deploy-update.sh"
echo "  - Restart apps: pm2 restart all"
echo "  - View logs: pm2 logs"
echo "  - PM2 status: pm2 status"
echo ""
echo "🔒 SSL certificate sẽ tự động renew mỗi ngày"
echo "🛡️ Firewall đã được cấu hình bảo mật"
echo ""
print_success "Dự án đã sẵn sàng sử dụng!"


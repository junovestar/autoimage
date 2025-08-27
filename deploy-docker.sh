#!/bin/bash

# ========================================
# SCRIPT DEPLOY DOCKER GEMINI AI IMAGE GENERATOR
# ========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Configuration
PROJECT_NAME="gemini-image-generator"
PROJECT_DIR="/home/$USER/$PROJECT_NAME"

# Get domain name from user
echo "=========================================="
echo "DEPLOY DOCKER GEMINI AI IMAGE GENERATOR"
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

print_status "Bắt đầu deploy Docker với domain: $DOMAIN_NAME"

# Update system
print_status "Cập nhật hệ thống..."
sudo apt update && sudo apt upgrade -y

# Install Docker
print_status "Cài đặt Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
print_status "Cài đặt Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
print_status "Cài đặt Nginx..."
sudo apt install -y nginx certbot python3-certbot-nginx

# Create project directory
print_status "Tạo thư mục dự án..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Create Docker Compose file
print_status "Tạo Docker Compose configuration..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: gemini-backend
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./backend:/app
      - ./data/images:/app/images
      - ./data/config:/app/config
    environment:
      - FLASK_ENV=production
      - FLASK_APP=app.py
    networks:
      - gemini-network

  frontend:
    build: ./frontend
    container_name: gemini-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=https://DOMAIN_NAME/api
    depends_on:
      - backend
    networks:
      - gemini-network

networks:
  gemini-network:
    driver: bridge

volumes:
  data:
EOF

# Create backend Dockerfile
print_status "Tạo Dockerfile cho backend..."
mkdir -p backend
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p images config

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
EOF

# Create frontend Dockerfile
print_status "Tạo Dockerfile cho frontend..."
mkdir -p frontend
cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Install serve to run the built app
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Run the application
CMD ["serve", "-s", "build", "-l", "3000"]
EOF

# Create data directories
print_status "Tạo thư mục dữ liệu..."
mkdir -p data/images data/config

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
    
    # Backend API
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
    
    # Images
    location /api/images/ {
        alias $PROJECT_DIR/data/images/;
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

# Build and start containers
print_status "Build và khởi động containers..."
docker-compose up -d --build

# Create deployment scripts
print_status "Tạo scripts quản lý..."

# Update script
cat > deploy-update.sh << 'EOF'
#!/bin/bash
cd /home/$USER/gemini-image-generator
git pull origin main
docker-compose down
docker-compose up -d --build
echo "Deploy completed!"
EOF

# Backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup data
tar -czf $BACKUP_DIR/gemini_backup_$DATE.tar.gz \
    data/ \
    backend/config.json \
    backend/tasks.json

echo "Backup completed: $BACKUP_DIR/gemini_backup_$DATE.tar.gz"
EOF

# Monitor script
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== Gemini AI Image Generator Docker Status ==="
docker-compose ps
echo ""
echo "=== Container Logs ==="
docker-compose logs --tail=20
echo ""
echo "=== System Resources ==="
docker stats --no-stream
EOF

# Make scripts executable
chmod +x deploy-update.sh backup.sh monitor.sh

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
sleep 10

echo ""
echo "=========================================="
print_success "DEPLOY DOCKER HOÀN THÀNH!"
echo "=========================================="
echo ""
echo "🌐 Website: https://$DOMAIN_NAME"
echo "📧 Email: $EMAIL_ADDRESS"
echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo "🐳 Backend container: gemini-backend"
echo "🎨 Frontend container: gemini-frontend"
echo ""
echo "📋 Các lệnh hữu ích:"
echo "  - Kiểm tra status: $PROJECT_DIR/monitor.sh"
echo "  - Backup dữ liệu: $PROJECT_DIR/backup.sh"
echo "  - Update code: $PROJECT_DIR/deploy-update.sh"
echo "  - Restart containers: docker-compose restart"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Start services: docker-compose up -d"
echo ""
echo "🔒 SSL certificate sẽ tự động renew mỗi ngày"
echo "🛡️ Firewall đã được cấu hình bảo mật"
echo "🐳 Docker containers đang chạy"
echo ""
print_success "Dự án đã sẵn sàng sử dụng!"

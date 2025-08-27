# HƯỚNG DẪN DEPLOY GEMINI AI IMAGE GENERATOR

## 🚀 Tổng quan

Dự án này cung cấp 2 cách deploy lên Ubuntu server:

1. **Deploy truyền thống** (`deploy.sh`) - Sử dụng systemd services
2. **Deploy Docker** (`deploy-docker.sh`) - Sử dụng Docker containers

## 📋 Yêu cầu hệ thống

### Server Ubuntu
- Ubuntu 20.04 LTS trở lên
- RAM: Tối thiểu 2GB (khuyến nghị 4GB)
- CPU: 2 cores trở lên
- Disk: Tối thiểu 20GB
- Domain name đã trỏ về server
- Email hợp lệ cho SSL certificate

### Domain Name
- Domain đã được đăng ký
- DNS A record trỏ về IP server
- Có thể mất 24-48h để DNS propagate

## 🔧 Chuẩn bị server

### 1. Kết nối SSH
```bash
ssh username@your-server-ip
```

### 2. Tạo user mới (khuyến nghị)
```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
su - deploy
```

### 3. Cấu hình SSH key (tùy chọn)
```bash
# Trên máy local
ssh-copy-id deploy@your-server-ip
```

## 📦 Upload code lên server

### Cách 1: Sử dụng Git
```bash
# Trên server
git clone https://github.com/your-username/gemini-image-generator.git
cd gemini-image-generator
```

### Cách 2: Upload file trực tiếp
```bash
# Trên máy local
scp -r . deploy@your-server-ip:/home/deploy/gemini-image-generator/
```

## 🚀 Deploy truyền thống

### 1. Chạy script deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

### 2. Nhập thông tin khi được hỏi
- Domain name: `example.com`
- Email: `your-email@example.com`

### 3. Chờ quá trình hoàn thành
Script sẽ tự động:
- Cài đặt Python 3.11, Node.js 18.x, Nginx
- Cấu hình SSL certificate
- Tạo systemd services
- Khởi động ứng dụng

## 🐳 Deploy Docker

### 1. Chạy script deploy Docker
```bash
chmod +x deploy-docker.sh
./deploy-docker.sh
```

### 2. Nhập thông tin khi được hỏi
- Domain name: `example.com`
- Email: `your-email@example.com`

### 3. Chờ quá trình hoàn thành
Script sẽ tự động:
- Cài đặt Docker và Docker Compose
- Tạo Dockerfiles và docker-compose.yml
- Build và khởi động containers
- Cấu hình SSL certificate

## 🔍 Kiểm tra sau khi deploy

### 1. Kiểm tra website
```bash
# Truy cập website
https://your-domain.com
```

### 2. Kiểm tra services (Deploy truyền thống)
```bash
# Kiểm tra status
sudo systemctl status gemini-backend
sudo systemctl status gemini-frontend
sudo systemctl status nginx

# Xem logs
sudo journalctl -u gemini-backend -f
sudo journalctl -u gemini-frontend -f
```

### 3. Kiểm tra containers (Deploy Docker)
```bash
# Kiểm tra containers
docker-compose ps

# Xem logs
docker-compose logs -f

# Kiểm tra resources
docker stats
```

## 📋 Quản lý ứng dụng

### Deploy truyền thống

#### Restart services
```bash
sudo systemctl restart gemini-backend
sudo systemctl restart gemini-frontend
sudo systemctl restart nginx
```

#### Update code
```bash
cd /home/deploy/gemini-image-generator
./deploy-update.sh
```

#### Backup dữ liệu
```bash
cd /home/deploy/gemini-image-generator
./backup.sh
```

#### Monitor system
```bash
cd /home/deploy/gemini-image-generator
./monitor.sh
```

### Deploy Docker

#### Restart containers
```bash
cd /home/deploy/gemini-image-generator
docker-compose restart
```

#### Update code
```bash
cd /home/deploy/gemini-image-generator
./deploy-update.sh
```

#### Backup dữ liệu
```bash
cd /home/deploy/gemini-image-generator
./backup.sh
```

#### Monitor system
```bash
cd /home/deploy/gemini-image-generator
./monitor.sh
```

## 🔧 Cấu hình bổ sung

### 1. Cấu hình API Keys
Sau khi deploy, truy cập website và thêm API keys trong tab "Cài đặt".

### 2. Cấu hình firewall
```bash
# Kiểm tra firewall
sudo ufw status

# Mở thêm port nếu cần
sudo ufw allow 8080
```

### 3. Cấu hình backup tự động
```bash
# Thêm cron job backup hàng ngày
crontab -e
# Thêm dòng: 0 2 * * * /home/deploy/gemini-image-generator/backup.sh
```

### 4. Cấu hình monitoring
```bash
# Cài đặt monitoring tools
sudo apt install htop iotop nethogs

# Theo dõi system resources
htop
```

## 🛠️ Troubleshooting

### 1. Lỗi SSL certificate
```bash
# Kiểm tra SSL
sudo certbot certificates

# Renew SSL
sudo certbot renew

# Xem logs
sudo journalctl -u certbot
```

### 2. Lỗi Nginx
```bash
# Kiểm tra cấu hình
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Xem logs
sudo tail -f /var/log/nginx/error.log
```

### 3. Lỗi Backend
```bash
# Kiểm tra logs
sudo journalctl -u gemini-backend -f

# Kiểm tra port
sudo netstat -tlnp | grep 5000

# Restart service
sudo systemctl restart gemini-backend
```

### 4. Lỗi Frontend
```bash
# Kiểm tra logs
sudo journalctl -u gemini-frontend -f

# Kiểm tra port
sudo netstat -tlnp | grep 3000

# Restart service
sudo systemctl restart gemini-frontend
```

### 5. Lỗi Docker
```bash
# Kiểm tra containers
docker-compose ps

# Xem logs
docker-compose logs

# Restart containers
docker-compose down && docker-compose up -d

# Clean up
docker system prune -f
```

## 📊 Monitoring và Maintenance

### 1. System monitoring
```bash
# CPU và Memory
htop

# Disk usage
df -h

# Network
nethogs

# Process
ps aux | grep python
ps aux | grep node
```

### 2. Log rotation
```bash
# Cấu hình log rotation
sudo nano /etc/logrotate.d/gemini

# Thêm cấu hình
/home/deploy/gemini-image-generator/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
}
```

### 3. Performance optimization
```bash
# Tối ưu Nginx
sudo nano /etc/nginx/nginx.conf

# Tối ưu system
sudo nano /etc/sysctl.conf
```

## 🔒 Security

### 1. Firewall
```bash
# Kiểm tra firewall
sudo ufw status

# Chỉ mở port cần thiết
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### 2. SSL/TLS
```bash
# Kiểm tra SSL
openssl s_client -connect your-domain.com:443

# Test SSL configuration
curl -I https://your-domain.com
```

### 3. Updates
```bash
# Update system
sudo apt update && sudo apt upgrade

# Update SSL certificates
sudo certbot renew
```

## 📞 Support

Nếu gặp vấn đề, hãy kiểm tra:

1. **Logs**: Xem logs của từng service
2. **Status**: Kiểm tra trạng thái services
3. **Network**: Kiểm tra kết nối mạng
4. **Resources**: Kiểm tra tài nguyên hệ thống

### Thông tin liên hệ
- Email: your-email@example.com
- GitHub: https://github.com/your-username/gemini-image-generator
- Documentation: https://your-domain.com/docs

---

**Lưu ý**: Đảm bảo backup dữ liệu thường xuyên và theo dõi tài nguyên hệ thống để tránh downtime.

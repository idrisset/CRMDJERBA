#!/bin/bash
# ============================================================
# DJERBA CONSTRUCTION CRM - Installation VPS (Ubuntu 24)
# Backend: FastAPI + MongoDB Atlas + Nginx + SSL
# ============================================================
set -e
echo "=========================================="
echo "  DJERBA CONSTRUCTION CRM - Installation"
echo "=========================================="

# --- 1. Mise à jour système ---
echo "[1/5] Mise à jour du système..."
apt update && apt upgrade -y
apt install -y curl wget unzip python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw

# --- 2. Firewall ---
echo "[2/5] Configuration du firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# --- 3. Backend ---
echo "[3/5] Installation du backend..."
mkdir -p /opt/crm-backend /opt/crm-backend/backups
cd /opt/crm-backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn motor bcrypt PyJWT python-dotenv python-multipart \
    openpyxl reportlab resend APScheduler websockets "pydantic[email]" aiohttp \
    certifi dnspython

# --- 4. Fichier .env ---
echo "[4/5] Création du fichier .env..."
JWT_SECRET=$(openssl rand -hex 32)
cat > /opt/crm-backend/.env << EOF
MONGO_URL="mongodb+srv://saighryma20_db_user:crm2026@cluster0.gyfvfdc.mongodb.net/?appName=Cluster0"
DB_NAME="crm_djerba"
CORS_ORIGINS="https://crmdjerba.com,https://www.crmdjerba.com,https://api.crmdjerba.com"
JWT_SECRET="$JWT_SECRET"
ADMIN_EMAIL="admin@immo.com"
ADMIN_PASSWORD="admin123"
FRONTEND_URL="https://crmdjerba.com"
RESEND_API_KEY="re_B3wSKy6s_LckQjzYcMVprB4aEDGqX24fP"
SENDER_EMAIL="onboarding@resend.dev"
NOTIFICATION_EMAIL="saighryma@gmail.com"
BACKUP_DIR="/opt/crm-backend/backups"
WHATSAPP_VERIFY_TOKEN=""
WHATSAPP_PHONE_NUMBER_ID=""
META_ACCESS_TOKEN=""
META_APP_SECRET=""
EOF

# --- 5. Service systemd + Nginx ---
echo "[5/5] Configuration services..."
cat > /etc/systemd/system/crm-backend.service << 'SERVICEEOF'
[Unit]
Description=DJERBA CRM Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/crm-backend
EnvironmentFile=/opt/crm-backend/.env
ExecStart=/opt/crm-backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

cat > /etc/nginx/sites-available/api.crmdjerba.com << 'NGINXEOF'
server {
    listen 80;
    server_name api.crmdjerba.com;
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/api.crmdjerba.com /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl daemon-reload
nginx -t && systemctl reload nginx

echo ""
echo "=========================================="
echo "  INSTALLATION TERMINEE"
echo "=========================================="
echo ""
echo "Prochaines étapes :"
echo "  1. wget LIEN_BACKEND -O backend.zip && unzip -o backend.zip && rm backend.zip"
echo "  2. systemctl start crm-backend && systemctl enable crm-backend"
echo "  3. curl http://localhost:8001/api/health"
echo "  4. certbot --nginx -d api.crmdjerba.com (après DNS)"
echo ""

#!/bin/bash
# ============================================================
# DJERBA CONSTRUCTION CRM - Installation automatique VPS
# VPS: Ubuntu (DigitalOcean)
# Backend: FastAPI + MongoDB + Nginx + SSL
# ============================================================

set -e
echo "=========================================="
echo "  DJERBA CONSTRUCTION CRM - Installation"
echo "=========================================="

# --- 1. Mise à jour système ---
echo "[1/8] Mise à jour du système..."
apt update && apt upgrade -y
apt install -y curl wget git unzip python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw gnupg

# --- 2. Installer MongoDB 7.0 ---
echo "[2/8] Installation de MongoDB..."
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
apt update
apt install -y mongodb-org
systemctl start mongod
systemctl enable mongod
echo "MongoDB installé et démarré."

# --- 3. Firewall ---
echo "[3/8] Configuration du firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# --- 4. Créer le dossier backend ---
echo "[4/8] Installation du backend..."
mkdir -p /opt/crm-backend
cd /opt/crm-backend

# Créer l'environnement Python
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install fastapi uvicorn motor bcrypt pyjwt python-dotenv python-multipart \
    openpyxl reportlab resend apscheduler websockets pydantic[email] aiohttp

echo "Dépendances Python installées."

# --- 5. Fichier .env ---
echo "[5/8] Création du fichier .env..."
cat > /opt/crm-backend/.env << 'ENVEOF'
MONGO_URL="mongodb://localhost:27017"
DB_NAME="crm_djerba"
CORS_ORIGINS="https://crmdjerba.com,https://www.crmdjerba.com,https://api.crmdjerba.com"
JWT_SECRET="CHANGEZ_MOI_avec_une_cle_secrete_aleatoire_64_caracteres_minimum"
ADMIN_EMAIL="admin@immo.com"
ADMIN_PASSWORD="admin123"
FRONTEND_URL="https://crmdjerba.com"
RESEND_API_KEY="re_B3wSKy6s_LckQjzYcMVprB4aEDGqX24fP"
SENDER_EMAIL="onboarding@resend.dev"
NOTIFICATION_EMAIL="saighryma@gmail.com"
WHATSAPP_VERIFY_TOKEN="djerba_construction_whatsapp_verify_2024"
WHATSAPP_PHONE_NUMBER_ID=""
META_ACCESS_TOKEN=""
META_APP_SECRET=""
ENVEOF

echo "Fichier .env créé. PENSEZ A CHANGER JWT_SECRET !"

# --- 6. Service systemd ---
echo "[6/8] Création du service systemd..."
cat > /etc/systemd/system/crm-backend.service << 'SERVICEEOF'
[Unit]
Description=DJERBA CRM Backend (FastAPI)
After=network.target mongod.service
Wants=mongod.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/crm-backend
Environment=PATH=/opt/crm-backend/venv/bin
EnvironmentFile=/opt/crm-backend/.env
ExecStart=/opt/crm-backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
echo "Service systemd créé."

# --- 7. Nginx reverse proxy ---
echo "[7/8] Configuration Nginx..."
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
        proxy_send_timeout 300s;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/api.crmdjerba.com /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
echo "Nginx configuré."

# --- 8. Instructions finales ---
echo ""
echo "=========================================="
echo "  INSTALLATION TERMINEE"
echo "=========================================="
echo ""
echo "ETAPES RESTANTES :"
echo ""
echo "1. Uploadez les fichiers backend :"
echo "   scp server.py backup_manager.py seed_edimco.py root@159.65.195.252:/opt/crm-backend/"
echo ""
echo "2. Changez le JWT_SECRET dans /opt/crm-backend/.env"
echo ""
echo "3. Démarrez le backend :"
echo "   systemctl start crm-backend"
echo "   systemctl enable crm-backend"
echo ""
echo "4. Configurez DNS : api.crmdjerba.com -> 159.65.195.252"
echo ""
echo "5. Installez SSL (après propagation DNS) :"
echo "   certbot --nginx -d api.crmdjerba.com"
echo ""
echo "6. Testez : curl https://api.crmdjerba.com/api/health"
echo ""

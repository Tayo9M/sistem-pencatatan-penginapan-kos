# Panduan Deployment Sistem Pencatatan Penginapan Kos

Panduan ini menjelaskan langkah-langkah untuk men-deploy aplikasi Sistem Pencatatan Penginapan Kos ke lingkungan produksi.

## Prasyarat

- Python 3.8 atau lebih baru
- MySQL
- Web server (Nginx, Apache)
- pip (Python package manager)
- Akses terminal/command line

## 1. Persiapan Server

### 1.1 Instalasi Dependensi Sistem

Pada sistem berbasis Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv mysql-server nginx
sudo apt-get install -y build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev
sudo apt-get install -y default-libmysqlclient-dev  # Untuk mysqlclient
```

## 2. Menyiapkan Database

### 2.1 Membuat Database MySQL
```bash
sudo mysql -u root -p
CREATE DATABASE kos_db;
CREATE USER 'kos_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON kos_db.* TO 'kos_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2.2 Import Skema Database
```bash
mysql -u kos_user -p kos_db < database_schema.sql
```

## 3. Mengatur Aplikasi

### 3.1 Mengunduh Kode
```bash
git clone https://github.com/username/sistem-pencatatan-penginapan-kos.git
cd sistem-pencatatan-penginapan-kos
```

### 3.2 Membuat Environment Python
```bash
python3 -m venv venv
source venv/bin/activate  # Pada Windows: venv\Scripts\activate
```

### 3.3 Instalasi Dependensi Python
```bash
pip install -r requirements.txt
# Pastikan mysqlclient terinstal untuk koneksi MySQL
pip install mysqlclient
```

### 3.4 Mengatur Variabel Lingkungan
Buat file `.env` di folder root proyek:
```
DATABASE_URL=mysql://kos_user:password@localhost/kos_db
SESSION_SECRET=secret_key_yang_aman_dan_panjang
```

## 4. Menjalankan Aplikasi dengan Gunicorn

### 4.1 Instal Gunicorn
```bash
pip install gunicorn
```

### 4.2 Menjalankan Aplikasi
```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

## 5. Konfigurasi Nginx sebagai Reverse Proxy

### 5.1 Buat Konfigurasi Nginx
Buat file `/etc/nginx/sites-available/kos-system`:
```
server {
    listen 80;
    server_name domain.com www.domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/sistem-pencatatan-penginapan-kos/static;
    }
}
```

### 5.2 Aktifkan Konfigurasi
```bash
sudo ln -s /etc/nginx/sites-available/kos-system /etc/nginx/sites-enabled
sudo nginx -t  # Verifikasi konfigurasi
sudo systemctl restart nginx
```

## 6. Menjalankan Aplikasi dengan Systemd

### 6.1 Buat Unit File Systemd
Buat file `/etc/systemd/system/kos-system.service`:
```
[Unit]
Description=Gunicorn instance to serve Sistem Pencatatan Penginapan Kos
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/sistem-pencatatan-penginapan-kos
Environment="PATH=/path/to/sistem-pencatatan-penginapan-kos/venv/bin"
Environment="DATABASE_URL=postgresql://kos_user:password@localhost/kos_db"
Environment="SESSION_SECRET=secret_key_yang_aman_dan_panjang"
ExecStart=/path/to/sistem-pencatatan-penginapan-kos/venv/bin/gunicorn --workers 3 --bind unix:kos-system.sock -m 007 main:app

[Install]
WantedBy=multi-user.target
```

### 6.2 Mengaktifkan Service
```bash
sudo systemctl start kos-system
sudo systemctl enable kos-system
```

## 7. Keamanan

- Selalu gunakan HTTPS di produksi dengan sertifikat SSL/TLS.
- Ganti SESSION_SECRET dengan string acak yang panjang dan aman.
- Atur firewall untuk mengizinkan hanya port 80, 443, dan SSH.
- Nonaktifkan akses langsung ke database dari jaringan luar.
- Backup database secara teratur.

## 8. Pemeliharaan dan Pembaruan

### 8.1 Memperbarui Aplikasi
```bash
cd /path/to/sistem-pencatatan-penginapan-kos
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart kos-system
```

### 8.2 Backup Database
```bash
pg_dump -U kos_user kos_db > backup_$(date +%Y%m%d).sql
```
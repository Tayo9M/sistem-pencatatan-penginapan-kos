# Sistem Pencatatan Penginapan Kos

Aplikasi web berbasis Flask untuk manajemen properti penginapan kos, yang memungkinkan pelacakan hunian, manajemen keuangan, dan pembuatan laporan.

## Fitur Utama

- **Manajemen Properti**: Mengelola beberapa properti dan kamar
- **Pencatatan Hunian**: Mencatat penghuni kos, periode hunian, dan status pembayaran
- **Manajemen Keuangan**: Melacak pendapatan dan pengeluaran untuk setiap properti
- **Laporan dan Ekspor PDF**: Menghasilkan laporan yang dapat diunduh dalam format PDF
- **Kalender Keuangan**: Visualisasi transaksi keuangan dalam tampilan kalender
- **Statistik**: Grafik dan visualisasi untuk tingkat hunian dan keuangan
- **Manajemen Pengguna**: Sistem kontrol akses berbasis peran (admin, manager, staff)

## Teknologi

- **Backend**: Flask (Python)
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Otentikasi**: Flask-Login
- **Frontend**: Bootstrap, JavaScript (Charts.js)
- **Ekspor PDF**: WeasyPrint

## Struktur Proyek

```
.
├── app.py                   # Konfigurasi dan inisialisasi aplikasi Flask
├── main.py                  # Entry point aplikasi
├── models.py                # Model database SQLAlchemy
├── routes.py                # Route dan fungsi view utama
├── pdf_routes.py            # Route untuk fungsi ekspor PDF
├── pdf_generator.py         # Fungsi untuk menghasilkan PDF
├── auth_helpers.py          # Fungsi helper otentikasi
├── static/                  # File statis (CSS, JS, gambar)
│   ├── css/                 # File CSS
│   ├── js/                  # File JavaScript
│   └── pdf/                 # Folder penyimpanan PDF sementara
└── templates/               # Template HTML
    └── pdf/                 # Template untuk generasi PDF
```

## Persyaratan

- Python 3.8+
- Flask
- PostgreSQL
- SQLAlchemy
- WeasyPrint (dan dependensinya)
- Gunicorn (untuk deployment)

## Instalasi dan Penggunaan

1. Clone repositori:
   ```
   git clone https://github.com/username/sistem-pencatatan-penginapan-kos.git
   cd sistem-pencatatan-penginapan-kos
   ```

2. Instal dependensi:
   ```
   pip install -r requirements.txt
   ```

3. Konfigurasi database:
   ```
   # Set variabel lingkungan DATABASE_URL
   export DATABASE_URL=postgresql://username:password@localhost/kos_db
   ```

4. Jalankan aplikasi:
   ```
   python main.py
   ```

## Kontributor

Aplikasi ini dikembangkan oleh [Nama Anda].

## Lisensi

[Jenis lisensi yang digunakan]
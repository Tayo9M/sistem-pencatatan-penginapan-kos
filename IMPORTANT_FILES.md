# File-file Penting untuk GitHub

Berikut ini adalah daftar file dan folder yang perlu diexport ke GitHub:

## File Utama
- `app.py`: Konfigurasi utama aplikasi Flask
- `main.py`: Entry point aplikasi
- `models.py`: Definisi model database
- `routes.py`: Route utama aplikasi
- `auth_helpers.py`: Helper fungsi untuk autentikasi
- `pdf_generator.py`: Fungsi untuk generasi PDF
- `pdf_routes.py`: Route untuk export PDF
- `create_financial_records.py`: Utilitas untuk membuat record keuangan

## Folder Utama
- `static/`: File statis (CSS, JavaScript)
  - `static/css/`: Stylesheet
  - `static/js/`: File JavaScript (calendar.js, charts.js)
  - `static/pdf/`: (Folder kosong untuk output PDF)
- `templates/`: Template HTML
  - `templates/pdf/`: Template untuk generasi PDF

## File Konfigurasi
- `.gitignore`: File yang diabaikan Git
- `LICENSE`: Lisensi proyek
- `README.md`: Dokumentasi proyek
- `deployment_requirements.txt`: Rename ke requirements.txt di GitHub

## File yang TIDAK Perlu Diexport
- `__pycache__/`
- `.replit`
- `.upm/`
- `.pythonlibs/`
- `*.db`
- `test.pdf`
- Temporary files

## Catatan Deployment
- Gunakan file `deployment_requirements.txt` sebagai `requirements.txt` di GitHub
- Pastikan untuk mengatur variabel lingkungan `DATABASE_URL` saat deployment
- Gunakan PostgreSQL untuk production
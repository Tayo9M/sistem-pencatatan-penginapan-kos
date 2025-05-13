# Instruksi Pemindahan ke GitHub

## Langkah-langkah Membuat Repositori GitHub dan Meng-upload Proyek

### 1. Membuat Repositori GitHub
1. Buka [GitHub](https://github.com/) dan login ke akun Anda
2. Klik tombol "+" di pojok kanan atas, kemudian pilih "New repository"
3. Masukkan nama repositori: `sistem-pencatatan-penginapan-kos`
4. Tambahkan deskripsi: "Sistem manajemen properti kos berbasis web menggunakan Flask dan PostgreSQL"
5. Pilih "Public" (atau "Private" jika Anda ingin repositori privat)
6. Centang "Initialize this repository with a README"
7. Klik "Create repository"

### 2. Mengunduh file dari Replit
1. Di Replit, klik pada setiap file yang ada di checklist dan unduh satu per satu:
   - File utama aplikasi (.py files)
   - Folder static (CSS, JS)
   - Folder templates
   - File-file tambahan (.gitignore, README.md, dll)
2. Anda juga bisa menggunakan fitur "Download as Zip" di Replit jika tersedia, kemudian ekstrak file-file yang diperlukan

### 3. Mengunggah ke GitHub
Metode 1: Melalui Web Interface GitHub
1. Buka repositori GitHub yang telah dibuat
2. Klik tombol "Add file" → "Upload files"
3. Seret dan lepas file-file yang telah diunduh
4. Klik "Commit changes"

Metode 2: Menggunakan Git di Komputer Lokal (Disarankan)
1. Clone repositori GitHub ke komputer lokal:
   ```
   git clone https://github.com/username/sistem-pencatatan-penginapan-kos.git
   cd sistem-pencatatan-penginapan-kos
   ```

2. Salin semua file yang telah diunduh ke folder repositori lokal
3. Rename `requirements_mysql.txt` menjadi `requirements.txt` (karena kita menggunakan MySQL, bukan PostgreSQL)
4. Tambahkan file-file ke staging area:
   ```
   git add .
   ```
5. Buat commit:
   ```
   git commit -m "Initial commit: Transfer dari Replit"
   ```
6. Push ke GitHub:
   ```
   git push origin main
   ```

### 4. Setelah Berhasil Upload
1. Verifikasi semua file telah terunggah dengan benar di GitHub
2. Periksa README.md sudah terlihat dengan baik di halaman utama repositori
3. Baca DEPLOYMENT_GUIDE.md untuk petunjuk tentang cara men-deploy aplikasi

## Catatan Penting
- Pastikan untuk tidak mengupload file-file sensitif seperti kunci API atau kredensial database
- Jangan lupa untuk mengubah password yang ada di file `initial_data.py` sebelum digunakan di lingkungan produksi
- Tambahkan informasi kontak Anda di README.md agar orang lain bisa menghubungi jika ada pertanyaan

## File Penting yang Harus Ada di GitHub:
- app.py
- main.py
- models.py
- routes.py
- pdf_routes.py
- pdf_generator.py
- auth_helpers.py
- initial_data.py
- create_financial_records.py
- Folder static/
- Folder templates/
- requirements.txt (dari requirements_mysql.txt)
- .gitignore
- LICENSE
- README.md
- DEPLOYMENT_GUIDE.md
- database_schema.sql (skema untuk MySQL)
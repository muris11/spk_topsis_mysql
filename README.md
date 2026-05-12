# spk_topsis_mysql

Sistem Informasi Kota Cerdas - POLINDRA

Modul Praktikum: Sistem Pendukung Keputusan (TOPSIS)

Ringkasan

- Aplikasi Flask untuk perhitungan TOPSIS menggunakan data dari MySQL (`spk_topsis`).
- Folder ini berisi `app.py`, `requirements.txt`, template HTML dan beberapa utility script untuk testing.

Persiapan lingkungan (Windows)

1. Pastikan Python 3.13 terinstall.
2. Jalankan dependencies:

```powershell
Set-Location "C:\laragon\www\Matkul SPK\spk-topsis-mysql-flask"
C:/Users/rifqy/AppData/Local/Programs/Python/Python313/python.exe -m pip install -r requirements.txt
# atau gunakan skrip yang disertakan
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Menjalankan aplikasi

```powershell
Set-Location "C:\laragon\www\Matkul SPK\spk-topsis-mysql-flask"
py .\app.py
# atau lebih stabil tanpa reloader:
py -c "from app import app; app.run(debug=False)"
```

Buka http://127.0.0.1:5000

Database

- Database: `spk_topsis` (MySQL)
- Tabel utama: `alternatif`, `kriteria`, `nilai_alternatif`.
- Contoh: untuk menambah alternatif dan nilainya, lihat file `docs/sql_examples.md` (disertakan di repo).

Snapshot & bukti untuk laporan

- Saya merekomendasikan langkah berikut untuk bukti di laporan:
  1. Backup database: `mysqldump -u root -p spk_topsis > spk_topsis_backup.sql`
  2. Ambil snapshot ranking sebelum perubahan:
     `py print_result.py > before.txt`
  3. Terapkan perubahan SQL (ubah bobot / tambah alternatif / isi nilai) menggunakan file `changes.sql`.
  4. Ambil snapshot setelah perubahan:
     `py print_result.py > after.txt`
  5. Bandingkan: `fc before.txt after.txt` dan sertakan `before.txt`, `after.txt`, `changes.sql` di laporan.

File penting di repository

- `app.py` — logika TOPSIS dan route Flask.
- `print_result.py` — script bantu untuk menghasilkan ranking (snapshot teks).
- `call_funcs.py` / `run_request.py` — utility pengujian lokal.
- `install.ps1` — skrip instalasi dependencies di Windows.
- `requirements.txt` — daftar paket Python.

Contoh singkat SQL (ubah bobot & tambah alternatif)

```sql
-- ubah bobot kriteria K1
UPDATE kriteria SET bobot_awal = 50 WHERE kode = 'K1';

-- tambah alternatif dan nilai (ganti <nilai> sesuai kriteria)
INSERT INTO alternatif (kode,nama) VALUES ('A6','Alternatif 6');
SET @alt_id := LAST_INSERT_ID();
INSERT INTO nilai_alternatif (alternatif_id,kriteria_id,nilai) VALUES
(@alt_id,1,7), (@alt_id,2,8), (@alt_id,3,6);
```

Lisensi & kontak

- Skrip ini untuk tujuan praktikum. Jika butuh bantuan lebih lanjut atau saya jalankan perubahan dan buatkan bukti, beri tahu saya.

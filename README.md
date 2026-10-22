# Dashboard Regresi Panel: Dampak Program MBG

Dashboard Streamlit untuk regresi data panel 34 provinsi Indonesia (2019-2025):
pengaruh anggaran Makan Bergizi Gratis (MBG) terhadap stunting, kemiskinan, dan pengangguran muda.

> **Catatan:** `data_panel.csv` adalah data **simulasi** untuk demo. Ganti dengan data asli
> (BPS, SSGI Kemenkes) dengan nama kolom yang sama sebelum menarik kesimpulan.

## Struktur repo (semua di root, tanpa subfolder)
| File | Fungsi |
|---|---|
| `app.py` | aplikasi Streamlit (dashboard + regresi) |
| `data_panel.csv` | dataset panel |
| `requirements.txt` | daftar library untuk Streamlit Cloud |
| `make_data.py` | skrip pembuat dataset simulasi (opsional) |
| `README.md`, `.gitignore` | dokumentasi |

## Kolom dataset
`provinsi, tahun, stunting_pct, kemiskinan_pct, pengangguran_muda_pct, mbg_per_kapita_ribu, pdrb_per_kapita_juta, akses_internet_pct, upah_minimum_juta`

## Jalankan lokal
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Community Cloud
1. Push semua file ke repo GitHub (root repo).
2. Buka https://share.streamlit.io, login dengan GitHub.
3. **Create app** → pilih repo, branch `main`, main file `app.py` → **Deploy**.
4. Jika ada error `No module named ...`, cek `requirements.txt`, lalu **Manage app → Reboot app**.

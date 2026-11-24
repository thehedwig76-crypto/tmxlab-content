# Cara renew token Threads (setiap 2 bulan, ~2 minit)

Token Threads tamat 60 hari selepas dibuat. Bila tamat, post berhenti. Data dalam GitHub tak hilang.

- Token sekarang dibuat: **23 Nov 2026** → tamat sekitar **22 Jan 2027**
- Peringatan dihantar 2 minggu awal: **8 Jan 2027**

---

## Bahagian A — Ambil token baru (Meta Developer)

1. Buka link ini (login akaun Facebook/Meta yang sama):
   **https://developers.facebook.com/apps/1544723040779159/use_cases/customize/settings/?use_case_enum=THREADS_API**
   - Kalau link tak jalan: developers.facebook.com → **My Apps** → pilih **tmxlab poster** → menu kiri **Use cases** (ikon pensel) → pada **Access the Threads API** tekan ikon pensel / **Customize** → tab **Settings**.
2. Scroll ke paling bawah, bahagian **User Token Generator**.
3. Pada baris **tmxlab**, tekan **Generate Access Token**.
4. Window kecil keluar → login Threads kalau diminta → **Continue / Allow**.
5. Token panjang keluar (mula dengan **TH…**) → tick **I understand** → tekan **Copy**.

⚠️ Jangan hantar token dalam chat atau kepada sesiapa.

---

## Bahagian B — Tampal dalam GitHub

1. Buka: **https://github.com/thehedwig76-crypto/tmxlab-content/settings/secrets/actions**
   - Kalau link tak jalan: github.com → repo **tmxlab-content** → tab **Settings** (atas kanan) → menu kiri **Secrets and variables** → **Actions**.
2. Dalam senarai **Repository secrets**, cari **THREADS_ACCESS_TOKEN** → tekan ikon pensel (**Update**).
3. Padam isi lama, **paste** token baru (Cmd+V).
4. Tekan **Update secret**.

---

## Bahagian C — Semak (pilihan)

1. Buka: **https://github.com/thehedwig76-crypto/tmxlab-content/actions**
2. Menu kiri pilih **Threads auto post** → butang **Run workflow** → pilih **check** → **Run workflow**.
3. Tunggu 1 minit. ✅ hijau = token OK. ❌ merah = ulang Bahagian A & B.

Siap. Bagitahu Claude "dah renew" supaya peringatan seterusnya diset.

# Threads @tmxlab

- `posts.json` — senarai post (masa waktu Malaysia + teks).
- `posted.json` — rekod post yang dah keluar (diisi automatik).
- Post keluar automatik melalui GitHub Actions (`Threads auto post`), semak setiap 15 minit.

Tukar / tambah post: edit `posts.json`. Setiap item perlukan `id` unik, `time` (contoh `2026-12-31T08:30:00+08:00`) dan `text` (maks 500 aksara).

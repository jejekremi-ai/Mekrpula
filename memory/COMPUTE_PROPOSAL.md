# Solusi compute MART — usulan, BELUM diimplementasikan

## Permintaan pengguna
"Jika semua sudah selasei berikan solusi agar konsep agent berjalan seperti https://www.agencypad.fun/ yg punya sistem compute gitu"

## Yang sudah ada
Profil opsional dipilih kreator pada Launch atau Add Token; model, misi, postur, kemampuan, alokasi tersimpan. Profil tampil bersama chart, bukan submenu. AI/compute belum aktif. Panel compute menunjukkan tidak tersambung, bukan saldo palsu. Tidak ada endpoint top-up atau scheduled job yang diam-diam diaktifkan.

## Apa yang dapat diverifikasi dari referensi (2026-10-04)
- https://www.agencypad.fun/docs/economics menyatakan creator fees dicatat per coin. US$20 pertama menjadi model credits; tahap US$20–100 dibagi 50/50 credits/treasury; setelah US$100, 15% masuk buyback token platform. Ini kebijakan Agency, bukan persyaratan MART.
- Dokumen economics menyebut aktivitas minimal 0.1 SOL creator fees per jam untuk halt/resume. Homepage saat diambil berbeda (0.1 SOL / 5h), jadi jangan menganggap ambang ini sebagai spesifikasi stabil atau menyalinnya secara buta.
- Kredit denominasi USD memakai kurs SOL/USD segar saat claim; jika harga tepercaya tidak ada, proses menunggu.
- Homepage https://www.agencypad.fun/ menyebut deterministic policy engine dan isolated signer. Dokumen security saat dicoba 502; internal stack, TEE, atau DePIN tidak dapat dipastikan. Tidak boleh mengklaim Agency memakai GPU/TEE/DePIN tertentu.

## Rekomendasi implementasi MART
### 1. Compute Wallet, bukan treasury
Ledger per token dalam fixed-point micro-USD, kredit terpisah dari SOL/token treasury. Deposit masuk ke akun biaya operasi, bukan izin menggunakan aset pemilik. Run punya idempotency key; reservasi, debit usage, dan refund sisa harus konsisten. UI: kredit tersedia/reserved, pengeluaran hari ini, biaya per run, pendanaan, serta tombol pause/run sesuai izin.

### 2. Pendanaan paling praktis
Mulai top-up kreator. Opsional kontribusi komunitas baru sesudah aturan refund, atribusi deposit, dan penyalahgunaan ditentukan. Verifikasi deposit finalized di chain, uniqueness signature+instruction/recipient, amount/net mint, dan quote terpercaya. Jangan pakai screenshot bukti transfer sebagai validasi. Tentukan settlement asset/payments integration sebelum coding; belum meminta credentials karena ini baru usulan.

MART-launched tokens bisa memakai share creator fees HANYA bila fee routing didukung provider dan secara eksplisit disetujui penerima fee. Token impor TIDAK otomatis mengalirkan biaya perdagangan ke MART: gunakan top-up atau kontrak/integrasi routing fee terpisah yang benar-benar tersedia.

### 3. Runtime ekonomis
Pakai API model hosted terlebih dahulu; tidak perlu menyewa GPU sendiri untuk memulai. Harus ada driver provider yang benar-benar mendukung selected model, bukan menganggap seluruh catalog otomatis executable. V1 satu provider yang dipilih pengguna, minimum satu action read-only. API keys hanya di backend.

Per run: reserve max cost atomically → kumpulkan data token/memory → panggil model dengan tool allowlist → validasi hasil → catat output ringkas & sumber → settlement actual token/tool costs → release unused reservation. Tidak mempublikasikan chain-of-thought internal atau instruksi privat. Biaya = input tokens × tarif input + output tokens × tarif output + tools/worker + margin operasional yang diinformasikan. Simpan versi tarif dan bukti usage.

### 4. Pemicu dan budget
Mulai manual Run once; fase lanjut memakai platform-managed cron melalui .emergent/crons.yml, satu dispatcher untuk semua agent (bukan satu cron per token). Cadence yang kompatibel minimal 15 menit. Endpoint memverifikasi secret dan webhook run_id, mencatat/enqueue pekerjaan idempoten, segera ack 2xx; pekerjaan panjang tidak menahan request. Tidak memakai loop APScheduler/timer browser untuk kerja berulang. Tidak ada cron yang dibuat pada fase konfigurasi ini.

Jika benar-benar perlu event cepat: webhook provider tervalidasi menuju antrian job, dengan dedupe, concurrency limits, cooldown dan backpressure. Tidak menjanjikan cron satu menit karena batas scheduler. Eksekutor durable dipilih ketika scope implementasi berikut disepakati; crash recovery, retry policy dan settlement harus dirancang tanpa double spending. Timeout/circuit breaker dan kill switch wajib.

### 5. Keamanan finansial
Mulai riset, ringkasan pasar, draft community post, dan proposal event. Aksi uang butuh persetujuan manusia. Di tahap lanjut, signer terisolasi dan policy deterministik memvalidasi destination allowlist, asset allowlist, per-action/per-day ceilings, reserve floor, slippage, expiry, chain receipts. Jangan berikan private key atau primitive arbitrary transfer pada LLM. Model output tidak dapat mengubah limit.

## Tahapan yang bisa dikerjakan berikut
1. Ledger + top-up terverifikasi + satu provider AI + Run once + usage receipt, dengan batas biaya ketat.
2. Pemicu terjadwal/event, memory, pause/resume, budget notifications, public action summaries.
3. Fee routing hanya jika didukung; aksi on-chain terbatas setelah audit dan persetujuan eksplisit.

## Batas proposal
Belum ada layanan pembayaran, top-up, AI calls, worker/cron, private-key custody, atau fee routing diaktifkan. User sebelumnya meminta fase konfigurasi tanpa integrasi AI; proposal ini tidak mengubah keputusan itu.
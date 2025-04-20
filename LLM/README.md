# Live Conversation API

Sistem Live Conversation sederhana menggunakan Google Gemini API yang terintegrasi dengan pemrosesan audio.

## Prasyarat

1. Python 3.10+ (diperlukan untuk fitur asyncio terbaru)
2. Google API Key (untuk Gemini API)
3. Package yang diperlukan:
   - google-genai
   - pyaudio
   - python-dotenv

## Instalasi

1. Pastikan Anda memiliki semua dependensi:
   ```
   pip install -r requirements.txt
   ```

2. Pastikan file `.env` Anda sudah berisi API Key Google yang valid:
   ```
   GOOGLE_API_KEY=YOUR_ACTUAL_API_KEY
   ```

## Cara Penggunaan

1. Jalankan aplikasi:
   ```
   python LLM/live_api.py
   ```

2. Gunakan sebagai berikut:
   - Ketik pesan pada prompt "pesan > " dan tekan Enter untuk mengirim pesan
   - Sistem akan secara otomatis merekam audio dari mikrofon
   - AI akan merespons dengan teks dan audio
   - Ketik 'q' untuk keluar dari aplikasi

## Struktur Kode

- `live_api.py`: Implementasi utama Live Conversation API
- `voice.py`: Modul pemrosesan audio untuk merekam dan memutar audio

## Catatan

- Pastikan mikrofon dan speaker Anda berfungsi dengan baik
- API ini menggunakan model Gemini 2.0 Flash Live, yang masih dalam tahap preview
- Voice yang digunakan adalah "Aoede" 
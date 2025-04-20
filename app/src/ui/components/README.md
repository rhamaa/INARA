# Struktur Komponen UI

Dokumen ini menjelaskan struktur komponen UI yang digunakan dalam aplikasi.

## Ringkasan

Komponen UI dalam aplikasi ini diorganisir dalam struktur modular untuk mempermudah pengembangan dan pemeliharaan. Setiap komponen memiliki tanggung jawab tertentu dan dapat digunakan kembali di berbagai bagian aplikasi.

## Struktur Folder

```
ui/
├── components/             # Folder untuk komponen UI yang dapat digunakan kembali
│   ├── theme.py            # Definisi warna dan gaya aplikasi
│   ├── datetime_panel.py   # Komponen untuk menampilkan tanggal dan waktu
│   ├── carousel_panel.py   # Komponen untuk rotasi pesan
│   ├── chat_input.py       # Komponen untuk input chat (RAG dan LLM)
│   └── ...
├── chat_box.py             # Re-export komponen (untuk backward compatibility)
└── md_panel.py             # Komponen untuk Markdown Viewer
```

## Komponen

### AppColors dan AppStyles (theme.py)

Menyediakan definisi warna dan gaya yang konsisten di seluruh aplikasi.

### DateTimePanel (datetime_panel.py)

Komponen untuk menampilkan tanggal dan waktu yang diperbarui secara periodik.

### CarouselPanel (carousel_panel.py)

Komponen untuk menampilkan pesan carousel yang berganti secara otomatis.

### RAGQueryPanel dan LLMCommandPanel (chat_input.py)

Komponen untuk input pengguna terkait dengan RAG dan pemrosesan LLM.

### MarkdownViewer (md_panel.py)

Komponen untuk menampilkan konten markdown dengan pemantauan perubahan file.

## Alur Data

```
          [Input User]
              │
              ▼
    ┌─────────────────────┐
    │      Chat Input     │  (LLMCommandPanel / RAGQueryPanel) 
    │ (ui/components/chat_input.py) │
    └──────────┬──────────┘
              │
              ▼
    ┌─────────────────────┐
    │    Chat Manager     │  Mengelola proses query
    │   (Function/chat.py)   │
    └──────────┬──────────┘
              │
              ▼
    ┌─────────────────────┐
    │     Simple RAG      │  Pencarian dan generasi konten
    │ (Function/tools/rag.py) │
    └──────────┬──────────┘
              │
              │ Langsung memperbarui
              │
              ▼
    ┌─────────────────────┐
    │   Markdown Panel    │  Menampilkan hasil ke pengguna
    │   (ui/md_panel.py)    │
    └─────────────────────┘
```

Dalam alur ini, semua komponen UI terhubung dalam satu rantai proses. RAG memiliki referensi langsung ke Markdown Panel dan memperbarui kontennya secara langsung saat query diproses, tanpa melalui callback.

## Cara Penggunaan

Untuk menggunakan komponen-komponen ini dalam file baru, Anda dapat mengimpornya langsung dari paket `ui.components`:

```python
from ui.components import AppColors, DateTimePanel, CarouselPanel
```

Untuk banyak file yang sudah ada, impor dari `ui.chat_box` tetap berfungsi berkat "re-export" yang sudah disediakan:

```python
from ui.chat_box import RAGQueryPanel, LLMCommandPanel
``` 
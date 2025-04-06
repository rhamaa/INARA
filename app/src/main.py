import flet as ft
import os
import threading
import time
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Handler untuk pemantauan perubahan file
class MarkdownFileHandler(FileSystemEventHandler):
    def __init__(self, markdown_component, md_file_path):
        self.markdown_component = markdown_component
        self.md_file_path = md_file_path
        self.page = markdown_component.page
        
    def on_modified(self, event):
        if event.src_path == self.md_file_path:
            # Baca file yang diperbarui
            try:
                with open(self.md_file_path, "r", encoding="utf-8") as md_file:
                    new_content = md_file.read()
                    
                # Update komponen markdown
                self.markdown_component.value = new_content
                self.page.update()
                print(f"[INFO] File markdown berhasil diperbarui: {time.strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"[ERROR] Gagal memperbarui markdown: {str(e)}")

def main(page: ft.Page):
    page.title = "Markdown Kiosk"
    page.padding = 10
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1000
    page.window_height = 700
    
    # Path ke file Markdown, relatif terhadap lokasi main.py
    md_file_path = os.path.join(os.path.dirname(__file__), "md", "main.md")
    md_file_path = os.path.abspath(md_file_path)  # Konversi ke path absolut
    
    # Baca konten awal dari file Markdown
    try:
        with open(md_file_path, "r", encoding="utf-8") as md_file:
            markdown_content = md_file.read()
    except Exception as e:
        markdown_content = f"# Error Membaca File Markdown\n\nTerjadi kesalahan saat membaca file: {str(e)}"
    
    # Fungsi untuk mengupdate waktu
    def update_time_date():
        while True:
            now = datetime.datetime.now()
            date_text.value = now.strftime("%d-%m-%Y")
            time_text.value = now.strftime("%H:%M:%S")
            page.update()
            time.sleep(1)
    
    # Membuat threading untuk update waktu
    time_thread = threading.Thread(target=update_time_date, daemon=True)
    
    # Fungsi untuk menambahkan teks ke markdown
    def add_text_to_markdown(e):
        if command_input.value:
            current_content = markdown_view.value
            new_content = current_content + "\n\n" + command_input.value
            
            # Update tampilan markdown
            markdown_view.value = new_content
            
            # Simpan ke file
            try:
                with open(md_file_path, "w", encoding="utf-8") as md_file:
                    md_file.write(new_content)
                print(f"[INFO] Konten berhasil disimpan ke file: {time.strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"[ERROR] Gagal menyimpan ke file: {str(e)}")
            
            # Reset input
            command_input.value = ""
            page.update()
    
    # Komponen markdown yang akan kita update (Canvas)
    markdown_view = ft.Markdown(
        value=markdown_content,
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        on_tap_link=lambda e: page.launch_url(e.data),
        expand=True,
    )
    
    # Markdown canvas dengan judul
    markdown_canvas = ft.Container(
        content=ft.Column([
            markdown_view
        ]),
        padding=10,
        expand=True,
        border=ft.border.all(2, ft.colors.BLACK),
        border_radius=10,
    )
    
    # Date dan Time widgets
    date_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    time_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    
    date_container = ft.Container(
        content=ft.Column([
            ft.Text("Date", size=18, weight=ft.FontWeight.BOLD),
            date_text
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=150,
        height=70,
        border=ft.border.all(2, ft.colors.BLACK),
        border_radius=10,
        padding=5,
        alignment=ft.alignment.center
    )
    
    time_container = ft.Container(
        content=ft.Column([
            ft.Text("Time", size=18, weight=ft.FontWeight.BOLD),
            time_text
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=100,
        height=70,
        border=ft.border.all(2, ft.colors.BLACK),
        border_radius=10,
        padding=5,
        alignment=ft.alignment.center
    )
    
    # Carousel Adds
    carousel_items = [
        "Item 1: Ini adalah item pertama",
        "Item 2: Informasi tentang markdown",
        "Item 3: Tips penggunaan aplikasi"
    ]
    
    current_carousel_index = 0
    
    carousel_text = ft.Text(
        carousel_items[current_carousel_index],
        size=16,
        text_align=ft.TextAlign.CENTER
    )
    
    # Fungsi untuk rotasi carousel
    def rotate_carousel():
        nonlocal current_carousel_index
        while True:
            time.sleep(5)  # Ganti setiap 5 detik
            current_carousel_index = (current_carousel_index + 1) % len(carousel_items)
            carousel_text.value = carousel_items[current_carousel_index]
            page.update()
    
    # Thread untuk carousel
    carousel_thread = threading.Thread(target=rotate_carousel, daemon=True)
    
    carousel_container = ft.Container(
        content=ft.Column([
            carousel_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=30),
        height=300,
        border=ft.border.all(2, ft.colors.BLACK),
        border_radius=10,
        padding=10,
        margin=ft.margin.only(top=10),
        alignment=ft.alignment.center
    )
    
    # Command input
    command_input = ft.TextField(
        label="Ketik teks untuk ditambahkan",
        hint_text="Tulis sesuatu...",
        multiline=True,
        min_lines=3,
        on_submit=add_text_to_markdown
    )
    
    command_container = ft.Container(
        content=ft.Column([
            ft.Text("Markdown Command", size=18, weight=ft.FontWeight.BOLD),
            command_input,
            ft.ElevatedButton("Tambahkan ke Canvas", 
                              on_click=add_text_to_markdown,
                              width=200,
                              style=ft.ButtonStyle(
                                  shape=ft.RoundedRectangleBorder(radius=10)
                              ))
        ]),
        height=200,
        border=ft.border.all(2, ft.colors.BLACK),
        border_radius=10,
        padding=10,
        margin=ft.margin.only(top=10)
    )
    
    # Right panel dengan date, time, carousel dan command
    right_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                date_container,
                time_container
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            carousel_container,
            command_container
        ]),
        width=280
    )
    
    # Main layout
    main_layout = ft.Row([
        markdown_canvas,
        right_panel
    ], expand=True)
    
    # Tambahkan ke halaman
    page.add(
        ft.Container(
            content=main_layout,
            border=ft.border.all(3, ft.colors.BLACK),
            border_radius=15,
            padding=10,
            expand=True
        )
    )
    
    # Mulai thread untuk waktu dan carousel
    time_thread.start()
    carousel_thread.start()
    
    # Siapkan pemantau file
    event_handler = MarkdownFileHandler(markdown_view, md_file_path)
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(md_file_path), recursive=False)
    observer.start()
    
    # Pastikan observer berhenti saat aplikasi ditutup
    def on_close(e):
        print("[INFO] Menghentikan pemantau file...")
        observer.stop()
        observer.join()
    
    page.on_close = on_close

ft.app(main)
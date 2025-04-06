import flet as ft
import os
import threading
import time
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
    page.title = "Markdown Viewer Responsif"
    page.scroll = "auto"
    
    # Path ke file Markdown, relatif terhadap lokasi main.py
    md_file_path = os.path.join(os.path.dirname(__file__), "md", "main.md")
    md_file_path = os.path.abspath(md_file_path)  # Konversi ke path absolut
    
    # Status bar untuk menunjukkan informasi
    status_text = ft.Text(
        value=f"Memantau file: {md_file_path}",
        color=ft.colors.BLUE_GREY_400,
        size=12,
        italic=True
    )
    
    # Baca konten awal dari file Markdown
    try:
        with open(md_file_path, "r", encoding="utf-8") as md_file:
            markdown_content = md_file.read()
    except Exception as e:
        markdown_content = f"# Error Membaca File Markdown\n\nTerjadi kesalahan saat membaca file: {str(e)}"
    
    # Komponen markdown yang akan kita update
    markdown_view = ft.Markdown(
        value=markdown_content,
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        on_tap_link=lambda e: page.launch_url(e.data),
    )
    
    # Tambahkan komponen ke halaman
    page.add(
        ft.Container(
            content=ft.Column([
                status_text,
                ft.Divider(),
                markdown_view
            ]),
            padding=10
        )
    )
    
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
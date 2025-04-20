"""
Modul UI untuk komponen-komponen markdown viewer
"""

import os
import time
import flet as ft
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

class MarkdownFileHandler(FileSystemEventHandler):
    """Handler untuk memantau perubahan pada file markdown."""
    
    def __init__(self, markdown_component: ft.Markdown, md_file_path: str):
        """
        Inisialisasi handler pemantau file.
        
        Args:
            markdown_component: Komponen markdown yang akan diperbarui
            md_file_path: Path ke file markdown yang dipantau
        """
        super().__init__()
        self.markdown_component = markdown_component
        self.md_file_path = md_file_path
        self.page = markdown_component.page
        
    def on_modified(self, event: FileModifiedEvent) -> None:
        """
        Dipanggil ketika file markdown dimodifikasi.
        
        Args:
            event: Event modifikasi file
        """
        if event.src_path == self.md_file_path:
            try:
                with open(self.md_file_path, "r", encoding="utf-8") as md_file:
                    new_content = md_file.read()
                    
                # Pastikan komponen dan page masih ada (tidak None)
                if self.markdown_component and self.page:
                    self.markdown_component.value = new_content
                    self.page.update()
                    print(f"[INFO] File markdown berhasil diperbarui: {time.strftime('%H:%M:%S')}")
                else:
                    print(f"[WARNING] Tidak dapat memperbarui UI: komponen atau page tidak tersedia")
                    
            except Exception as e:
                print(f"[ERROR] Gagal memperbarui markdown: {str(e)}")


class MarkdownViewer:
    """Komponen untuk menampilkan dan mengontrol markdown."""
    
    def __init__(self, page: ft.Page, md_file_path: str):
        """
        Inisialisasi viewer markdown.
        
        Args:
            page: Halaman Flet tempat viewer berada
            md_file_path: Path ke file markdown
        """
        self.page = page
        self.md_file_path = md_file_path
        
        # Baca konten file
        from Function.tools.md import FileManager
        self.content = FileManager.read_markdown_file(md_file_path)
        
        # Komponen markdown
        self.markdown_view = ft.Markdown(
            value=self.content,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: page.launch_url(e.data),
            expand=True,
        )
        
        # Container untuk markdown
        self.view = ft.Container(
            content=ft.Column([self.markdown_view]),
            padding=10,
            expand=True,
            bgcolor="white",
            border=ft.border.all(2, "#27548A"),
            border_radius=10,
        )
        
        # File handler untuk memantau perubahan
        self._file_handler = MarkdownFileHandler(self.markdown_view, md_file_path)
        self._observer = Observer()
        self._observer.schedule(
            self._file_handler, 
            os.path.dirname(md_file_path), 
            recursive=False
        )
    
    def update_content(self, content: str) -> None:
        """
        Update konten markdown langsung.
        
        Args:
            content: Konten baru
        """
        self.markdown_view.value = content
        
        # Simpan ke file
        from Function.tools.md import FileManager
        FileManager.write_markdown_file(self.md_file_path, content)
        
        self.page.update()
    
    def start_monitoring(self) -> None:
        """Memulai pemantauan perubahan file."""
        self._observer.start()
    
    def stop_monitoring(self) -> None:
        """Menghentikan pemantauan perubahan file."""
        self._observer.stop()
        self._observer.join()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplikasi Markdown Kiosk - Viewer dengan pemantauan perubahan otomatis
"""

from __future__ import annotations

import os
import threading
import time
import datetime
from typing import List, Optional, Callable, Any

import flet as ft
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


# =============================================================================
# KONSTANTA DAN KONFIGURASI
# =============================================================================

class AppConfig:
    """Konfigurasi aplikasi."""
    
    # Konfigurasi aplikasi
    TITLE = "Markdown Kiosk"
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    UPDATE_INTERVAL = 1  # Detik untuk update waktu
    CAROUSEL_INTERVAL = 5  # Detik untuk rotasi carousel


class AppColors:
    """Palet warna aplikasi."""
    
    BASE = "#F5EEDC"      # Warna dasar/background
    PRIMARY = "#27548A"   # Warna utama 
    SECONDARY = "#183B4E" # Warna sekunder
    ACCENT = "#DDA853"    # Warna aksen
    WHITE = "white"       # Warna putih


# =============================================================================
# KELAS UTILITY
# =============================================================================

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
                    
                self.markdown_component.value = new_content
                self.page.update()
                print(f"[INFO] File markdown berhasil diperbarui: {time.strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"[ERROR] Gagal memperbarui markdown: {str(e)}")


class FileManager:
    """Mengelola operasi file markdown."""
    
    @staticmethod
    def read_markdown_file(file_path: str) -> str:
        """
        Membaca konten dari file markdown.
        
        Args:
            file_path: Path ke file markdown
            
        Returns:
            Konten file markdown sebagai string
        """
        try:
            with open(file_path, "r", encoding="utf-8") as md_file:
                return md_file.read()
        except Exception as e:
            return f"# Error Membaca File Markdown\n\nTerjadi kesalahan saat membaca file: {str(e)}"
    
    @staticmethod
    def write_markdown_file(file_path: str, content: str) -> bool:
        """
        Menulis konten ke file markdown.
        
        Args:
            file_path: Path ke file markdown
            content: Konten yang akan ditulis
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            with open(file_path, "w", encoding="utf-8") as md_file:
                md_file.write(content)
            print(f"[INFO] Konten berhasil disimpan ke file: {time.strftime('%H:%M:%S')}")
            return True
        except Exception as e:
            print(f"[ERROR] Gagal menyimpan ke file: {str(e)}")
            return False


# =============================================================================
# KOMPONEN UI
# =============================================================================

class DateTimePanel:
    """Komponen panel tanggal dan waktu."""
    
    def __init__(self, page: ft.Page):
        """
        Inisialisasi panel tanggal dan waktu.
        
        Args:
            page: Halaman Flet tempat panel berada
        """
        self.page = page
        
        # Date dan Time text
        self.date_text = ft.Text(
            "", 
            size=16, 
            weight=ft.FontWeight.BOLD, 
            color=AppColors.BASE
        )
        
        self.time_text = ft.Text(
            "", 
            size=16, 
            weight=ft.FontWeight.BOLD, 
            color=AppColors.BASE
        )
        
        # Container untuk date
        self.date_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Date", 
                    size=18, 
                    weight=ft.FontWeight.BOLD, 
                    color=AppColors.BASE
                ),
                self.date_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=150,
            height=70,
            bgcolor=AppColors.PRIMARY,
            border=ft.border.all(2, AppColors.SECONDARY),
            border_radius=10,
            padding=5,
            alignment=ft.alignment.center
        )
        
        # Container untuk time
        self.time_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Time", 
                    size=18, 
                    weight=ft.FontWeight.BOLD, 
                    color=AppColors.BASE
                ),
                self.time_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=100,
            height=70,
            bgcolor=AppColors.PRIMARY,
            border=ft.border.all(2, AppColors.SECONDARY),
            border_radius=10,
            padding=5,
            alignment=ft.alignment.center
        )
        
        # Row untuk date dan time
        self.view = ft.Row(
            [self.date_container, self.time_container],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # Thread untuk update waktu
        self._thread = threading.Thread(
            target=self._update_time_date, 
            daemon=True
        )
    
    def _update_time_date(self) -> None:
        """Fungsi untuk mengupdate tanggal dan waktu secara periodik."""
        while True:
            now = datetime.datetime.now()
            self.date_text.value = now.strftime("%d-%m-%Y")
            self.time_text.value = now.strftime("%H:%M:%S")
            self.page.update()
            time.sleep(AppConfig.UPDATE_INTERVAL)
    
    def start(self) -> None:
        """Memulai thread update waktu."""
        self._thread.start()


class CarouselPanel:
    """Komponen panel carousel."""
    
    def __init__(self, page: ft.Page, items: List[str]):
        """
        Inisialisasi panel carousel.
        
        Args:
            page: Halaman Flet tempat panel berada
            items: Daftar item yang akan ditampilkan dalam carousel
        """
        self.page = page
        self.items = items
        self.current_index = 0
        
        # Text untuk carousel
        self.carousel_text = ft.Text(
            self.items[self.current_index],
            size=16,
            color=AppColors.PRIMARY,
            text_align=ft.TextAlign.CENTER
        )
        
        # Container untuk carousel
        self.view = ft.Container(
            content=ft.Column([
                self.carousel_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=30),
            height=300,
            bgcolor=AppColors.BASE,
            border=ft.border.all(2, AppColors.ACCENT),
            border_radius=10,
            padding=10,
            margin=ft.margin.only(top=10),
            alignment=ft.alignment.center
        )
        
        # Thread untuk rotasi carousel
        self._thread = threading.Thread(
            target=self._rotate_carousel, 
            daemon=True
        )
    
    def _rotate_carousel(self) -> None:
        """Fungsi untuk merotasi item carousel secara periodik."""
        while True:
            time.sleep(AppConfig.CAROUSEL_INTERVAL)
            self.current_index = (self.current_index + 1) % len(self.items)
            self.carousel_text.value = self.items[self.current_index]
            self.page.update()
    
    def start(self) -> None:
        """Memulai thread rotasi carousel."""
        self._thread.start()


class CommandPanel:
    """Komponen panel untuk input perintah markdown."""
    
    def __init__(
        self, 
        page: ft.Page, 
        md_view: ft.Markdown, 
        md_file_path: str
    ):
        """
        Inisialisasi panel perintah.
        
        Args:
            page: Halaman Flet tempat panel berada
            md_view: Komponen markdown yang akan diupdate
            md_file_path: Path ke file markdown
        """
        self.page = page
        self.md_view = md_view
        self.md_file_path = md_file_path
        
        # Input field
        self.command_input = ft.TextField(
            label="Ketik teks untuk ditambahkan",
            hint_text="Tulis sesuatu...",
            multiline=True,
            min_lines=3,
            on_submit=self._add_text_to_markdown,
            border_color=AppColors.PRIMARY,
            label_style=ft.TextStyle(color=AppColors.PRIMARY)
        )
        
        # Button untuk menambahkan text
        self.add_button = ft.ElevatedButton(
            "Tambahkan ke Canvas", 
            on_click=self._add_text_to_markdown,
            width=200,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                color=AppColors.BASE,
                bgcolor=AppColors.ACCENT
            )
        )
        
        # Container untuk command panel
        self.view = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Markdown Command", 
                    size=18, 
                    weight=ft.FontWeight.BOLD, 
                    color=AppColors.PRIMARY
                ),
                self.command_input,
                self.add_button
            ]),
            height=200,
            bgcolor=AppColors.BASE,
            border=ft.border.all(2, AppColors.PRIMARY),
            border_radius=10,
            padding=10,
            margin=ft.margin.only(top=10)
        )
    
    def _add_text_to_markdown(self, e: ft.ControlEvent) -> None:
        """
        Fungsi untuk menambahkan teks ke file markdown.
        
        Args:
            e: Event dari Flet
        """
        if self.command_input.value:
            current_content = self.md_view.value
            new_content = current_content + "\n\n" + self.command_input.value
            
            # Update tampilan markdown
            self.md_view.value = new_content
            
            # Simpan ke file
            if FileManager.write_markdown_file(self.md_file_path, new_content):
                # Reset input jika berhasil
                self.command_input.value = ""
                self.page.update()


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
            bgcolor=AppColors.WHITE,
            border=ft.border.all(2, AppColors.PRIMARY),
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
    
    def start_monitoring(self) -> None:
        """Memulai pemantauan perubahan file."""
        self._observer.start()
    
    def stop_monitoring(self) -> None:
        """Menghentikan pemantauan perubahan file."""
        self._observer.stop()
        self._observer.join()


# =============================================================================
# APLIKASI UTAMA
# =============================================================================

class MarkdownApp:
    """Kelas utama aplikasi Markdown Kiosk."""
    
    def __init__(self):
        """Inisialisasi aplikasi."""
        self.md_file_path = None
        self.components = {}
    
    def initialize(self, page: ft.Page) -> None:
        """
        Inisialisasi aplikasi.
        
        Args:
            page: Halaman Flet utama
        """
        # Setup halaman
        self._setup_page(page)
        
        # Setup file path
        self._setup_file_path()
        
        # Inisialisasi komponen
        self._init_components(page)
        
        # Setup layout
        self._setup_layout(page)
        
        # Setup event handler
        self._setup_event_handlers(page)
        
        # Mulai semua thread dan monitor
        self._start_components()
    
    def _setup_page(self, page: ft.Page) -> None:
        """
        Setup konfigurasi halaman.
        
        Args:
            page: Halaman Flet utama
        """
        page.title = AppConfig.TITLE
        page.padding = 10
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = AppConfig.WINDOW_WIDTH
        page.window_height = AppConfig.WINDOW_HEIGHT
        page.bgcolor = AppColors.BASE
    
    def _setup_file_path(self) -> None:
        """Setup path ke file markdown."""
        md_file_path = os.path.join(os.path.dirname(__file__), "md", "main.md")
        self.md_file_path = os.path.abspath(md_file_path)
    
    def _init_components(self, page: ft.Page) -> None:
        """
        Inisialisasi komponen UI.
        
        Args:
            page: Halaman Flet utama
        """
        # Komponen markdown viewer
        self.components["markdown_viewer"] = MarkdownViewer(page, self.md_file_path)
        
        # Komponen datetime
        self.components["datetime_panel"] = DateTimePanel(page)
        
        # Komponen carousel
        carousel_items = [
            "Item 1: Ini adalah item pertama",
            "Item 2: Informasi tentang markdown",
            "Item 3: Tips penggunaan aplikasi"
        ]
        self.components["carousel_panel"] = CarouselPanel(page, carousel_items)
        
        # Komponen command
        self.components["command_panel"] = CommandPanel(
            page, 
            self.components["markdown_viewer"].markdown_view, 
            self.md_file_path
        )
    
    def _setup_layout(self, page: ft.Page) -> None:
        """
        Setup layout halaman.
        
        Args:
            page: Halaman Flet utama
        """
        # Right panel (komponen kanan)
        right_panel = ft.Container(
            content=ft.Column([
                self.components["datetime_panel"].view,
                self.components["carousel_panel"].view,
                self.components["command_panel"].view
            ]),
            width=280
        )
        
        # Layout utama
        main_layout = ft.Row([
            self.components["markdown_viewer"].view,
            right_panel
        ], expand=True)
        
        # Tambahkan ke halaman
        page.add(
            ft.Container(
                content=main_layout,
                border=ft.border.all(3, AppColors.SECONDARY),
                border_radius=15,
                padding=10,
                expand=True
            )
        )
    
    def _setup_event_handlers(self, page: ft.Page) -> None:
        """
        Setup event handler.
        
        Args:
            page: Halaman Flet utama
        """
        def on_close(e: ft.ControlEvent) -> None:
            """Handler untuk event penutupan aplikasi."""
            print("[INFO] Menghentikan pemantau file...")
            self.components["markdown_viewer"].stop_monitoring()
        
        page.on_close = on_close
    
    def _start_components(self) -> None:
        """Mulai semua komponen yang memerlukan thread atau observer."""
        self.components["datetime_panel"].start()
        self.components["carousel_panel"].start()
        self.components["markdown_viewer"].start_monitoring()
    
    def run(self) -> None:
        """Jalankan aplikasi."""
        ft.app(target=self.initialize)


# Jalankan aplikasi jika file dieksekusi langsung
if __name__ == "__main__":
    app = MarkdownApp()
    app.run()
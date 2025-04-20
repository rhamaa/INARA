"""
Komponen UI untuk menampilkan carousel (rotasi pesan)
"""

import time
import threading
import flet as ft
from typing import List

class AppColors:
    """Palet warna aplikasi."""
    
    BASE = "#F5EEDC"      # Warna dasar/background
    PRIMARY = "#27548A"   # Warna utama 
    SECONDARY = "#183B4E" # Warna sekunder
    ACCENT = "#DDA853"    # Warna aksen
    WHITE = "white"       # Warna putih
    GREEN = "#4CAF50"     # Warna hijau
    RED = "#F44336"       # Warna merah

class CarouselPanel:
    """Komponen panel carousel."""
    
    def __init__(self, page: ft.Page, items: List[str], carousel_interval: int = 5):
        """
        Inisialisasi panel carousel.
        
        Args:
            page: Halaman Flet tempat panel berada
            items: Daftar item yang akan ditampilkan dalam carousel
            carousel_interval: Interval rotasi dalam detik
        """
        self.page = page
        self.items = items
        self.current_index = 0
        self.carousel_interval = carousel_interval
        
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
            height=200,
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
            time.sleep(self.carousel_interval)
            self.current_index = (self.current_index + 1) % len(self.items)
            self.carousel_text.value = self.items[self.current_index]
            self.page.update()
    
    def start(self) -> None:
        """Memulai thread rotasi carousel."""
        self._thread.start() 
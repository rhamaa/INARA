"""
Komponen UI untuk menampilkan tanggal dan waktu
"""

import time
import threading
import flet as ft
from typing import Dict

class AppColors:
    """Palet warna aplikasi."""
    
    BASE = "#F5EEDC"      # Warna dasar/background
    PRIMARY = "#27548A"   # Warna utama 
    SECONDARY = "#183B4E" # Warna sekunder
    ACCENT = "#DDA853"    # Warna aksen
    WHITE = "white"       # Warna putih
    GREEN = "#4CAF50"     # Warna hijau
    RED = "#F44336"       # Warna merah

class DateTimePanel:
    """Komponen panel tanggal dan waktu."""
    
    def __init__(self, page: ft.Page, update_interval: int = 1):
        """
        Inisialisasi panel tanggal dan waktu.
        
        Args:
            page: Halaman Flet tempat panel berada
            update_interval: Interval update dalam detik
        """
        self.page = page
        self.update_interval = update_interval
        
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
        import datetime
        
        while True:
            now = datetime.datetime.now()
            self.date_text.value = now.strftime("%d-%m-%Y")
            self.time_text.value = now.strftime("%H:%M:%S")
            self.page.update()
            time.sleep(self.update_interval)
    
    def start(self) -> None:
        """Memulai thread update waktu."""
        self._thread.start() 
"""
Modul UI untuk komponen-komponen chat dan panel interaksi AI
"""

import flet as ft
import threading
import time
from typing import Callable, List

class AppColors:
    """Palet warna aplikasi untuk komponen chat."""
    
    BASE = "#F5EEDC"      # Warna dasar/background
    PRIMARY = "#27548A"   # Warna utama 
    SECONDARY = "#183B4E" # Warna sekunder
    ACCENT = "#DDA853"    # Warna aksen
    WHITE = "white"       # Warna putih
    GREEN = "#4CAF50"     # Warna hijau
    RED = "#F44336"       # Warna merah

class RAGQueryPanel:
    """Panel untuk query RAG."""
    
    def __init__(
        self, 
        page: ft.Page, 
        on_query: Callable[[str], None],
        status_callback: Callable[[str], None] = None
    ):
        """
        Inisialisasi panel RAG query.
        
        Args:
            page: Halaman Flet
            on_query: Callback untuk query baru
            status_callback: Callback untuk status
        """
        self.page = page
        self.on_query = on_query
        self.status_text = ft.Text(
            value="RAG siap untuk pertanyaan",
            color=AppColors.PRIMARY,
            size=14,
            italic=True
        )
        
        # Status callback
        def update_status(message: str):
            self.status_text.value = message
            self.page.update()
        
        self.status_callback = update_status if status_callback is None else status_callback
        
        # Query input
        self.query_input = ft.TextField(
            label="Ketik pertanyaan Anda",
            hint_text="Contoh: Siapa rektor UKRI?",
            multiline=True,
            min_lines=2,
            max_lines=4,
            on_submit=self._on_submit_query,
            border_color=AppColors.PRIMARY,
            label_style=ft.TextStyle(color=AppColors.PRIMARY)
        )
        
        # Button untuk mengirim query
        self.submit_button = ft.ElevatedButton(
            "Tanyakan", 
            on_click=self._on_submit_query,
            icon=ft.icons.SEARCH,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                color=AppColors.BASE,
                bgcolor=AppColors.ACCENT
            )
        )
        
        # Container untuk RAG panel
        self.view = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Tanya AI", 
                    size=18, 
                    weight=ft.FontWeight.BOLD, 
                    color=AppColors.PRIMARY
                ),
                self.query_input,
                ft.Row([
                    self.submit_button,
                    self.status_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            height=180,
            bgcolor=AppColors.BASE,
            border=ft.border.all(2, AppColors.PRIMARY),
            border_radius=10,
            padding=10,
            margin=ft.margin.only(top=10)
        )
    
    def _on_submit_query(self, e: ft.ControlEvent) -> None:
        """
        Handler untuk submit query.
        
        Args:
            e: Event dari Flet
        """
        if self.query_input.value:
            query = self.query_input.value
            self.status_callback(f"Memproses: {query}")
            self.on_query(query)
            self.query_input.value = ""
            self.page.update()


class LLMCommandPanel:
    """Komponen panel untuk input perintah LLM."""
    
    def __init__(
        self, 
        page: ft.Page, 
        rag_handler: Callable[[str], None]
    ):
        """
        Inisialisasi panel perintah LLM.
        
        Args:
            page: Halaman Flet tempat panel berada
            rag_handler: Handler untuk memproses query RAG
        """
        self.page = page
        self.rag_handler = rag_handler
        
        # Input field
        self.command_input = ft.TextField(
            label="Tanyakan ke AI",
            hint_text="Ketik pertanyaan Anda tentang UKRI...",
            multiline=True,
            min_lines=3,
            on_submit=self._process_llm_query,
            border_color=AppColors.PRIMARY,
            label_style=ft.TextStyle(color=AppColors.PRIMARY)
        )
        
        # Button untuk submit query
        self.submit_button = ft.ElevatedButton(
            "Proses dengan AI", 
            on_click=self._process_llm_query,
            width=200,
            icon=ft.icons.PSYCHOLOGY_ALT,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                color=AppColors.BASE,
                bgcolor=AppColors.ACCENT
            )
        )
        
        # Status text
        self.status_text = ft.Text(
            value="Siap menerima pertanyaan",
            color=AppColors.PRIMARY,
            size=12,
            italic=True
        )
        
        # Container untuk command panel
        self.view = ft.Container(
            content=ft.Column([
                ft.Text(
                    "LLM Command", 
                    size=18, 
                    weight=ft.FontWeight.BOLD, 
                    color=AppColors.PRIMARY
                ),
                self.command_input,
                ft.Row([
                    self.submit_button,
                    self.status_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            height=200,
            bgcolor=AppColors.BASE,
            border=ft.border.all(2, AppColors.PRIMARY),
            border_radius=10,
            padding=10,
            margin=ft.margin.only(top=10)
        )
    
    def _process_llm_query(self, e: ft.ControlEvent) -> None:
        """
        Proses query LLM.
        
        Args:
            e: Event dari Flet
        """
        if self.command_input.value:
            query = self.command_input.value
            
            # Update status
            self.status_text.value = f"Memproses: {query}"
            self.page.update()
            
            # Kirim query ke RAG handler
            self.rag_handler(query)
            
            # Reset input field dan update status
            self.command_input.value = ""
            self.status_text.value = "Query berhasil diproses"
            self.page.update()


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

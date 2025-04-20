#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplikasi Markdown Kiosk - Viewer dengan pemantauan perubahan otomatis dan RAG
"""

from __future__ import annotations

import os
import sys
from typing import Dict

import flet as ft

# Import modul-modul UI
from ui.components import (
    AppColors, AppStyles, 
    RAGQueryPanel, LLMCommandPanel, 
    CarouselPanel, DateTimePanel,
    MarkdownViewer
)

# Import modul-modul backend
from Function.tools.rag import SimpleRAG, RAG_AVAILABLE
from Function.tools.md import FileManager
from Function.chat import ChatManager

# Import untuk dotenv
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
except ImportError:
    print("dotenv tidak tersedia, API key harus diatur secara manual")


# =============================================================================
# KONSTANTA DAN KONFIGURASI
# =============================================================================

class AppConfig:
    """Konfigurasi aplikasi."""
    
    # Konfigurasi aplikasi
    TITLE = "Markdown Kiosk dengan RAG"
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    UPDATE_INTERVAL = 1  # Detik untuk update waktu
    CAROUSEL_INTERVAL = 5  # Detik untuk rotasi carousel


# =============================================================================
# APLIKASI UTAMA
# =============================================================================

class MarkdownApp:
    """Kelas utama aplikasi Markdown Kiosk."""
    
    def __init__(self):
        """Inisialisasi aplikasi."""
        self.md_file_path = None
        self.components = {}
        self.rag = None
        self.chat_manager = None
    
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
        
        # Inisialisasi RAG jika tersedia
        self._init_rag(page)
        
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
        
        # Pastikan direktori md ada
        os.makedirs(os.path.dirname(self.md_file_path), exist_ok=True)
        
        # Buat file markdown jika belum ada
        if not os.path.exists(self.md_file_path):
            with open(self.md_file_path, "w", encoding="utf-8") as f:
                f.write("# Selamat Datang\n\nIni adalah aplikasi Markdown Kiosk dengan RAG.")
    
    def _init_components(self, page: ft.Page) -> None:
        """
        Inisialisasi komponen UI.
        
        Args:
            page: Halaman Flet utama
        """
        # Komponen markdown viewer
        self.components["markdown_viewer"] = MarkdownViewer(page, self.md_file_path)
        
        # Komponen datetime
        self.components["datetime_panel"] = DateTimePanel(page, update_interval=AppConfig.UPDATE_INTERVAL)
        
        # Komponen carousel
        carousel_items = [
            "RAG terintegrasi dengan Markdown Viewer",
            "Tanyakan sesuatu tentang UKRI untuk memulai",
            "Jawaban akan ditampilkan dalam format Markdown"
        ]
        self.components["carousel_panel"] = CarouselPanel(
            page, 
            carousel_items, 
            carousel_interval=AppConfig.CAROUSEL_INTERVAL
        )
    
    def _init_rag(self, page: ft.Page) -> None:
        """
        Inisialisasi RAG jika tersedia.
        
        Args:
            page: Halaman Flet utama
        """
        if RAG_AVAILABLE:
            try:
                # Hubungkan langsung dengan MarkdownViewer
                self.rag = SimpleRAG(
                    markdown_viewer=self.components["markdown_viewer"]
                )
                
                # Buat status callback untuk UI panel
                def status_callback(message: str):
                    if "rag_panel" in self.components:
                        self.components["rag_panel"].status_callback(message)
                
                # Inisialisasi ChatManager
                self.chat_manager = ChatManager(
                    rag_instance=self.rag,
                    status_callback=status_callback,
                    # Tidak perlu result_callback lagi karena RAG langsung update markdown
                )
                
                # Handler untuk query dari UI
                def on_rag_query(query: str):
                    self.chat_manager.process_query(query)
                
                # Tambahkan komponen RAG query
                self.components["rag_panel"] = RAGQueryPanel(
                    page,
                    on_query=on_rag_query
                )
                
                # Tambahkan panel LLM Command
                self.components["llm_command"] = LLMCommandPanel(
                    page,
                    rag_handler=on_rag_query
                )
                
                # Tambahkan tanda sukses di carousel
                carousel_items = [
                    "✅ RAG berhasil dimuat dan siap digunakan",
                    "Tanyakan sesuatu tentang UKRI untuk memulai",
                    "Gunakan panel LLM Command di bawah"
                ]
                self.components["carousel_panel"].items = carousel_items
                
                # Update status di LLM Command
                self.components["llm_command"].status_text.value = "RAG siap digunakan"
                self.components["llm_command"].status_text.color = AppColors.GREEN
                
            except Exception as e:
                print(f"Error initializing RAG: {str(e)}")
                
                # Tambahkan RAG Panel for display errors
                def on_rag_query(query: str):
                    pass  # No-op karena RAG gagal dimuat
                
                self.components["rag_panel"] = RAGQueryPanel(
                    page,
                    on_query=on_rag_query
                )
                
                self.components["llm_command"] = LLMCommandPanel(
                    page,
                    rag_handler=on_rag_query
                )
                
                self.components["rag_panel"].status_text.value = f"Error: {str(e)}"
                self.components["rag_panel"].status_text.color = AppColors.RED
                
                # Update status di LLM Command juga
                self.components["llm_command"].status_text.value = f"Error: {str(e)}"
                self.components["llm_command"].status_text.color = AppColors.RED
                
                # Tambahkan pesan error di carousel
                carousel_items = [
                    "❌ RAG gagal dimuat: " + str(e),
                    "Pastikan file vector store tersedia",
                    "Dan API key telah dikonfigurasi dengan benar"
                ]
                self.components["carousel_panel"].items = carousel_items
        else:
            # Tambahkan komponen UI meskipun RAG tidak tersedia
            def on_rag_query(query: str):
                pass  # No-op karena RAG tidak tersedia
            
            self.components["rag_panel"] = RAGQueryPanel(
                page,
                on_query=on_rag_query
            )
            
            self.components["llm_command"] = LLMCommandPanel(
                page,
                rag_handler=on_rag_query
            )
            
            # Update status
            self.components["rag_panel"].status_text.value = "Dependensi RAG tidak tersedia"
            self.components["rag_panel"].status_text.color = AppColors.RED
            
            # Update status di LLM Command juga
            self.components["llm_command"].status_text.value = "Dependensi RAG tidak tersedia"
            self.components["llm_command"].status_text.color = AppColors.RED
    
    def _setup_layout(self, page: ft.Page) -> None:
        """
        Setup layout halaman.
        
        Args:
            page: Halaman Flet utama
        """
        # Right panel (komponen kanan)
        right_column = [
            self.components["datetime_panel"].view,
            self.components["carousel_panel"].view
        ]
        
        # Tambahkan LLM command panel
        if "llm_command" in self.components:
            right_column.append(self.components["llm_command"].view)
        
        right_panel = ft.Container(
            content=ft.Column(right_column),
            width=320
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
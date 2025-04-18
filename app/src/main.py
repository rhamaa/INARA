#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplikasi Markdown Kiosk - Viewer dengan pemantauan perubahan otomatis dan RAG
"""

from __future__ import annotations

import os
import threading
import time
import datetime
import json
import pickle
import faiss
import numpy as np
import re
import sys
from typing import List, Dict, Optional, Callable, Any, Tuple

import flet as ft
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

# Import untuk RAG
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


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
    
    # Konfigurasi RAG
    VECTOR_STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "LLM", "data", "vector_store")
    EMBEDDING_MODEL = "models/text-embedding-004"
    GENERATION_MODEL = "gemini-2.0-flash"


class AppColors:
    """Palet warna aplikasi."""
    
    BASE = "#F5EEDC"      # Warna dasar/background
    PRIMARY = "#27548A"   # Warna utama 
    SECONDARY = "#183B4E" # Warna sekunder
    ACCENT = "#DDA853"    # Warna aksen
    WHITE = "white"       # Warna putih
    GREEN = "#4CAF50"     # Warna hijau
    RED = "#F44336"       # Warna merah


# =============================================================================
# KELAS RAG
# =============================================================================

class SimpleRAG:
    """Kelas untuk menangani RAG (Retrieval Augmented Generation)."""
    
    def __init__(self, vector_store_path: str = AppConfig.VECTOR_STORE_PATH, status_callback: Callable = None):
        """
        Inisialisasi SimpleRAG.
        
        Args:
            vector_store_path: Path ke vector store
            status_callback: Callback untuk memperbarui status
        """
        if not RAG_AVAILABLE:
            raise ImportError("Dependensi RAG tidak tersedia. Pastikan google-generativeai dan dotenv terinstal.")
        
        self.vector_store_path = vector_store_path
        self.embedding_model = AppConfig.EMBEDDING_MODEL
        self.generation_model = AppConfig.GENERATION_MODEL
        self.status_callback = status_callback
        
        # Konfigurasi API key
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API key tidak ditemukan. Set GOOGLE_API_KEY di file .env")
        
        genai.configure(api_key=self.api_key)
        
        # Load vector store
        self._update_status("Memuat vector store...")
        self.load_vector_store()
        
        # Initialize generation model
        self._update_status("Menginisialisasi model...")
        self.model = genai.GenerativeModel(
            model_name=self.generation_model,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        self._update_status("RAG siap digunakan")
    
    def _update_status(self, message: str):
        """
        Update status melalui callback.
        
        Args:
            message: Pesan status
        """
        if self.status_callback:
            self.status_callback(message)
        print(f"[RAG] {message}")
    
    def load_vector_store(self):
        """Load the vector store"""
        if not os.path.exists(f"{self.vector_store_path}.index"):
            raise FileNotFoundError(f"Vector store not found at {self.vector_store_path}.index")
        
        if not os.path.exists(f"{self.vector_store_path}.pkl"):
            raise FileNotFoundError(f"Vector store data not found at {self.vector_store_path}.pkl")
        
        # Load the index
        self.index = faiss.read_index(f"{self.vector_store_path}.index")
        
        # Load the documents
        with open(f"{self.vector_store_path}.pkl", "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.chunks_info = data["chunks_info"]
        
        self._update_status(f"Vector store dimuat: {len(self.chunks_info)} chunks dari {len(self.documents)} dokumen")
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the vector store and return the top k relevant chunks.
        
        Args:
            query: Query pencarian
            top_k: Jumlah hasil teratas yang dikembalikan
            
        Returns:
            Daftar chunk relevan
        """
        self._update_status(f"Mencari dokumen untuk: {query}")
        
        # Create embedding for the query
        query_embedding = genai.embed_content(
            model=self.embedding_model,
            content=query,
            task_type="retrieval_query"
        )
        
        # Convert to numpy array
        query_vector = np.array([query_embedding["embedding"]]).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_vector, top_k)
        
        # Gather results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # -1 means no result
                chunk_info = self.chunks_info[idx]
                results.append({
                    "id": chunk_info["doc_id"],
                    "chunk_idx": chunk_info["chunk_idx"],
                    "text": chunk_info["text"],
                    "score": float(distances[0][i])
                })
        
        self._update_status(f"Ditemukan {len(results)} dokumen relevan")
        return results
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a response based on the query and retrieved chunks.
        
        Args:
            query: Query pengguna
            context_chunks: Chunk konteks yang ditemukan
            
        Returns:
            Respons yang dihasilkan
        """
        self._update_status("Menghasilkan respons...")
        
        # Prepare context from chunks
        context = ""
        for i, chunk in enumerate(context_chunks):
            context += f"\nChunk {i+1} (dari {chunk['id']}):\n{chunk['text']}\n"
        
        # Prepare prompt
        prompt = f"""
        Berdasarkan informasi berikut, jawablah pertanyaan pengguna.
        Jika jawabannya tidak ada dalam informasi yang diberikan, katakan bahwa kamu tidak memiliki informasi tersebut.
        
        Informasi:
        {context}
        
        Pertanyaan pengguna: {query}
        
        Jawaban (dalam format Markdown):
        """
        
        # Generate response
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Format untuk markdown yang baik
            response_text = f"# Jawaban untuk: {query}\n\n{response_text}\n\n## Sumber Informasi\n\n"
            
            # Tambahkan sumber informasi
            for i, chunk in enumerate(context_chunks):
                doc_id = chunk['id']
                response_text += f"- {doc_id}\n"
            
            self._update_status("Respons berhasil dihasilkan")
            return response_text
                
        except Exception as e:
            error_msg = f"Error saat menghasilkan respons: {str(e)}"
            self._update_status(error_msg)
            return f"# Error\n\n{error_msg}"
    
    def process_query(self, query: str) -> str:
        """
        Proses query dari awal hingga akhir.
        
        Args:
            query: Query pengguna
            
        Returns:
            Respons yang dihasilkan
        """
        try:
            # Retrieve relevant chunks
            results = self.search_documents(query)
            
            if not results:
                return f"# Tidak ada informasi\n\nMaaf, saya tidak menemukan informasi yang relevan untuk pertanyaan: {query}"
            
            # Generate response
            response = self.generate_response(query, results)
            return response
            
        except Exception as e:
            return f"# Error\n\nTerjadi kesalahan saat memproses query: {str(e)}"


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
                    
                # Pastikan komponen dan page masih ada (tidak None)
                if self.markdown_component and self.page:
                    self.markdown_component.value = new_content
                    self.page.update()
                    print(f"[INFO] File markdown berhasil diperbarui: {time.strftime('%H:%M:%S')}")
                else:
                    print(f"[WARNING] Tidak dapat memperbarui UI: komponen atau page tidak tersedia")
                    
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
            # Pastikan direktori ada
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
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
            time.sleep(AppConfig.CAROUSEL_INTERVAL)
            self.current_index = (self.current_index + 1) % len(self.items)
            self.carousel_text.value = self.items[self.current_index]
            self.page.update()
    
    def start(self) -> None:
        """Memulai thread rotasi carousel."""
        self._thread.start()


class RAGQueryPanel:
    """Panel untuk query RAG."""
    
    def __init__(
        self, 
        page: ft.Page, 
        on_query: Callable[[str], None],
        status_callback: Callable[[str], None]
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
    
    def update_content(self, content: str) -> None:
        """
        Update konten markdown langsung.
        
        Args:
            content: Konten baru
        """
        self.markdown_view.value = content
        FileManager.write_markdown_file(self.md_file_path, content)
        self.page.update()
    
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
        self.rag = None
    
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
            "RAG terintegrasi dengan Markdown Viewer",
            "Tanyakan sesuatu tentang UKRI untuk memulai",
            "Jawaban akan ditampilkan dalam format Markdown"
        ]
        self.components["carousel_panel"] = CarouselPanel(page, carousel_items)
    
    def _init_rag(self, page: ft.Page) -> None:
        """
        Inisialisasi RAG jika tersedia.
        
        Args:
            page: Halaman Flet utama
        """
        # Handler untuk query RAG
        def on_rag_query(query: str):
            if self.rag:
                # Proses query dan dapatkan respons
                response = self.rag.process_query(query)
                
                # Update markdown dengan respons
                self.components["markdown_viewer"].update_content(response)
        
        # Tambahkan komponen RAG query
        self.components["rag_panel"] = RAGQueryPanel(
            page,
            on_query=on_rag_query,
            status_callback=None  # Akan diperbarui nanti
        )
        
        # Tambahkan panel LLM Command
        self.components["llm_command"] = LLMCommandPanel(
            page,
            rag_handler=on_rag_query
        )
        
        # Coba inisialisasi RAG
        if RAG_AVAILABLE:
            try:
                self.rag = SimpleRAG(
                    status_callback=self.components["rag_panel"].status_callback
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
        
        # Tambahkan panel RAG jika sudah dibuat (opsional)
        #if "rag_panel" in self.components:
        #    right_column.append(self.components["rag_panel"].view)
        
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
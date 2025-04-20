"""
Modul backend untuk menangani fungsi AI dan chat - tidak berisi komponen UI
"""

from typing import Callable, Optional
import os

# Import untuk backend RAG
from Function.tools.rag import SimpleRAG
from Function.tools.md import FileManager

class ChatManager:
    """Kelas untuk mengelola logic chat dan LLM tanpa UI."""
    
    def __init__(
        self, 
        rag_instance: SimpleRAG,
        status_callback: Optional[Callable[[str], None]] = None,
        result_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Inisialisasi Chat Manager.
        
        Args:
            rag_instance: Instance RAG yang sudah dibuat
            status_callback: Callback untuk memperbarui status proses
            result_callback: Callback untuk menerima hasil respons
        """
        self.rag = rag_instance
        self.status_callback = status_callback
        self.result_callback = result_callback
    
    def process_query(self, query: str) -> str:
        """
        Memproses query pengguna dan mendapatkan respons.
        
        Args:
            query: Query dari pengguna
            
        Returns:
            Respons dari AI
        """
        try:
            # Update status jika callback tersedia
            if self.status_callback:
                self.status_callback(f"Memproses query: {query}")
            
            # Gunakan RAG untuk memproses query
            response = self.rag.process_query(query)
            
            # Panggil callback hasil jika tersedia
            if self.result_callback:
                self.result_callback(response)
            
            return response
        except Exception as e:
            error_message = f"Error saat memproses query: {str(e)}"
            if self.status_callback:
                self.status_callback(error_message)
            return f"# Error\n\n{error_message}"
    
    def save_result_to_markdown(self, content: str, file_path: str) -> bool:
        """
        Menyimpan hasil respons ke file markdown.
        
        Args:
            content: Konten respons untuk disimpan
            file_path: Path file target
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            return FileManager.write_markdown_file(file_path, content)
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Error saat menyimpan hasil: {str(e)}")
            return False

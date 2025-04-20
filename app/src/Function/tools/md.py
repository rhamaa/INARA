"""
Modul untuk menangani operasi file markdown.
"""

import os
import time

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

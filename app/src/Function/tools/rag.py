"""
RAG (Retrieval Augmented Generation) - Modul untuk menangani retrieval dan generasi
"""

import os
import pickle
import faiss
import numpy as np
from typing import List, Dict, Optional, Callable, Any, Tuple

# Import untuk RAG
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

class AppConfig:
    """Konfigurasi aplikasi untuk RAG."""
    
    # Konfigurasi RAG
    VECTOR_STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "vector_store")
    EMBEDDING_MODEL = "models/text-embedding-004"
    GENERATION_MODEL = "gemini-2.0-flash"

class SimpleRAG:
    """Kelas untuk menangani RAG (Retrieval Augmented Generation)."""
    
    def __init__(self, vector_store_path: str = AppConfig.VECTOR_STORE_PATH, status_callback: Callable = None, markdown_viewer = None):
        """
        Inisialisasi SimpleRAG.
        
        Args:
            vector_store_path: Path ke vector store
            status_callback: Callback untuk memperbarui status
            markdown_viewer: Instance MarkdownViewer untuk diupdate
        """
        if not RAG_AVAILABLE:
            raise ImportError("Dependensi RAG tidak tersedia. Pastikan google-generativeai dan dotenv terinstal.")
        
        self.vector_store_path = vector_store_path
        self.embedding_model = AppConfig.EMBEDDING_MODEL
        self.generation_model = AppConfig.GENERATION_MODEL
        self.status_callback = status_callback
        self.markdown_viewer = markdown_viewer
        
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
    
    def set_markdown_viewer(self, markdown_viewer):
        """
        Set instance MarkdownViewer yang akan digunakan.
        
        Args:
            markdown_viewer: Instance MarkdownViewer
        """
        self.markdown_viewer = markdown_viewer
    
    def update_markdown_panel(self, content: str):
        """
        Update konten pada markdown panel.
        
        Args:
            content: Konten markdown yang akan ditampilkan
        """
        if self.markdown_viewer:
            self.markdown_viewer.update_content(content)
            self._update_status(f"Markdown panel diperbarui dengan konten baru")
        else:
            self._update_status("Tidak dapat memperbarui markdown panel: MarkdownViewer tidak tersedia")
    
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
                response = f"# Tidak ada informasi\n\nMaaf, saya tidak menemukan informasi yang relevan untuk pertanyaan: {query}"
            else:
                # Generate response
                response = self.generate_response(query, results)
            
            # Update markdown panel langsung
            self.update_markdown_panel(response)
            
            return response
            
        except Exception as e:
            error_msg = f"# Error\n\nTerjadi kesalahan saat memproses query: {str(e)}"
            
            # Update markdown panel dengan error
            if self.markdown_viewer:
                self.update_markdown_panel(error_msg)
                
            return error_msg

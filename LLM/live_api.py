"""
Live Conversation API Sederhana - Terintegrasi dengan voice.py

Panduan penggunaan:
1. Pastikan Anda telah menginstal semua dependensi:
   pip install google-genai pyaudio

2. Jalankan dengan perintah:
   python LLM/live_api.py
"""

import os
import asyncio
import sys
from voice import AudioProcessor

from google import genai
from google.genai import types

# Konfigurasi API Gemini
MODEL = "models/gemini-2.0-flash-live-001"

# Dapatkan API key dari variabel lingkungan
API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    print("Error: GOOGLE_API_KEY tidak ditemukan dalam variabel lingkungan.")
    print("Pastikan Anda telah mengatur API key di file .env")
    sys.exit(1)

# Inisialisasi client Gemini
client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=API_KEY,
)

# Konfigurasi untuk Live Connect
CONFIG = types.LiveConnectConfig(
    response_modalities=["audio"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
)

class LiveConversation:
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.audio_in_queue = None
        self.audio_out_queue = None
        self.session = None

    async def send_text(self):
        """Mengirim pesan teks ke AI dan menandai akhir giliran"""
        while True:
            text = await asyncio.to_thread(input, "pesan > ")
            if text.lower() == "q":
                break
            await self.session.send(input=text, end_of_turn=True)

    async def receive_response(self):
        """Menerima respons dari AI"""
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                    continue
                if text := response.text:
                    print(text, end="")

            # Bersihkan antrian audio jika ada interupsi
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def run(self):
        try:
            print("Memulai percakapan live dengan Gemini 2.0")
            print("Ketik 'q' untuk keluar")
            
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                
                # Inisialisasi antrian
                self.audio_in_queue = asyncio.Queue()
                self.audio_out_queue = asyncio.Queue()
                
                # Siapkan audio
                mic_stream = await self.audio_processor.setup_microphone()
                speaker_stream = await self.audio_processor.setup_speaker()
                
                # Buat task
                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.audio_processor.record_audio(mic_stream, self.audio_out_queue))
                tg.create_task(self.receive_response())
                tg.create_task(self.audio_processor.play_audio(speaker_stream, self.audio_in_queue))
                
                # Task untuk mengirim audio ke AI
                async def send_audio():
                    while True:
                        audio_data = await self.audio_out_queue.get()
                        await self.session.send(input=audio_data)
                
                tg.create_task(send_audio())
                
                # Tunggu sampai pengguna keluar
                await send_text_task
                raise asyncio.CancelledError("Pengguna meminta keluar")

        except asyncio.CancelledError:
            print("\nMengakhiri percakapan")
        finally:
            self.audio_processor.cleanup()

if __name__ == "__main__":
    convo = LiveConversation()
    asyncio.run(convo.run()) 
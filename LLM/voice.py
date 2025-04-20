import pyaudio
import asyncio

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

class AudioProcessor:
    def __init__(self):
        self.pya = pyaudio.PyAudio()
        
    async def setup_microphone(self):
        """Menyiapkan mikrofon untuk merekam audio"""
        mic_info = self.pya.get_default_input_device_info()
        audio_stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        return audio_stream
    
    async def setup_speaker(self):
        """Menyiapkan speaker untuk memutar audio"""
        speaker_stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        return speaker_stream
    
    async def record_audio(self, audio_stream, queue):
        """Merekam audio dari mikrofon dan mengirimkannya ke queue"""
        kwargs = {"exception_on_overflow": False}
        
        while True:
            data = await asyncio.to_thread(audio_stream.read, CHUNK_SIZE, **kwargs)
            await queue.put({"data": data, "mime_type": "audio/pcm"})
    
    async def play_audio(self, speaker_stream, queue):
        """Memutar audio yang diterima dari AI"""
        while True:
            bytestream = await queue.get()
            await asyncio.to_thread(speaker_stream.write, bytestream)
    
    def cleanup(self):
        """Membersihkan sumber daya audio"""
        self.pya.terminate()

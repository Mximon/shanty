import numpy as np
from pathlib import Path
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from openai import OpenAI
import time
import datetime
import wave
import shutil


class LRL_v4_MaritimeEngine:
    def __init__(self, config, formatter):
        print("--- Initializing Engine LRL V4 ---")

        # 1. Paths and Logging Setup
        self.base_path = Path(__file__).parent
        self.log_dir = self.base_path / "logs"
        self._setup_folders()

        # 2. STT local
        self.stt_model = WhisperModel("small", device="cuda", compute_type="int8")

        # 3. LLM via API
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=config["tokens"]["groq"],
        )
        self.llm_model = "llama-3.3-70b-versatile"
        self.formatter = formatter
        self.history = []
        self.max_history_len = 10

        # 4. TTS
        self.voice_en = PiperVoice.load(config["voices"]["GB_alan"])
        self.voice_de = PiperVoice.load(config["voices"]["DE_karlsson"])

        print(f"--- LRL V4 Engine Ready ---")

    def _setup_folders(self):
        """Creates the directory structure for the maritime logbook."""
        for sub in ["audio_in", "audio_out", "transcripts"]:
            (self.log_dir / sub).mkdir(parents=True, exist_ok=True)

    def _log_event(
        self, incoming_audio_path, user_text, reply, outgoing_audio_bytes, sample_rate
    ):
        """Internal helper to save data to the logbook."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Copy Incoming Audio
        if incoming_audio_path:
            shutil.copy(
                incoming_audio_path, self.log_dir / "audio_in" / f"{timestamp}_IN.wav"
            )

        # 2. Save Outgoing Audio (TTS)
        out_wav_path = self.log_dir / "audio_out" / f"{timestamp}_OUT.wav"
        with wave.open(str(out_wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(outgoing_audio_bytes)

        # 3. Save Text Logs
        logbook_path = self.log_dir / "transcripts" / "radio_logbook.txt"
        with open(logbook_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}]\n")
            f.write(f"IN:  {user_text}\n")
            f.write(f"OUT: {reply}\n")
            f.write("-" * 30 + "\n")

    def process_radio_cycle(self, audio_path, ship_context, hotwords):
        # A. Transcription
        t0 = time.time()
        user_text = ""
        try:
            segments, info = self.stt_model.transcribe(
                audio_path, beam_size=1, vad_filter=True, initial_prompt=hotwords
            )
            user_text = " ".join([s.text for s in list(segments)]).strip()
        except Exception as e:
            print(f"FasterWhisper Error: {e}")
            return (None, None, None, "Transcription Error", [None, None, None])

        if not user_text:
            return (None, None, None, "No voice detected.", [None, None, None])

        detected_lang = info.language if info.language in ["en", "de"] else "en"
        voice = self.voice_en if detected_lang == "en" else self.voice_de
        language = "English" if detected_lang == "en" else "German"

        current_ship_context = ship_context.replace("{{LANGUAGE}}", language)
        time_transcription = time.time() - t0

        # B. Reflexion
        t1 = time.time()
        try:
            messages = [{"role": "system", "content": current_ship_context}]
            messages.extend(self.history)
            messages.append({"role": "user", "content": user_text})

            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.llm_model,
                max_tokens=150,
                temperature=0.1,
            )
            reply = chat_completion.choices[0].message.content.strip()

            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": reply})
            if len(self.history) > self.max_history_len:
                self.history = self.history[-self.max_history_len :]

        except Exception as e:
            print(f"API Error: {e}")
            reply = "System unable to answer."

        time_reflexion = time.time() - t1
        formated_reply = self.formatter.format_for_radio(reply, lang=detected_lang)

        # C. TTS
        t2 = time.time()
        try:
            full_audio_bytes = b""
            sample_rate = 22050
            for chunk in voice.synthesize(formated_reply):
                full_audio_bytes += chunk.audio_int16_bytes
                sample_rate = chunk.sample_rate

            audio_array = np.frombuffer(full_audio_bytes, dtype=np.int16)
            time_tts = time.time() - t2

            # --- LOGGING CALL ---
            self._log_event(audio_path, user_text, reply, full_audio_bytes, sample_rate)
            # --------------------

            return (
                audio_array,
                sample_rate,
                user_text,
                reply,
                [time_transcription, time_reflexion, time_tts],
            )

        except Exception as e:
            print(f"TTS Error: {e}")
            return (
                None,
                None,
                user_text,
                reply,
                [time_transcription, time_reflexion, None],
            )

    def clear_history(self):
        self.history = []

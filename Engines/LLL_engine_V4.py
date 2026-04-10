import numpy as np
from pathlib import Path
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
import ollama
import time


class LLL_v4_MaritimeEngine:
    def __init__(self, config, formatter):
        print("--- Initializing Engine ---")
        self.stt_model = WhisperModel("base", device="cuda", compute_type="int8")

        # 2. LLM
        self.llm_model = "qwen3.5:0.8b"
        try:
            ollama.pull(self.llm_model)
        except Exception as e:
            print(f"Warning: Could not pre-load Ollama model: {e}")
        self.formatter = formatter

        # 3. TTS
        self.voice_en = PiperVoice.load(config["voices"]["GB_alan"])
        self.voice_de = PiperVoice.load(config["voices"]["DE_karlsson"])

        self.output_path = Path(__file__).parent / "response_temp.wav"
        print(f"--- LLL V4 Engine Ready ---")

    def prerun_llm(self, system_prompt):
        ollama.chat(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ""},
            ],
        )

    def process_radio_cycle(self, audio_path, ship_context):

        # A. Transcription
        t0 = time.time()
        try:
            segments, info = self.stt_model.transcribe(
                audio_path, beam_size=1, vad_filter=True
            )
            user_text = " ".join([s.text for s in list(segments)]).strip()

        except Exception as e:
            print(f"FasterWhisper Error: {e}")
            reply = "Local processing error. Over."

        if not user_text:
            return (
                None,
                None,
                None,
                "No voice detected.",
                [None, None, None],
            )
        detected_lang = info.language if info.language in ["en", "de"] else "en"
        if detected_lang == "en":
            voice = self.voice_en
            language = "English"
        else:
            voice = self.voice_de
            language = "German"
        ship_context = ship_context.replace("{{LANGUAGE}}", language)

        time_transcription = time.time() - t0

        # B Reflexion
        t1 = time.time()
        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": ship_context},
                    {"role": "user", "content": user_text},
                ],
                options={
                    "temperature": 0,  # Supprime l'aléatoire (Créativité -> 0)
                    "num_predict": 100,  # Limite la longueur (environ 75 mots)
                    "top_p": 0.9,  # Filtre les mots les moins probables
                    "repeat_penalty": 1.2,  # Évite les répétitions de phrases
                },
            )
            reply = response["message"]["content"].strip()
        except Exception as e:
            print(f"Ollama Error: {e}")
            reply = "Local processing error. Over."

        time_reflexion = time.time() - t1

        formated_reply = self.formatter.format_for_radio(reply, lang=detected_lang)

        # C. TTS
        t2 = time.time()
        try:
            full_audio = b""
            for chunk in voice.synthesize(formated_reply):
                full_audio += chunk.audio_int16_bytes

            audio_array = np.frombuffer(full_audio, dtype=np.int16)
            time_tts = time.time() - t2

            return (
                audio_array,
                chunk.sample_rate,
                user_text,
                reply,
                [time_transcription, time_reflexion, time_tts],
            )

        except Exception as e:
            print(f"TTS API Error: {e}")
            return (
                None,
                None,
                user_text,
                reply,
                [time_transcription, time_reflexion, None],
            )

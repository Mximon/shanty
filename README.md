# shanty
STT-LLM-TTS Pipeline for Maritime Radio Communications

## Requirements : 
- Cuda for the Local-Remote-Local implementation
- Python 12.x
- Ollama for the Local-Local-Local implementation
If you don't use Cuda you will have to change the execution of the Whisper model in Engines/LRL_engin_V4.py from "cuda" to "cpu" or something else.
Cuda is automatically installed with the requirements.

## Installation:
- git clone https://github.com/Mximon/shanty.git
- create python venv (python 12.x)
- pip install requirements.txt

## Execution:
- Get Huggingface User Access Token at https://huggingface.co/docs/hub/security-tokens
- For LRL implementation get Groq API Key at https://console.groq.com/keys
- Update config.yaml with the keys
- Go in root directory
- python main.py
- Open browser at indicated localhost server

## Architecture

The system uses a Speech-to-Text | LLM | Text-to-Speech pipeline to understand and respond to Maritime Radio Communications
Two implementations are available: LRL (Local-Remote-Local) and LLL (Local-Local-Local)
Both use faster-whisper for STT and PiperVoice for TTS but the LRL version uses the groq API with llama-3.3-70b-versatile for the answer generation while the LLL implementation uses Ollama with qwen3.5:0.8b.


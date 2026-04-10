# shanty
STT-LLM-TTS Pipeline for Maritime Radio Communications

##Requirements : 
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
- Go in root directory
- python main.py

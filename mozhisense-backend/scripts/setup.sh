#!/bin/bash
set -e

echo "\033[32m[MozhiSense] Step 1: Creating Python virtual environment...\033[0m"
python3 -m venv venv
source venv/bin/activate

echo "\033[32m[MozhiSense] Step 2: Upgrading pip...\033[0m"
pip install --upgrade pip

echo "\033[32m[MozhiSense] Step 3: Installing requirements...\033[0m"
pip install -r requirements.txt

echo "\033[32m[MozhiSense] Step 4: Creating models directory and downloading Stanza Tamil model...\033[0m"
mkdir -p models/stanza
python -c "import stanza; stanza.download('ta', model_dir='models/stanza')"

echo "\033[32m[MozhiSense] Step 5: Installing Ollama and pulling Qwen 1.5B into models/ollama...\033[0m"
curl -fsSL https://ollama.com/install.sh | sh
mkdir -p models/ollama
export OLLAMA_MODELS="$(pwd)/models/ollama"
ollama pull qwen2:1.5b

echo "\033[32m[MozhiSense] Step 6: Initializing SQLite database...\033[0m"
python -c "from db.database import init_db; init_db()"

echo "\033[32m[MozhiSense] Step 7: Verifying pipeline...\033[0m"
export PYTHONPATH="$(pwd)"
python scripts/verify.py

echo "\033[32m[MozhiSense] Step 8: Running pre-generation pipeline...\033[0m"
python admin/pregenerate.py

echo "\033[32m[MozhiSense] Step 8: Starting FastAPI server...\033[0m"
uvicorn main:app --reload --host 0.0.0.0 --port 8000

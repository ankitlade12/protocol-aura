import subprocess
import sys


def run_api():
    subprocess.run([sys.executable, "-m", "uvicorn", "protocol_aura.api.main:app", "--reload"])


def run_ui():
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/protocol_aura/ui/dashboard.py"])


if __name__ == "__main__":
    run_ui()

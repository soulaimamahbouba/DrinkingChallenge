"""
AquaGuard — One-click setup and run script.

Usage:
    python run.py setup     # install deps + generate data + train models
    python run.py generate  # generate synthetic data only
    python run.py train     # train models only
    python run.py api       # start FastAPI server
    python run.py dashboard # start Streamlit dashboard
    python run.py demo      # generate + train + launch dashboard
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)


def run_cmd(cmd, desc=""):
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}")
    subprocess.run(cmd, shell=True, check=True)


def setup():
    run_cmd(f"{sys.executable} -m pip install -r requirements.txt", "Installing dependencies")
    generate()
    train()


def generate():
    run_cmd(f"{sys.executable} src/data/synthetic_generator.py", "Generating synthetic sensor data")


def train():
    run_cmd(f"{sys.executable} src/models/train.py", "Training ML models")


def api():
    run_cmd(f"{sys.executable} -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000",
            "Starting FastAPI server on http://localhost:8000")


def dashboard():
    run_cmd(f"{sys.executable} -m streamlit run src/dashboard/app.py --server.port 8501",
            "Starting Streamlit dashboard on http://localhost:8501")


def demo():
    generate()
    train()
    dashboard()


if __name__ == "__main__":
    commands = {
        "setup": setup,
        "generate": generate,
        "train": train,
        "api": api,
        "dashboard": dashboard,
        "demo": demo,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: python run.py [setup|generate|train|api|dashboard|demo]")
        print("\nRecommended first run: python run.py demo")
        sys.exit(1)

    commands[sys.argv[1]]()

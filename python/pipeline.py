"""
pipeline.py - Full Data Pipeline Orchestrator
Author: Kouamé Ruben
Description: Runs the complete pipeline: ingest => clean => transform => forecast => alerts
"""

import subprocess
import sys
import time
import os
from pathlib import Path

STEPS = [
    ("01_ingest.py",    "[1/5] Ingesting raw data..."),
    ("02_clean.py",     "[2/5] Cleaning & validating..."),
    ("03_transform.py", "[3/5] Transforming & computing KPIs..."),
    ("04_forecast.py",  "[4/5] Running ML forecasts..."),
    ("05_alerts.py",    "[5/5] Generating alerts & recommendations..."),
]

def run_pipeline():
    print("=" * 60)
    print("  PHARMA SUPPLY CHAIN - DATA PIPELINE")
    print("=" * 60)
    
    start = time.time()
    
    # Determine project root (parent of python/ folder)
    this_file = Path(__file__).resolve()
    python_dir = this_file.parent
    project_root = python_dir.parent
    
    # Change working directory to project root so data/ paths work
    os.chdir(project_root)
    print(f"\n  Working directory: {project_root}")
    
    for script, msg in STEPS:
        print(f"\n{msg}")
        script_path = python_dir / script
        
        if not script_path.exists():
            print(f"  [ERROR] Script not found: {script_path}")
            return False
        
        # Force UTF-8 encoding for subprocess output (fixes Windows cp1252 issues)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True,
            cwd=str(project_root),
            env=env,
            encoding="utf-8",
            errors="replace"
        )
        
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                print(f"  {line}")
        
        if result.returncode != 0:
            print(f"  [ERROR] FAILED:")
            for line in result.stderr.strip().split("\n")[-10:]:
                print(f"     {line}")
            return False
    
    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  [OK] Pipeline complete in {elapsed:.1f}s")
    print(f"  [>>] Launch dashboard: streamlit run dashboard/app.py")
    print(f"{'=' * 60}")
    return True

if __name__ == "__main__":
    run_pipeline()

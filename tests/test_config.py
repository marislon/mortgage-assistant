import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_app_fails_without_database_url(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        check=False,
        cwd=tmp_path,
        env={
            **{k: v for k, v in os.environ.items() if k != "DATABASE_URL"},
            "PYTHONPATH": str(ROOT),
        },
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "database_url" in proc.stderr.lower()

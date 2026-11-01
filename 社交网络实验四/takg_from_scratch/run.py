from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT / "src"))

from takg.cli import main


if __name__ == "__main__":
    main()

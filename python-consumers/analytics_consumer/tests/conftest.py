# Ensure the package 'analytics_consumer' is importable when running tests
import sys
from pathlib import Path

# Add the parent directory of the package to sys.path
# tests/ -> analytics_consumer/ -> python-consumers/
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

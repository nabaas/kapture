"""Pytest config — adds the repo root to sys.path so `trading_research.*`
imports resolve regardless of where pytest is invoked from.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

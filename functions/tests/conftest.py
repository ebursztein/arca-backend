"""
Pytest configuration for Arca Backend tests.

Adds the functions directory to the path so tests can import modules.
"""
import sys
from pathlib import Path

# Add functions directory to path for imports
functions_dir = Path(__file__).parent.parent
sys.path.insert(0, str(functions_dir))

"""Pytest configuration for Timer MCP tests."""

import os
import sys
from pathlib import Path

# Add src directory to Python path so tests can import timer_mcp
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Set a default environment for tests
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "8000")

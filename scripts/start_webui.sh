#!/usr/bin/env python3
"""
启动AOSFT-MVP Web UI
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

import streamlit.web.bootstrap as bootstrap

if __name__ == '__main__':
    script_path = str(project_root / "src" / "web" / "dashboard.py")
    bootstrap.run(script_path, "", [], {})

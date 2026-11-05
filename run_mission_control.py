"""
ORBIT-INTEL 6G: Mission Control Web Server Launcher
IEEE Communications Society STLC 2026 Showcase.
"""

import sys
import webbrowser
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web.server import app

def main():
    port = 5000
    url = f"http://127.0.0.1:{port}"
    print("=" * 72)
    print("ORBIT-INTEL 6G: GLOBAL NETWORK INTELLIGENCE & MISSION CONTROL")
    print("    Target: IEEE ComSoc STLC 2026 Showcase Demonstration")
    print(f"    Web Interface: {url}")
    print("=" * 72)

    # Launch browser automatically
    try:
        webbrowser.open(url)
    except Exception:
        pass

    app.run(host="127.0.0.1", port=port, debug=False)

if __name__ == "__main__":
    main()

"""
ACEForge — ACEmulator Content Generator
Entry point. Run this file to launch the application.
"""

import sys
import os

# Ensure the package root is on the path when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aceforge.app import ACEForgeApp

if __name__ == "__main__":
    app = ACEForgeApp()
    app.mainloop()

#!/usr/bin/env python3
"""
Pet Manager Application
=======================

A desktop application for managing pets with offline-first architecture.
Uses Turso (LibSQL) for both local and remote database storage with
automatic synchronization.

Features:
- User authentication (login/register)
- Pet CRUD operations
- Offline-first with local SQLite storage
- Automatic sync with Turso cloud database when online
- Session persistence across app restarts

Usage:
    python main.py

Configuration:
    Copy .env.example to .env and add your Turso credentials:
    - TURSO_DATABASE_URL: Your Turso database URL
    - TURSO_AUTH_TOKEN: Your Turso auth token

    The app works fully offline without Turso configuration,
    but sync features will be disabled.
"""

import sys
import os

# Add the project directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import PetManagerApp


def main():
    """Application entry point."""
    try:
        app = PetManagerApp()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

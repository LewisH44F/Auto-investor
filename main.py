#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║     AutoInvestor Intelligence System                 ║
║     AI-powered NASDAQ analysis platform              ║
║                                                      ║
║     Press ▶ in VS Code to launch everything.         ║
╚══════════════════════════════════════════════════════╝

No Docker. No terminals. No setup.
Just press Run.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).parent
PORT = 8000
URL = f"http://localhost:{PORT}"

# ── Step 1: Auto-install missing dependencies ─────────────────────────────────

PACKAGES = [
    "fastapi",
    "uvicorn[standard]",
    "sqlalchemy",
    "aiosqlite",
    "yfinance",
    "pandas",
    "numpy",
    "httpx",
    "apscheduler",
    "pydantic-settings",
    "python-dotenv",
    "feedparser",
    "beautifulsoup4",
    "loguru",
    "aiofiles",
    "websockets",
    "rich",
]

IMPORT_MAP = {
    "fastapi": "fastapi",
    "uvicorn[standard]": "uvicorn",
    "sqlalchemy": "sqlalchemy",
    "aiosqlite": "aiosqlite",
    "yfinance": "yfinance",
    "pandas": "pandas",
    "numpy": "numpy",
    "httpx": "httpx",
    "apscheduler": "apscheduler",
    "pydantic-settings": "pydantic_settings",
    "python-dotenv": "dotenv",
    "feedparser": "feedparser",
    "beautifulsoup4": "bs4",
    "loguru": "loguru",
    "aiofiles": "aiofiles",
    "websockets": "websockets",
    "rich": "rich",
}


def _check_and_install():
    missing = []
    for pkg, mod in IMPORT_MAP.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"\n📦 Installing {len(missing)} required packages...")
        print("   This only happens once.\n")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade"] + missing,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            print(f"   ✓ Packages installed successfully\n")
        except subprocess.CalledProcessError:
            # Try without --quiet for visibility
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + missing
            )


_check_and_install()

# ── Now safe to import everything ─────────────────────────────────────────────
import os
from dotenv import load_dotenv

load_dotenv(ROOT_DIR / ".env")

# Add project root to Python path
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Step 2: Pretty console output ─────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def _print_banner():
    console.print()
    console.print(Panel.fit(
        "[bold blue]AutoInvestor Intelligence System[/bold blue]\n"
        "[dim cyan]AI-powered NASDAQ swing-trade analysis platform[/dim cyan]\n"
        "[dim]Powered by yfinance • SQLite • FastAPI • Real-time analysis[/dim]",
        border_style="blue",
        padding=(1, 4),
    ))
    console.print()


# ── Step 3: Build React frontend (one-time) ───────────────────────────────────

def _build_frontend():
    dist = ROOT_DIR / "frontend" / "dist"
    if (dist / "index.html").exists():
        console.print("[dim]  ✓ Frontend already built[/dim]")
        return

    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        console.print("[yellow]  ℹ  Node/npm not found — using built-in HTML dashboard[/yellow]")
        console.print("[dim]    Install Node.js for the full React dashboard[/dim]")
        return

    frontend_dir = ROOT_DIR / "frontend"
    if not (frontend_dir / "package.json").exists():
        return

    console.print("[blue]  Building React dashboard...[/blue] [dim](one-time, ~60s)[/dim]")
    try:
        subprocess.run(
            [npm, "install", "--silent", "--prefer-offline"],
            cwd=frontend_dir, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            [npm, "run", "build"],
            cwd=frontend_dir, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        console.print("  [green]✓ React dashboard built[/green]")
    except subprocess.CalledProcessError:
        console.print("[yellow]  ⚠  Frontend build failed — using built-in HTML dashboard[/yellow]")


# ── Step 4: Initialize database ───────────────────────────────────────────────

def _init_database():
    import asyncio
    from app.core.database import init_db_sync
    console.print("  [blue]Initialising database...[/blue]")
    init_db_sync()
    console.print("  [green]✓ SQLite database ready[/green]")


# ── Step 5: Start FastAPI server ──────────────────────────────────────────────

def _start_server():
    import uvicorn
    from app.main import create_app
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="warning",
        access_log=False,
    )


def _wait_for_server(timeout: int = 30) -> bool:
    import urllib.request
    import urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{URL}/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.4)
    return False


# ── Step 6: Open browser ──────────────────────────────────────────────────────

def _open_browser():
    time.sleep(0.5)
    # Prefer Chrome, fallback to default
    chrome_paths = [
        "google-chrome", "google-chrome-stable", "chromium-browser",
        "chromium", "chrome",
    ]
    if sys.platform == "darwin":
        chrome_paths = ["open -a 'Google Chrome'"] + chrome_paths
    elif sys.platform == "win32":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ] + chrome_paths

    for path in chrome_paths:
        if shutil.which(path.split()[0]):
            try:
                subprocess.Popen([path, URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                continue

    webbrowser.open(URL)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    _print_banner()

    console.print("[bold]Starting up...[/bold]\n")

    console.print("  [green]✓ Dependencies ready[/green]")

    _build_frontend()
    _init_database()

    # Start server in daemon thread
    server_thread = threading.Thread(target=_start_server, daemon=True, name="uvicorn")
    server_thread.start()

    console.print("  [blue]Starting API server...[/blue]")
    ready = _wait_for_server(timeout=30)

    if not ready:
        console.print("\n[red]  ✗ Server failed to start. Check for port conflicts on :8000[/red]")
        sys.exit(1)

    console.print("  [green]✓ Server ready[/green]\n")

    # Print access table
    table = Table(box=box.ROUNDED, border_style="blue", show_header=False, padding=(0, 2))
    table.add_column("Label", style="dim")
    table.add_column("URL", style="bold cyan")
    table.add_row("📊 Dashboard", URL)
    table.add_row("📖 API Docs",  f"{URL}/docs")
    table.add_row("❤  Health",    f"{URL}/health")
    console.print(table)

    console.print()
    console.print("[bold green]  🚀 AutoInvestor is running![/bold green]")
    console.print("[dim]     Press Ctrl+C to stop[/dim]\n")

    _open_browser()

    try:
        server_thread.join()
    except KeyboardInterrupt:
        console.print("\n[yellow]  Shutting down gracefully...[/yellow]")
        console.print("[dim]  Goodbye.[/dim]\n")


if __name__ == "__main__":
    main()

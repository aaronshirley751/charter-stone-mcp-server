import time
import schedule
import logging
from datetime import datetime
import sys
import io

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import your agents
# Note: We assume watchdog.py and orchestrator.py are in the same folder
import watchdog
import orchestrator

# =============================================================================
# CONFIGURATION
# =============================================================================

# How often to run (in minutes)
WATCHDOG_INTERVAL = 60   # Scan for news every hour
ORCHESTRATOR_INTERVAL = 15 # Check the inbox every 15 mins

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DAEMON] - %(message)s',
    handlers=[
        logging.FileHandler("daemon.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# =============================================================================
# JOB WRAPPERS
# =============================================================================

def run_watchdog():
    logging.info("🐺 Releasing the Watchdog...")
    try:
        # reload history to ensure fresh state if running long-term
        watchdog.scan_feeds()
        logging.info("✅ Watchdog scan complete.")
    except Exception as e:
        logging.error(f"❌ Watchdog crashed: {e}")

def run_orchestrator():
    logging.info("🌉 Bridge opening...")
    try:
        orchestrator.process_tasks()
        logging.info("✅ Orchestration complete.")
    except Exception as e:
        logging.error(f"❌ Orchestrator crashed: {e}")

# =============================================================================
# MAIN LOOP
# =============================================================================

def start_engine():
    print("""
    ===================================================
       CHARTER & STONE - DAEMON ENGINE v1.0
       "The Digital Standup that never sleeps"
    ===================================================
    """)
    
    # 1. Schedule the Jobs
    schedule.every(WATCHDOG_INTERVAL).minutes.do(run_watchdog)
    schedule.every(ORCHESTRATOR_INTERVAL).minutes.do(run_orchestrator)
    
    # 2. Run immediately on startup (so you know it works)
    logging.info("🚀 Startup: Running initial pass...")
    run_orchestrator() # Run bridge first to clear inbox
    run_watchdog()     # Then scan for new leads
    
    # 3. Enter the Loop
    logging.info(f"⏳ Standing by. Watchdog: {WATCHDOG_INTERVAL}m | Bridge: {ORCHESTRATOR_INTERVAL}m")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        start_engine()
    except KeyboardInterrupt:
        print("\n🛑 Daemon stopped by user.")

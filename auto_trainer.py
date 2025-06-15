from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from datetime import datetime

def scheduled_job():
    print(f"[{datetime.now().isoformat()}] Running scheduled job...")

def start_scheduler():
    scheduler = AsyncIOScheduler(timezone=pytz.utc)
    scheduler.add_job(scheduled_job, "interval", minutes=5)
    scheduler.start()

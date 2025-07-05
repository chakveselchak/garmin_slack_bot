import schedule
import time
import threading
from models import db, User
from garmin import get_body_battery
from slack_api import update_slack_status
from flask import Flask
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 👈 или INFO, если не хочешь много мусора
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

logger = logging.getLogger(__name__)

def update_all_users():
    with Flask(__name__).app_context():
        users = User.query.all()
        logger.info(f"users = {users}")
        for user in users:
            if user.slack_access_token and user.garmin_email and user.garmin_password:
                battery = get_body_battery(user.garmin_email, user.garmin_password)
                logger.info(f"battery = {battery}"
                if battery is not None:
                    update_slack_status(user.slack_access_token, battery)

def start_scheduler():
    schedule.every(1).minutes.do(update_all_users)
    logger.info(f"tik")

    def run():
        while True:
            schedule.run_pending()
            time.sleep(1)

    threading.Thread(target=run, daemon=True).start()

import schedule
import time
import threading
from models import db, User
from garmin import get_body_battery
from slack_api import update_slack_status
from flask import Flask

def update_all_users():
    with Flask(__name__).app_context():
        users = User.query.all()
        for user in users:
            if user.slack_access_token and user.garmin_email and user.garmin_password:
                battery = get_body_battery(user.garmin_email, user.garmin_password)
                if battery is not None:
                    update_slack_status(user.slack_access_token, battery)

def start_scheduler():
    schedule.every(30).minutes.do(update_all_users)

    def run():
        while True:
            schedule.run_pending()
            time.sleep(1)

    threading.Thread(target=run, daemon=True).start()

import schedule
import time
import threading
import logging
from models import db, User
from garmin import get_body_battery
from slack_api import update_slack_status

# Настройка логов
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

def start_scheduler(app):
    def update_all_users():
        with app.app_context():
            users = User.query.all()
            logger.info(f"Найдено пользователей: {len(users)}")

            for user in users:
                logger.info(f"Проверка: {user.slack_user_id}")

                if user.slack_access_token and user.garmin_email and user.garmin_password:
                    logger.info(f"Запрашиваю Body Battery для {user.garmin_email}")

                    battery = get_body_battery(user.garmin_email, user.garmin_password)
                    if battery is not None:
                        logger.info(f"✔️ Battery = {battery} для {user.slack_user_id}")
                        update_slack_status(user.slack_access_token, battery)
                    else:
                        logger.warning(f"⚠️ Не удалось получить Body Battery для {user.slack_user_id}")
                else:
                    logger.warning(f"❌ Пропущен пользователь {user.slack_user_id} — нет токена или данных Garmin")

    # Интервал обновления (15 мин = разумно для Garmin API)
    schedule.every(15).minutes.do(update_all_users)
    logger.info("⏰ Планировщик запущен")

    def run():
        while True:
            schedule.run_pending()
            time.sleep(1)

    threading.Thread(target=run, daemon=True).start()

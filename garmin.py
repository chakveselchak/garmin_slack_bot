from garminconnect import Garmin
import logging
import os

logging.basicConfig(
    level=logging.DEBUG,  # 👈 или INFO, если не хочешь много мусора
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

logger = logging.getLogger(__name__)

# Папка для хранения сессий
SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

def get_body_battery(email, password):
    session_file = os.path.join(SESSIONS_DIR, email.replace("@", "_at_") + ".json")

    try:
        # Если есть сохранённая сессия — используем её
        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                session_data = json.load(f)
            client = Garmin(email, password, session_data=session_data)
            client.login()
        else:
            # Первый вход — логинимся и сохраняем сессию
            client = Garmin(email, password)
            client.login()
            session_data = client.export_session()
            with open(session_file, "w") as f:
                json.dump(session_data, f)
        
        logger.info(f"session: {session_data}")

        # Получаем Body Battery
        battery = client.get_body_battery()
        battery_level = battery.get("batteryLevel")

        logger.info(f"BodyBattery for {email}: {battery_level}")
        return battery_level

    except Exception as e:
        logger.error(f"Garmin error for {email}: {e}")
        return None
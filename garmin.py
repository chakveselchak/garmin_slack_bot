from garminconnect import Garmin
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 👈 или INFO, если не хочешь много мусора
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

logger = logging.getLogger(__name__)

def get_body_battery(email, password):
    try:
        client = Garmin(email, password)
        client.login()

        data = client.get_body_battery()
        logger.info(f"datatata = {data}")
        # Пример: {'batteryLevel': 75, 'timestamp': ...}

        battery_level = data.get("batteryLevel")
        logger.info(f"Garmin body battery = {battery_level}")
        return battery_level
    except Exception as e:
        logger.error(f"Garmin error for {email}: {e}")
        return None

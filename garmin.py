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
        logger.info(f"client = {client}")
        data = client.get_body_battery()
        logger.info(f"get_body_battery = {data}")
        return data.get("bodyBattery", {}).get("value", None)
    except Exception as e:
        print("Garmin error:", e)
        return None

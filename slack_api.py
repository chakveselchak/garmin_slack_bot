from slack_sdk import WebClient
import logging

logger = logging.getLogger(__name__)

def update_slack_status(token, battery):
    client = WebClient(token=token)
    
    # Формируем текст статуса в зависимости от уровня батареи
    if battery < 35:
        text = f"Body Battery: {battery}% - Просьба не звонить. Отвечу текстом"
        emoji = ":low_battery:"
    else:
        text = f"Body Battery: {battery}%"
        emoji = ":battery:"
    
    profile = {
        "status_text": text,
        "status_emoji": emoji,
        "status_expiration": 0
    }
    try:
        client.users_profile_set(profile=profile)
        logger.info(f"✅ Статус Slack обновлен: {text}")
    except Exception as e:
        logger.error(f"❌ Ошибка Slack: {e}")

from slack_sdk import WebClient
import logging

logger = logging.getLogger(__name__)

def get_battery_emoji(battery_level, icon_style="classic"):
    """Получает emoji для батареи в зависимости от уровня и стиля"""
    if icon_style == "doom":
        # Игровой формат (DOOM 1993)
        if battery_level > 86:
            return ":doom0:"
        elif battery_level > 72:
            return ":doom1:"
        elif battery_level > 58:
            return ":doom2:"
        elif battery_level > 44:
            return ":doom3:"
        elif battery_level > 30:
            return ":doom4:"
        elif battery_level > 25:
            return ":doom5:"
        elif battery_level > 20:
            return ":doom6:"
        else:  # ниже 20%
            return ":doom7:"
    else:
        # Классический формат (батарейки)
        if battery_level < 35:
            return ":low_battery:"
        else:
            return ":battery:"

def update_slack_status(token, battery, icon_style="classic"):
    client = WebClient(token=token)
    
    # Формируем текст статуса в зависимости от уровня батареи
    if battery < 35:
        text = f"Body Battery: {battery}% - Просьба не звонить. Отвечу текстом"
    else:
        text = f"Body Battery: {battery}%"
    
    # Получаем соответствующую иконку
    emoji = get_battery_emoji(battery, icon_style)
    
    profile = {
        "status_text": text,
        "status_emoji": emoji,
        "status_expiration": 0
    }
    try:
        client.users_profile_set(profile=profile)
        logger.info(f"✅ Статус Slack обновлен: {text} ({emoji})")
    except Exception as e:
        logger.error(f"❌ Ошибка Slack: {e}")

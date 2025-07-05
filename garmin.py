from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
import logging
import os
import json
import time
import random
import datetime
from requests.exceptions import HTTPError

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

logger = logging.getLogger(__name__)

# Папка для хранения токенов
TOKENSTORE_DIR = os.path.expanduser("~/.garminconnect")
os.makedirs(TOKENSTORE_DIR, exist_ok=True)

def init_api(email, password):
    """Инициализация API с сохранением токенов"""
    try:
        api = Garmin(email, password)
        api.login()
        logger.info(f"Успешная авторизация для {email}")
        return api
    except (
        GarminConnectConnectionError,
        GarminConnectAuthenticationError,
        GarminConnectTooManyRequestsError,
        HTTPError,
    ) as err:
        logger.error(f"Ошибка авторизации для {email}: {err}")
        return None

def get_body_battery(email, password, max_retries=3):
    """Получение Body Battery с правильной обработкой сессий"""
    
    for attempt in range(max_retries):
        try:
            # Инициализируем API
            api = init_api(email, password)
            if not api:
                logger.error(f"Не удалось инициализировать API для {email}")
                return None
            
            # Получаем данные Body Battery для сегодняшнего дня
            today = datetime.date.today()
            battery_data = api.get_body_battery(today.isoformat())
            
            # Извлекаем уровень батареи
            if battery_data and 'bodyBatteryValuesArray' in battery_data:
                # Берем последнее значение за день
                values = battery_data['bodyBatteryValuesArray']
                if values:
                    battery_level = values[-1].get('batteryLevel', 0)
                    logger.info(f"BodyBattery for {email}: {battery_level}")
                    return battery_level
                else:
                    logger.warning(f"Нет данных Body Battery для {email}")
                    return None
            else:
                logger.warning(f"Неожиданный формат данных Body Battery для {email}")
                return None

        except GarminConnectTooManyRequestsError as e:
            logger.error(f"Rate limited для {email} (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(1, 5)
                logger.info(f"Ожидание {wait_time:.1f} секунд перед повторной попыткой...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Достигнуто максимальное количество попыток для {email}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка Garmin для {email} (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = random.uniform(5, 15)
                logger.info(f"Ожидание {wait_time:.1f} секунд перед повторной попыткой...")
                time.sleep(wait_time)
                continue
            else:
                return None
    
    return None
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

# Глобальный кэш для хранения активных сессий
_active_sessions = {}
_session_timestamps = {}

def get_cached_api(email, password):
    """Получение кэшированного API клиента или создание нового"""
    global _active_sessions, _session_timestamps
    
    # Проверяем, есть ли активная сессия
    if email in _active_sessions:
        # Проверяем, не истекла ли сессия (24 часа)
        if time.time() - _session_timestamps.get(email, 0) < 24 * 3600:
            logger.info(f"Использую кэшированную сессию для {email}")
            return _active_sessions[email]
        else:
            logger.info(f"Сессия для {email} истекла, создаю новую")
            del _active_sessions[email]
            del _session_timestamps[email]
    
    # Создаем новую сессию
    try:
        logger.info(f"Создаю новую сессию для {email}")
        api = Garmin(email, password)
        api.login()
        
        # Сохраняем в кэш
        _active_sessions[email] = api
        _session_timestamps[email] = time.time()
        
        logger.info(f"✅ Успешно создана сессия для {email}")
        return api
        
    except (
        GarminConnectConnectionError,
        GarminConnectAuthenticationError,
        GarminConnectTooManyRequestsError,
        HTTPError,
    ) as err:
        logger.error(f"❌ Ошибка создания сессии для {email}: {err}")
        return None

def get_body_battery(email, password, max_retries=2):
    """Получение Body Battery с использованием кэшированных сессий"""
    
    for attempt in range(max_retries):
        try:
            # Получаем API клиент (кэшированный или новый)
            api = get_cached_api(email, password)
            if not api:
                logger.error(f"Не удалось получить API клиент для {email}")
                return None
            
            # Добавляем небольшую задержку перед запросом
            time.sleep(random.uniform(2, 5))
            
            # Получаем данные Body Battery для сегодняшнего дня
            today = datetime.date.today()
            logger.info(f"Запрашиваю Body Battery для {email} на {today}")
            
            battery_data = api.get_body_battery(today.isoformat())
            
            # Отладочное логирование для понимания формата данных
            logger.debug(f"Полученные данные Body Battery: {battery_data}")
            logger.debug(f"Тип данных: {type(battery_data)}")
            
            # Извлекаем уровень батареи
            if battery_data:
                if isinstance(battery_data, dict):
                    logger.debug(f"Ключи в данных: {list(battery_data.keys())}")
                    
                    # Проверяем различные возможные форматы
                    if 'bodyBatteryValuesArray' in battery_data:
                        values = battery_data.get('bodyBatteryValuesArray', [])
                        if values:
                            battery_level = values[-1].get('batteryLevel', 0)
                            logger.info(f"✅ BodyBattery для {email}: {battery_level} (формат: bodyBatteryValuesArray)")
                            return battery_level
                    
                    # Альтернативный формат - прямо в корне
                    elif 'batteryLevel' in battery_data:
                        battery_level = battery_data.get('batteryLevel', 0)
                        logger.info(f"✅ BodyBattery для {email}: {battery_level} (формат: прямой)")
                        return battery_level
                    
                    # Проверяем другие возможные ключи
                    elif 'bodyBatteryData' in battery_data:
                        body_battery_data = battery_data.get('bodyBatteryData', [])
                        if body_battery_data:
                            battery_level = body_battery_data[-1].get('batteryLevel', 0)
                            logger.info(f"✅ BodyBattery для {email}: {battery_level} (формат: bodyBatteryData)")
                            return battery_level
                    
                    # Если это список
                    elif isinstance(battery_data, list) and battery_data:
                        battery_level = battery_data[-1].get('batteryLevel', 0)
                        logger.info(f"✅ BodyBattery для {email}: {battery_level} (формат: список)")
                        return battery_level
                    
                    else:
                        logger.warning(f"⚠️ Неизвестный формат данных Body Battery для {email}")
                        logger.warning(f"Доступные ключи: {list(battery_data.keys()) if isinstance(battery_data, dict) else 'не словарь'}")
                        return None
                        
                elif isinstance(battery_data, list):
                    logger.debug(f"Данные в формате списка, длина: {len(battery_data)}")
                    if battery_data:
                        battery_level = battery_data[-1].get('batteryLevel', 0)
                        logger.info(f"✅ BodyBattery для {email}: {battery_level} (формат: список)")
                        return battery_level
                    else:
                        logger.warning(f"⚠️ Пустой список данных Body Battery для {email}")
                        return None
                else:
                    logger.warning(f"⚠️ Неожиданный тип данных Body Battery для {email}: {type(battery_data)}")
                    return None
            else:
                logger.warning(f"⚠️ Нет данных Body Battery для {email}")
                return None

        except GarminConnectTooManyRequestsError as e:
            logger.error(f"❌ Rate limited для {email} (попытка {attempt + 1}/{max_retries}): {e}")
            
            # Удаляем сессию из кэша, так как она может быть проблемной
            if email in _active_sessions:
                del _active_sessions[email]
                del _session_timestamps[email]
            
            if attempt < max_retries - 1:
                # Увеличиваем время ожидания значительно
                wait_time = random.uniform(300, 600)  # 5-10 минут
                logger.info(f"⏳ Ожидание {wait_time/60:.1f} минут перед повторной попыткой...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"❌ Достигнуто максимальное количество попыток для {email}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Общая ошибка Garmin для {email} (попытка {attempt + 1}/{max_retries}): {e}")
            
            # Удаляем сессию из кэша при ошибке
            if email in _active_sessions:
                del _active_sessions[email]
                del _session_timestamps[email]
            
            if attempt < max_retries - 1:
                wait_time = random.uniform(60, 120)  # 1-2 минуты
                logger.info(f"⏳ Ожидание {wait_time:.1f} секунд перед повторной попыткой...")
                time.sleep(wait_time)
                continue
            else:
                return None
    
    return None

def clear_session_cache():
    """Очистка кэша сессий"""
    global _active_sessions, _session_timestamps
    _active_sessions.clear()
    _session_timestamps.clear()
    logger.info("🧹 Кэш сессий очищен")
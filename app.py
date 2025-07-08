import os
import logging
from dotenv import load_dotenv
load_dotenv()


from flask import Flask, request, redirect, render_template, session
from models import db, init_db, User
from oauth import start_slack_oauth, handle_slack_callback
from scheduler import start_scheduler

logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.secret_key = 'supersecret'
db.init_app(app)

with app.app_context():
    init_db()
    
    # Миграция для существующих пользователей
    try:
        users_without_icon_style = User.query.filter(User.icon_style == None).all()
        for user in users_without_icon_style:
            user.icon_style = "classic"
        if users_without_icon_style:
            db.session.commit()
            logger.info(f"Обновлено {len(users_without_icon_style)} пользователей с настройками по умолчанию")
    except Exception as e:
        logger.warning(f"Миграция настроек иконок: {e}")
    
    start_scheduler(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/slack/oauth/start')
def slack_oauth_start():
    return start_slack_oauth()

@app.route('/slack/oauth/callback')
def slack_oauth_callback():
    return handle_slack_callback(request)

@app.route('/connect-garmin', methods=["GET", "POST"])
def connect_garmin():
    if "slack_user_id" not in session:
        return redirect("/")

    user = User.query.filter_by(slack_user_id=session["slack_user_id"]).first()
    if request.method == "POST" and user:
        user.garmin_email = request.form["email"]  # автошифруется
        user.garmin_password = request.form["password"]  # автошифруется
        db.session.commit()
        
        # Сразу выполняем первый запрос Body Battery
        from garmin import get_body_battery
        from slack_api import update_slack_status
        
        if user and user.garmin_email and user.garmin_password and user.slack_access_token:
            logger.info(f"Первый запрос Body Battery для {user.garmin_email}")
            battery = get_body_battery(user.garmin_email, user.garmin_password)
            if battery is not None:
                logger.info(f"✔️ Первый Battery = {battery} для {user.slack_user_id}")
                update_slack_status(user.slack_access_token, battery, user.icon_style)
            else:
                logger.warning(f"⚠️ Не удалось получить первый Body Battery для {user.slack_user_id}")
        else:
            logger.warning("Не все данные пользователя доступны для первого запроса Body Battery")
        
        return redirect("/status")
    return render_template("login.html")

@app.route('/status')
def status():
    if "slack_user_id" not in session:
        return redirect("/")
    user = User.query.filter_by(slack_user_id=session["slack_user_id"]).first()
    
    success = user and user.garmin_email and user.garmin_password and user.slack_access_token
    battery_level = None
    
    # Если все подключено, попробуем получить текущий уровень батареи
    if success and user:
        try:
            from garmin import get_body_battery
            battery_level = get_body_battery(user.garmin_email, user.garmin_password)
        except Exception as e:
            logger.warning(f"Не удалось получить Body Battery для отображения: {e}")
    
    return render_template('status.html', success=success, battery_level=battery_level, 
                         icon_style=user.icon_style if user else "classic")

@app.route('/clear-cache')
def clear_cache():
    """Очистка кэша сессий Garmin"""
    from garmin import clear_session_cache
    clear_session_cache()
    
    return render_template('message.html', 
                         title="Кэш очищен",
                         message="🧹 Кэш сессий Garmin успешно очищен",
                         type="success",
                         back_url="/status")

@app.route('/test-battery')
def test_battery():
    """Тестирование получения Body Battery для текущего пользователя"""
    if "slack_user_id" not in session:
        return render_template('message.html',
                             title="Ошибка доступа",
                             message="❌ Нет активной сессии. Сначала подключите Slack.",
                             type="error",
                             back_url="/")
    
    user = User.query.filter_by(slack_user_id=session["slack_user_id"]).first()
    if not user or not user.garmin_email or not user.garmin_password:
        return render_template('message.html',
                             title="Garmin не подключен",
                             message="❌ Garmin аккаунт не подключен. Сначала подключите Garmin.",
                             type="error",
                             back_url="/connect-garmin")
    
    from garmin import get_body_battery
    logger.info(f"Тестовый запрос Body Battery для {user.garmin_email}")
    
    battery = get_body_battery(user.garmin_email, user.garmin_password)
    if battery is not None:
        return render_template('message.html',
                             title="Body Battery получен",
                             message=f"✅ Текущий Body Battery: {battery}%",
                             type="success",
                             back_url="/status",
                             battery_level=battery)
    else:
        return render_template('message.html',
                             title="Ошибка получения данных",
                             message="❌ Не удалось получить данные Body Battery. Проверьте логи.",
                             type="error",
                             back_url="/status")

@app.route('/settings', methods=['POST'])
def update_settings():
    """Обновление настроек пользователя"""
    if "slack_user_id" not in session:
        return redirect("/")
    
    user = User.query.filter_by(slack_user_id=session["slack_user_id"]).first()
    if not user:
        return redirect("/")
    
    # Обновляем стиль иконок
    icon_style = request.form.get('icon_style', 'classic')
    if icon_style in ['classic', 'doom']:
        user.icon_style = icon_style
        db.session.commit()
        
        return render_template('message.html',
                             title="Настройки обновлены",
                             message=f"✅ Стиль иконок изменен на: {'Классический' if icon_style == 'classic' else 'Игровой (DOOM)'}",
                             type="success",
                             back_url="/status")
    else:
        return render_template('message.html',
                             title="Ошибка",
                             message="❌ Неверный стиль иконок",
                             type="error",
                             back_url="/status")

if __name__ == '__main__':
    if os.environ.get("RENDER"):
        app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    else:
        app.run(debug=True, ssl_context=('cert.pem', 'key.pem'))




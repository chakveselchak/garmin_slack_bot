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
    start_scheduler(app)

@app.route('/')
def index():
    return '<a href="/slack/oauth/start">Подключить Slack</a>'

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
                update_slack_status(user.slack_access_token, battery)
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
    if user and user.garmin_email and user.garmin_password:
        return "✅ Всё готово! Статус будет обновляться автоматически каждые 2 часа."
    else:
        return "❌ Не все данные подключены. Пожалуйста, подключите Garmin и Slack."

@app.route('/clear-cache')
def clear_cache():
    """Очистка кэша сессий Garmin"""
    from garmin import clear_session_cache
    clear_session_cache()
    return "🧹 Кэш сессий Garmin очищен"

@app.route('/test-battery')
def test_battery():
    """Тестирование получения Body Battery для текущего пользователя"""
    if "slack_user_id" not in session:
        return "❌ Нет активной сессии. Сначала подключите Slack."
    
    user = User.query.filter_by(slack_user_id=session["slack_user_id"]).first()
    if not user or not user.garmin_email or not user.garmin_password:
        return "❌ Garmin аккаунт не подключен. Сначала подключите Garmin."
    
    from garmin import get_body_battery
    logger.info(f"Тестовый запрос Body Battery для {user.garmin_email}")
    
    battery = get_body_battery(user.garmin_email, user.garmin_password)
    if battery is not None:
        return f"✅ Body Battery: {battery}%"
    else:
        return "❌ Не удалось получить данные Body Battery. Проверьте логи."

if __name__ == '__main__':
    if os.environ.get("RENDER"):
        app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    else:
        app.run(debug=True, ssl_context=('cert.pem', 'key.pem'))




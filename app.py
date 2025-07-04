import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, redirect, render_template, session
from models import db, init_db, User
from oauth import start_slack_oauth, handle_slack_callback
from scheduler import start_scheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.secret_key = 'supersecret'
db.init_app(app)

with app.app_context():
    init_db()

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
    if request.method == "POST":
        user.garmin_email = request.form["email"]  # автошифруется
        user.garmin_password = request.form["password"]  # автошифруется
        db.session.commit()
        return "✅ Garmin успешно подключён!"
    return render_template("login.html")

if __name__ == '__main__':
    if os.environ.get("RENDER"):
        app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    else:
        app.run(debug=True, ssl_context=('cert.pem', 'key.pem'))




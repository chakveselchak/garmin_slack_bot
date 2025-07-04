import os
from urllib.parse import urlencode
from flask import redirect, session
import requests
from models import db, User
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 👈 или INFO, если не хочешь много мусора
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

logger = logging.getLogger(__name__)



SLACK_CLIENT_ID = os.getenv('SLACK_CLIENT_ID')
SLACK_CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')


def start_slack_oauth():
    logger.info(f"SLACK_CLIENT_ID = {SLACK_CLIENT_ID}")
    logger.info(f"SLACK_CLIENT_SECRET = {SLACK_CLIENT_SECRET}")
    logger.info(f"REDIRECT_URI = {REDIRECT_URI}")

    params = {
        "client_id": SLACK_CLIENT_ID,
        "user_scope": "users.profile:write,identity.basic",
        "redirect_uri": REDIRECT_URI
    }
    logger.info(f"Final redirect to: https://slack.com/oauth/v2/authorize?{urlencode(params)}")  # ✅ правильно
    return redirect(f"https://slack.com/oauth/v2/authorize?" + urlencode(params))

def handle_slack_callback(request):
    code = request.args.get('code')
    logger.info(f"code = {code}")
    response = requests.post("https://slack.com/api/oauth.v2.access", data={
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }).json()

    if response.get("ok"):
        slack_user_id = response['authed_user']['id']
        access_token = response['authed_user']['access_token']  # <-- это xoxp token
        


        session["slack_user_id"] = slack_user_id

        user = User.query.filter_by(slack_user_id=slack_user_id).first()
        if not user:
            user = User(slack_user_id=slack_user_id)
        user.slack_access_token = access_token
        db.session.add(user)
        db.session.commit()

        return redirect("/connect-garmin")
    else:
        return f"Ошибка: {response.get('error')}"

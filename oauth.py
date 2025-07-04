import os
from urllib.parse import urlencode
from flask import redirect, session
import requests
from models import db, User

SLACK_CLIENT_ID = os.getenv('SLACK_CLIENT_ID')
SLACK_CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET')

def start_slack_oauth():
    params = {
        "client_id": SLACK_CLIENT_ID,
        "scope": "users.profile:write,identity.basic",
        "redirect_uri": "https://garmin-slack-bot.onrender.com/slack/oauth/callback"
    }
    return redirect("https://slack.com/oauth/v2/authorize?" + urlencode(params))

def handle_slack_callback(request):
    code = request.args.get('code')
    response = requests.post("https://slack.com/api/oauth.v2.access", data={
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "code": code,
        "redirect_uri": "https://garmin-slack-bot.onrender.com/slack/oauth/callback"
    }).json()

    if response.get("ok"):
        slack_user_id = response['authed_user']['id']
        access_token = response['authed_user']['access_token']

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

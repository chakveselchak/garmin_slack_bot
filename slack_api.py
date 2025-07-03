from slack_sdk import WebClient

def update_slack_status(token, battery):
    client = WebClient(token=token)
    text = f"Body Battery: {battery}%"
    profile = {
        "status_text": text,
        "status_emoji": ":battery:",
        "status_expiration": 0
    }
    try:
        client.users_profile_set(profile=profile)
    except Exception as e:
        print("Slack error:", e)

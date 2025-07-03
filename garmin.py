from garminconnect import Garmin

def get_body_battery(email, password):
    try:
        client = Garmin(email, password)
        client.login()
        data = client.get_body_battery()
        return data.get("bodyBattery", {}).get("value", None)
    except Exception as e:
        print("Garmin error:", e)
        return None

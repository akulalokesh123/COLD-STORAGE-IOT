import random
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask
import threading
import os

# --- Initialize Firebase using environment variables ---
firebase_cred = credentials.Certificate({
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
})
firebase_admin.initialize_app(firebase_cred, {"databaseURL": os.getenv("FIREBASE_DB_URL")})

zones_ref = db.reference("zones")

ref.set({"test": "success"})
print("Firebase push worked!")
# --- Thresholds ---
TEMP_MAX = 10
HUMIDITY_MAX = 80

# --- Initial zone values ---
zone_values = {f"zone{i}": {"temperature": random.uniform(5,10), "humidity": random.uniform(60,80)} for i in range(1,5)}

# --- Function to push data ---
def push_data_loop():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {}

        for zone, values in zone_values.items():
            temp = round(values["temperature"] + random.uniform(-1,1), 2)
            hum = round(values["humidity"] + random.uniform(-1,1), 2)

            temp = max(0, min(15, temp))
            hum = max(50, min(90, hum))

            zone_values[zone]["temperature"] = temp
            zone_values[zone]["humidity"] = hum

            status = "⚠️ Out of Range" if temp > TEMP_MAX or hum > HUMIDITY_MAX else "Within Range"

            data[zone] = {"temperature": temp, "humidity": hum, "timestamp": now, "status": status}

        try:
            zones_ref.set(data)
            print(f"Pushed at {now}:", data)
        except Exception as e:
            print(f"Failed to push data at {now}: {e}")

        time.sleep(5)

# --- Start simulator in a separate thread ---
threading.Thread(target=push_data_loop, daemon=True).start()

# --- Flask web server ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Simulator running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

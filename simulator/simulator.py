import random
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask
import threading

# Initialize Firebase using the uploaded secret file
cred = credentials.Certificate("/etc/secrets/cold-storage-firebase.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://cold-storage-iot-default-rtdb.firebaseio.com"
})

zones_ref = db.reference("zones")

# Thresholds
TEMP_MAX = 10
HUMIDITY_MAX = 80

zone_values = {f"zone{i}": {"temperature": random.uniform(5,10), "humidity": random.uniform(60,80)} for i in range(1,5)}

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
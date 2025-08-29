import random
import time
import json
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# -----------------------------
# Firebase setup (ENV variable)
# -----------------------------
firebase_key = os.environ.get("FIREBASE_KEY")  # Environment variable from Render
if not firebase_key:
    raise Exception("❌ FIREBASE_KEY environment variable not set")

cred_dict = json.loads(firebase_key)
cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://cold-storage-iot-default-rtdb.firebaseio.com"
})

zones_ref = db.reference("zones")

# Thresholds
TEMP_MAX = 10
HUMIDITY_MAX = 80

# Initialize previous values for smoother random changes
zone_values = {
    f"zone{i}": {"temperature": random.uniform(5, 10), "humidity": random.uniform(60, 80)}
    for i in range(1, 5)
}

while True:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {}

    for zone, values in zone_values.items():
        # Smooth random variation (smaller to look realistic)
        temp = round(values["temperature"] + random.uniform(-0.3, 0.3), 2)
        hum = round(values["humidity"] + random.uniform(-0.5, 0.5), 2)

        # Keep within reasonable bounds
        temp = max(0, min(15, temp))
        hum = max(50, min(90, hum))

        # Update zone values
        zone_values[zone]["temperature"] = temp
        zone_values[zone]["humidity"] = hum

        # Determine status
        status = "⚠️ Out of Range" if temp > TEMP_MAX or hum > HUMIDITY_MAX else "Within Range"

        # Build data dict
        data[zone] = {
            "temperature": temp,
            "humidity": hum,
            "timestamp": now,
            "status": status
        }

    # Push to Firebase
    zones_ref.set(data)
    print(f"Pushed at {now}:", data)

    time.sleep(10)  # every 10s

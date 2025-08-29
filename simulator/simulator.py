import os
import random
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# ------------------------------
# Firebase Initialization
# ------------------------------

# Path to the uploaded secret JSON file on Render
SERVICE_ACCOUNT_FILE = "/etc/secrets/cold-storage-iot-firebase-adminsdk-fbsvc-8cf30a9517.json"

# Initialize Firebase Admin SDK
cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
firebase_admin.initialize_app(cred, {
    "databaseURL": os.getenv("DATABASE_URL")
})

# Reference to the "zones" node in the database
zones_ref = db.reference("zones")

# ------------------------------
# Simulation Settings
# ------------------------------

TEMP_MAX = 10       # Max temperature threshold
HUMIDITY_MAX = 80   # Max humidity threshold

# Initialize zone values with random starting numbers
zone_values = {
    f"zone{i}": {
        "temperature": random.uniform(5, 10),
        "humidity": random.uniform(60, 80)
    }
    for i in range(1, 5)
}

# ------------------------------
# Simulation Loop
# ------------------------------

try:
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {}

        for zone, values in zone_values.items():
            # Randomly fluctuate temperature and humidity
            temp = round(values["temperature"] + random.uniform(-1, 1), 2)
            hum = round(values["humidity"] + random.uniform(-1, 1), 2)

            # Clamp values to realistic ranges
            temp = max(0, min(15, temp))
            hum = max(50, min(90, hum))

            # Update current zone values
            zone_values[zone]["temperature"] = temp
            zone_values[zone]["humidity"] = hum

            # Determine status
            status = "⚠️ Out of Range" if temp > TEMP_MAX or hum > HUMIDITY_MAX else "Within Range"

            # Prepare data payload for Firebase
            data[zone] = {
                "temperature": temp,
                "humidity": hum,
                "timestamp": now,
                "status": status
            }

        # Push to Firebase with error handling
        try:
            zones_ref.set(data)
            print(f"Pushed at {now}:", data)
        except Exception as e:
            print(f"Failed to push data at {now}: {e}")

        # Wait 5 seconds before next update
        time.sleep(5)

except KeyboardInterrupt:
    print("Simulation stopped by user.")

import os
import time
import random
import datetime
import threading
import pytz
import io
import csv

from flask import Flask, Response
import firebase_admin
from firebase_admin import credentials, db

# -----------------------------
# Firebase setup
# -----------------------------
cred = credentials.Certificate("/etc/secrets/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://cold-storage-iot-default-rtdb.firebaseio.com/"
})

zones_ref = db.reference("zones")
logs_ref = db.reference("logs")   # ✅ logs location in your screenshot

# -----------------------------
# Thresholds
# -----------------------------
TEMP_MAX = 10
HUMIDITY_MAX = 80

# Initialize previous values for smoother random changes
zone_values = {
    f"zone{i}": {"temperature": random.uniform(5, 10), "humidity": random.uniform(60, 80)}
    for i in range(1, 5)
}

# -----------------------------
# Data Simulator
# -----------------------------
def push_data_loop():
    print("🚀 Simulator started. Pushing data to Firebase...")

    IST = pytz.timezone("Asia/Kolkata")

    while True:
        now = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
        zones_data = {}

        for zone, values in zone_values.items():
            # Smooth random variation
            temp = round(values["temperature"] + random.uniform(-1, 1), 2)
            hum = round(values["humidity"] + random.uniform(-1, 1), 2)

            # Keep within reasonable bounds
            temp = max(0, min(15, temp))
            hum = max(50, min(90, hum))

            # Update zone values
            zone_values[zone]["temperature"] = temp
            zone_values[zone]["humidity"] = hum

            # Determine status
            status = "⚠ Out of Range" if temp > TEMP_MAX or hum > HUMIDITY_MAX else "Within Range"

            # Build zone dict
            zones_data[zone] = {
                "temperature": temp,
                "humidity": hum,
                "timestamp": now,
                "status": status
            }

        try:
            # ✅ Store under timestamp key (like your Firebase screenshot)
            logs_ref.child(now).set(zones_data)
            print(f"✅ Pushed at {now}:", zones_data)
        except Exception as e:
            print(f"❌ Failed to push data: {e}")

        time.sleep(5)

# -----------------------------
# Flask Web Server
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Simulator is running and sending zone data to Firebase!"

@app.route("/download-logs")
def download_logs():
    try:
        # ✅ Fetch last 500 timestamp entries
        all_logs = logs_ref.order_by_key().limit_to_last(500).get()

        if not all_logs:
            return "⚠ No logs found", 404

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp_key", "zone", "temperature", "humidity", "status", "timestamp"])

        for timestamp_key, zones in all_logs.items():
            for zone, values in zones.items():
                writer.writerow([
                    timestamp_key,
                    zone,
                    values.get("temperature"),
                    values.get("humidity"),
                    values.get("status"),
                    values.get("timestamp"),
                ])

        response = Response(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=logs.csv"
        return response

    except Exception as e:
        return f"❌ Error fetching logs: {str(e)}", 500

# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    # Start simulator in background
    threading.Thread(target=push_data_loop, daemon=True).start()

    # Run Flask app (Render needs this to stay alive)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


"""import os
import time
import random
import datetime
import threading

import firebase_admin
from firebase_admin import credentials, db
from flask import Flask

# -----------------------------
# Firebase Setup
# -----------------------------
cred = credentials.Certificate("/etc/secrets/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://cold-storage-iot-default-rtdb.firebaseio.com/"
})

zones_ref = db.reference("zones")

# -----------------------------
# Thresholds
# -----------------------------
TEMP_MAX = 10
HUMIDITY_MAX = 80

# Initialize previous values for smoother random changes
zone_values = {
    f"zone{i}": {"temperature": random.uniform(5, 10), "humidity": random.uniform(60, 80)}
    for i in range(1, 5)
}

# -----------------------------
# Data Simulator
# -----------------------------
def push_data_loop():
    print("🚀 Simulator started. Pushing data to Firebase...")

    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {}

        for zone, values in zone_values.items():
            # Smooth random variation
            temp = round(values["temperature"] + random.uniform(-1, 1), 2)
            hum = round(values["humidity"] + random.uniform(-1, 1), 2)

            # Keep within reasonable bounds
            temp = max(0, min(15, temp))
            hum = max(50, min(90, hum))

            # Update zone values
            zone_values[zone]["temperature"] = temp
            zone_values[zone]["humidity"] = hum

            # Determine status
            status = "⚠ Out of Range" if temp > TEMP_MAX or hum > HUMIDITY_MAX else "Within Range"

            # Build data dict
            data[zone] = {
                "temperature": temp,
                "humidity": hum,
                "timestamp": now,
                "status": status
            }

        # Push to Firebase
        try:
            zones_ref.set(data)
            print(f"✅ Pushed at {now}:", data)
        except Exception as e:
            print(f"❌ Failed to push data: {e}")

        time.sleep(5)

# -----------------------------
# Flask web server
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Simulator is running and sending zone data to Firebase!"

# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    # Start simulator in background
    threading.Thread(target=push_data_loop, daemon=True).start()

    # Run Flask app (so Render keeps service alive)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)"""

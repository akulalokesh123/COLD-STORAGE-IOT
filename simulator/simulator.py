import os
import time
import random
import datetime
import threading
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask

# -----------------------------
# Load environment variables
# -----------------------------
if os.path.exists(".env"):
    print("Loading .env from project root...")
    load_dotenv(".env")
elif os.path.exists("/etc/secrets/.env"):
    print("Loading .env from /etc/secrets...")
    load_dotenv("/etc/secrets/.env")
else:
    print("⚠️ No .env file found!")

# -----------------------------
# Firebase Setup
# -----------------------------
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
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
})

firebase_admin.initialize_app(firebase_cred, {
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
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
    app.run(host="0.0.0.0", port=port)

import os
import random
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# Load service account from environment variables
service_account = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),  # convert \n into real newlines
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("UNIVERSE_DOMAIN")
}

# Initialize Firebase
cred = credentials.Certificate(service_account)
firebase_admin.initialize_app(cred, {
    "databaseURL": os.getenv("DATABASE_URL")
})

zones_ref = db.reference("zones")

# Thresholds
TEMP_MAX = 10
HUMIDITY_MAX = 80

zone_values = {
    f"zone{i}": {"temperature": random.uniform(5, 10), "humidity": random.uniform(60, 80)}
    for i in range(1, 5)
}

while True:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {}

    for zone, values in zone_values.items():
        temp = round(values["temperature"] + random.uniform(-1, 1), 2)
        hum = round(values["humidity"] + random.uniform(-1, 1), 2)

        temp = max(0, min(15, temp))
        hum = max(50, min(90, hum))

        zone_values[zone]["temperature"] = temp
        zone_values[zone]["humidity"] = hum

        status = "⚠️ Out of Range" if temp > TEMP_MAX or hum > HUMIDITY_MAX else "Within Range"

        data[zone] = {
            "temperature": temp,
            "humidity": hum,
            "timestamp": now,
            "status": status
        }

    zones_ref.set(data)
    print(f"Pushed at {now}:", data)

    time.sleep(5)

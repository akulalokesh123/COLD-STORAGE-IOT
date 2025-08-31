import requests
import csv
import re
import os
import json

# ------------------------
# Config
# ------------------------
API_KEY = os.getenv("RENDER_API_KEY", "rnd_genEnQBuBR3r6bbXwBhXltyYykXH")  # load from env if available
SERVICE_ID = "srv-d2olcla4d50c73a30180"  # replace with your actual service ID
OUTPUT_FILE = "logs1.csv"

# ------------------------
# Fetch logs from Render
# ------------------------
url = f"https://api.render.com/v1/services/{SERVICE_ID}/logs"

headers = {"Authorization": f"Bearer {API_KEY}"}
params = {"limit": 500, "tail": "false"}  # last 500 lines

response = requests.get(url, headers=headers, params=params)

if response.status_code != 200:
    print("❌ Failed to fetch logs:", response.text)
    exit()

logs = response.json().get("logs", [])

# ------------------------
# Parse logs into rows
# ------------------------
rows = []
for entry in logs:
    line = entry.get("message", "")

    # Look for structured JSON inside log line
    match = re.search(r"\{.*\}", line)
    if match:
        try:
            data = json.loads(match.group(0))  # ✅ safe JSON parsing
            row = {}
            for zone, values in data.items():
                for k, v in values.items():
                    row[f"{zone}_{k}"] = v
            rows.append(row)
        except Exception as e:
            print("⚠ Parse error:", e)

# ------------------------
# Save to CSV
# ------------------------
if rows:
    keys = sorted(rows[0].keys())
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Logs saved to {OUTPUT_FILE}")
else:
    print("⚠ No structured data parsed from logs")


// script.js
import { ref, onValue } from "https://www.gstatic.com/firebasejs/9.17.1/firebase-database.js";
import { db } from "./firbase-config.js";

// -------------------------
// Thresholds
// -------------------------
const toggle = document.getElementById("themeToggle");

toggle.addEventListener("change", () => {
  document.body.classList.toggle("dark", toggle.checked);
});

const TEMP_MIN = 0;
const TEMP_MAX = 10;
const HUMIDITY_MAX = 80;

// Store last 10 readings per zone
const recentData = { 1: [], 2: [], 3: [], 4: [] };

// Track alerts and compliance
const alertCountPerZone = { 1: 0, 2: 0, 3: 0, 4: 0 };
const totalReadingsPerZone = { 1: 0, 2: 0, 3: 0, 4: 0 };

// Track consecutive out-of-range readings
const consecutiveAlerts = { 1: 0, 2: 0, 3: 0, 4: 0 };

// -------------------------
// Chart.js Setup
// -------------------------
const tempCtx = document.getElementById("tempChart").getContext("2d");
const humCtx = document.getElementById("humChart").getContext("2d");

const tempChart = new Chart(tempCtx, {
  type: "line",
  data: { labels: [], datasets: [] },
  options: { responsive: true, plugins: { legend: { display: true } } }
});

const humChart = new Chart(humCtx, {
  type: "line",
  data: { labels: [], datasets: [] },
  options: { responsive: true, plugins: { legend: { display: true } } }
});

// -------------------------
// Helper: Update KPIs
// -------------------------
function updateKPIs() {
  let alertCount = 0, totalTemp = 0, totalHum = 0, count = 0;

  for (let i = 1; i <= 4; i++) {
    const data = recentData[i][recentData[i].length - 1];
    if (!data) continue;
    count++;
    totalTemp += data.temperature;
    totalHum += data.humidity;

    if (data.status === "⚠️ Alert") {
      alertCount++;
    }
  }

  document.getElementById("alertCount").innerText = alertCount;
  document.getElementById("avgTemp").innerText = count ? (totalTemp / count).toFixed(1) + " °C" : "No data";
  document.getElementById("avgHum").innerText = count ? (totalHum / count).toFixed(1) + " %" : "No data";

  const totalAlerts = Object.values(alertCountPerZone).reduce((a,b)=>a+b, 0);
  if(document.getElementById("totalAlertFrequency")){
    document.getElementById("totalAlertFrequency").innerText = totalAlerts;
  }
}

// -------------------------
// Helper: Update Charts
// -------------------------

function updateCharts() {
  const labels = recentData[1].map(d => d.timestamp).slice(-10) || [];
  tempChart.data.labels = labels;
  humChart.data.labels = labels;

  tempChart.data.datasets = [];
  humChart.data.datasets = [];

  const zoneColors = { 1: "blue", 2: "green", 3: "orange", 4: "purple" };

  for (let i = 1; i <= 4; i++) {
    const zoneData = recentData[i].slice(-10) || [];
    const latest = zoneData[zoneData.length - 1]; // latest reading

    // check if latest reading is out of range
    const latestAlert = latest &&
      (latest.temperature < TEMP_MIN ||
       latest.temperature > TEMP_MAX ||
       latest.humidity > HUMIDITY_MAX);

    // choose color (red if latest is alert, otherwise fixed color)
    const lineColor = latestAlert ? "red" : zoneColors[i];

    tempChart.data.datasets.push({
      label: `Zone ${i}`,
      data: zoneData.map(d => d.temperature),
      borderColor: lineColor,
      fill: false,
      tension: 0.3
    });

    humChart.data.datasets.push({
      label: `Zone ${i}`,
      data: zoneData.map(d => d.humidity),
      borderColor: lineColor,
      fill: false,
      tension: 0.3
    });
  }

  tempChart.update();
  humChart.update();
}

// -------------------------
// Helper: Update Logs
// -------------------------
function updateLogs(zoneId, val) {
  const tbody = document.querySelector("#logTable tbody");
  const tr = document.createElement("tr");

  tr.innerHTML = `
    <td>Zone ${zoneId}</td>
    <td>${val.temperature} °C</td>
    <td>${val.humidity} %</td>
    <td>${val.status}</td>
    <td>${val.timestamp}</td>
  `;
  tbody.prepend(tr);
  if (tbody.childElementCount > 20) tbody.removeChild(tbody.lastChild);
}

// -------------------------
// Helper: Update Zone Compliance
// -------------------------
function updateZoneCompliance() {
  for (let i = 1; i <= 4; i++) {
    const compliance = totalReadingsPerZone[i] > 0
      ? ((totalReadingsPerZone[i] - alertCountPerZone[i]) / totalReadingsPerZone[i] * 100).toFixed(1)
      : "--";

    const zoneEl = document.getElementById(`zone${i}`);
    const complianceEl = zoneEl.querySelector(".compliance");
    if (complianceEl) {
      complianceEl.innerText = `Compliance: ${compliance}%`;
    } else {
      const p = document.createElement("p");
      p.className = "compliance";
      p.innerText = `Compliance: ${compliance}%`;
      zoneEl.appendChild(p);
    }
  }
}

// -------------------------
// Listen to all zones
// -------------------------
for (let i = 1; i <= 4; i++) {
  const zoneRef = ref(db, `zones/zone${i}`);
  onValue(zoneRef, (snapshot) => {
    const val = snapshot.val();
    const zoneEl = document.getElementById(`zone${i}`);

    if (!val) {
      zoneEl.innerHTML = `
        <h2>Zone ${i}</h2>
        <p class="temperature">No data</p>
        <p class="humidity">No data</p>
        <p class="timestamp">--</p>
        <p class="alert">Status: --</p>
      `;
      return;
    }

    // Track readings
    recentData[i].push(val);
    if (recentData[i].length > 10) recentData[i].shift();

    totalReadingsPerZone[i]++;

    // Check thresholds
    const outOfRange = val.temperature < TEMP_MIN || val.temperature > TEMP_MAX || val.humidity > HUMIDITY_MAX;

    if (outOfRange) {
      consecutiveAlerts[i]++;
    } else {
      consecutiveAlerts[i] = 0; // reset if normal
    }

    // Raise alert only if 3 consecutive out-of-range readings
    let status = "Within Range";
    if (consecutiveAlerts[i] >= 3) {
      status = "⚠️ Alert";
      alertCountPerZone[i]++;
    }

    val.status = status;

    // Update zone card
    zoneEl.innerHTML = `
      <h2>Zone ${i}</h2>
      <p class="temperature">Temperature: ${val.temperature} °C</p>
      <p class="humidity">Humidity: ${val.humidity} %</p>
      <p class="timestamp">${val.timestamp}</p>
      <p class="alert ${status === "⚠️ Alert" ? "out-of-range" : ""}">Status: ${status}</p>
    `;

    // Update compliance
    updateZoneCompliance();

    // Update KPIs, charts, logs
    updateKPIs();
    updateCharts();
    updateLogs(i, val);
  });
}

console.log("Dashboard script.js loaded successfully with 3-consecutive-alert logic!");

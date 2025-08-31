import { ref, onValue, get, query, limitToLast } from "https://www.gstatic.com/firebasejs/9.17.1/firebase-database.js";
import { db } from "./firbase-config.js";

const toggle = document.getElementById("themeToggle");
toggle.addEventListener("change", () => {
  document.body.classList.toggle("dark", toggle.checked);
  localStorage.setItem("theme", toggle.checked ? "dark" : "light");
});

// Apply saved theme on load
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
  toggle.checked = true;
}

// -------------------------
// Thresholds
// -------------------------
const TEMP_MIN = 0, TEMP_MAX = 10, HUMIDITY_MAX = 80;

// -------------------------
// Data Storage
// -------------------------
const recentData = { 1: [], 2: [], 3: [], 4: [] };
const alertCountPerZone = { 1: 0, 2: 0, 3: 0, 4: 0 };
const totalReadingsPerZone = { 1: 0, 2: 0, 3: 0, 4: 0 };
const consecutiveAlerts = { 1: 0, 2: 0, 3: 0, 4: 0 };
let latestValues = { 1: null, 2: null, 3: null, 4: null };

// -------------------------
// Chart.js Setup
// -------------------------
const tempChart = new Chart(document.getElementById("tempChart").getContext("2d"), {
  type: "line",
  data: { labels: [], datasets: [] },
  options: { responsive: true, plugins: { legend: { display: true } }, animation: { duration: 1000 } }
});

const humChart = new Chart(document.getElementById("humChart").getContext("2d"), {
  type: "line",
  data: { labels: [], datasets: [] },
  options: { responsive: true, plugins: { legend: { display: true } }, animation: { duration: 1000 } }
});

// -------------------------
// Helper Functions
// -------------------------
function updateKPIs() {
  let alertCount = 0, totalTemp = 0, totalHum = 0, count = 0;

  for (let i = 1; i <= 4; i++) {
    const data = recentData[i][recentData[i].length - 1];
    if (!data) continue;
    count++;
    totalTemp += data.temperature;
    totalHum += data.humidity;
    if (data.status === "⚠️ Alert") alertCount++;
  }

  document.getElementById("alertCount").innerText = alertCount;
  document.getElementById("avgTemp").innerText = count ? (totalTemp / count).toFixed(1) + " °C" : "--";
  document.getElementById("avgHum").innerText = count ? (totalHum / count).toFixed(1) + " %" : "--";

  const totalAlerts = Object.values(alertCountPerZone).reduce((a, b) => a + b, 0);
  if (document.getElementById("totalAlertFrequency")) document.getElementById("totalAlertFrequency").innerText = totalAlerts;
}

function updateZoneCompliance() {
  for (let i = 1; i <= 4; i++) {
    const compliance = totalReadingsPerZone[i] > 0
      ? ((totalReadingsPerZone[i] - alertCountPerZone[i]) / totalReadingsPerZone[i] * 100).toFixed(1)
      : "--";

    const zoneEl = document.getElementById(`zone${i}`);
    let complianceEl = zoneEl.querySelector(".compliance");
    if (!complianceEl) {
      complianceEl = document.createElement("p");
      complianceEl.className = "compliance";
      zoneEl.appendChild(complianceEl);
    }
    complianceEl.innerText = `Compliance: ${compliance}%`;
  }
}

function updateLogs(zoneId, val) {
  const tbody = document.querySelector("#logTable tbody");
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>Zone ${zoneId}</td>
    <td>${val.temperature.toFixed(2)} °C</td>
    <td>${val.humidity.toFixed(2)} %</td>
    <td>${val.status}</td>
    <td>${val.timestamp}</td>
  `;
  tbody.prepend(tr);
  if (tbody.childElementCount > 20) tbody.removeChild(tbody.lastChild);
}

// -------------------------
// Update Charts every 5 seconds
// -------------------------
setInterval(() => {
  const labels = [];
  const tempDatasets = [];
  const humDatasets = [];
  const zoneColors = { 1: "blue", 2: "green", 3: "orange", 4: "purple" };

  for (let i = 1; i <= 4; i++) {
    const val = latestValues[i];
    if (!val) continue;

    recentData[i].push(val);
    if (recentData[i].length > 5) recentData[i].shift();

    const timestamps = recentData[i].map(d => d.timestamp);
    const tempData = recentData[i].map(d => d.temperature);
    const humData = recentData[i].map(d => d.humidity);

    if (labels.length < timestamps.length) labels.splice(0, labels.length, ...timestamps);

    const alert = val.temperature > TEMP_MAX || val.temperature < TEMP_MIN || val.humidity > HUMIDITY_MAX;
    const color = alert ? "red" : zoneColors[i];

    tempDatasets.push({ label: `Zone ${i}`, data: tempData, borderColor: color, fill: false, tension: 0.4 });
    humDatasets.push({ label: `Zone ${i}`, data: humData, borderColor: color, fill: false, tension: 0.4 });
  }

  tempChart.data.labels = labels;
  tempChart.data.datasets = tempDatasets;
  tempChart.update();

  humChart.data.labels = labels;
  humChart.data.datasets = humDatasets;
  humChart.update();
}, 5000);

// -------------------------
// Firebase listeners
// -------------------------
for (let i = 1; i <= 4; i++) {
  const zoneRef = ref(db, `zones/zone${i}`);
  onValue(zoneRef, snapshot => {
    const val = snapshot.val();
    if (!val) return;

    const outOfRange = val.temperature < TEMP_MIN || val.temperature > TEMP_MAX || val.humidity > HUMIDITY_MAX;
    if (outOfRange) consecutiveAlerts[i]++; else consecutiveAlerts[i] = 0;

    let status = "Within Range";
    if (consecutiveAlerts[i] >= 3) { status = "⚠️ Alert"; alertCountPerZone[i]++; }
    val.status = status;

    totalReadingsPerZone[i]++;
    latestValues[i] = val;  // store for throttled chart updates

    const zoneEl = document.getElementById(`zone${i}`);
    zoneEl.innerHTML = `
      <h2>Zone ${i}</h2>
      <p class="temperature">Temperature: ${val.temperature.toFixed(2)} °C</p>
      <p class="humidity">Humidity: ${val.humidity.toFixed(2)} %</p>
      <p class="timestamp">${val.timestamp}</p>
      <p class="alert ${status === "⚠️ Alert" ? "out-of-range" : ""}">Status: ${status}</p>
    `;

    updateZoneCompliance();
    updateKPIs();
    updateLogs(i, val);
  });
}

// -------------------------
// Download Logs CSV
// -------------------------
window.downloadLogs = async function() {
  try {
    const logsRef = ref(db, "logs");
    const snapshot = await get(query(logsRef, limitToLast(500)));
    if (!snapshot.exists()) { alert("No logs found!"); return; }

    const logs = snapshot.val();
    let csv = "timestamp,zone,temperature,humidity,status\n";

    Object.entries(logs).forEach(([time, zones]) => {
      Object.entries(zones).forEach(([zone, data]) => {
        csv += `${time},${zone},${data.temperature},${data.humidity},${data.status}\n`;
      });
    });

    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "logs.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (err) {
    console.error(err);
    alert("Failed to download logs");
  }
};

console.log("Dashboard script.js loaded successfully with smooth 5-second chart updates!");

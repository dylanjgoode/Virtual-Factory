const state = {
  devices: {},
  traffic: [],
};

const devicesEl = document.getElementById("devices");
const trafficEl = document.getElementById("traffic");
const totalDevicesEl = document.getElementById("total-devices");
const onlineDevicesEl = document.getElementById("online-devices");
const trafficCountEl = document.getElementById("traffic-count");
const commandDeviceEl = document.getElementById("command-device");
const brokerStatusEl = document.getElementById("broker-status");

function setBrokerStatus(text, online) {
  brokerStatusEl.querySelector("span:last-child").textContent = `Broker: ${text}`;
  const dot = brokerStatusEl.querySelector(".dot");
  dot.style.background = online ? "#58c7c1" : "#ffb347";
  dot.style.boxShadow = online ? "0 0 10px rgba(88, 199, 193, 0.8)" : "0 0 8px rgba(255, 179, 71, 0.8)";
}

function updateStats() {
  const devices = Object.values(state.devices);
  totalDevicesEl.textContent = devices.length;
  onlineDevicesEl.textContent = devices.filter((d) => d.status === "online").length;
  trafficCountEl.textContent = state.traffic.length;
}

function renderDeviceOptions() {
  commandDeviceEl.innerHTML = "";
  Object.keys(state.devices).forEach((deviceId) => {
    const option = document.createElement("option");
    option.value = deviceId;
    option.textContent = deviceId;
    commandDeviceEl.appendChild(option);
  });
}

function renderDevices() {
  devicesEl.innerHTML = "";
  const devices = Object.values(state.devices).sort((a, b) => a.device_id.localeCompare(b.device_id));
  devices.forEach((device) => {
    const card = document.createElement("div");
    card.className = `device-card ${device.status === "offline" ? "offline" : ""}`;

    const title = document.createElement("h3");
    title.textContent = device.device_id;

    const meta = document.createElement("div");
    meta.className = "device-meta";
    meta.textContent = `${device.device_type} | state: ${device.state} | status: ${device.status}`;

    const sensors = document.createElement("div");
    sensors.className = "sensor-list";
    const sensorEntries = Object.entries(device.sensors || {});
    if (sensorEntries.length === 0) {
      const empty = document.createElement("div");
      empty.textContent = "No telemetry yet";
      sensors.appendChild(empty);
    } else {
      sensorEntries.forEach(([name, data]) => {
        const row = document.createElement("div");
        row.className = "sensor-item";
        row.innerHTML = `<span>${name}</span><span>${data.value ?? "-"} ${data.unit ?? ""}</span>`;
        sensors.appendChild(row);
      });
    }

    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(sensors);

    if (device.last_alarm) {
      const alarm = document.createElement("div");
      alarm.className = "alarm";
      alarm.textContent = `Alarm: ${device.last_alarm.sensor} ${device.last_alarm.alarm_type} ${device.last_alarm.value}`;
      card.appendChild(alarm);
    }

    devicesEl.appendChild(card);
  });
}

function renderTraffic() {
  trafficEl.innerHTML = "";
  const entries = state.traffic.slice(-60).reverse();
  entries.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "traffic-entry";
    const payloadPreview = entry.payload.length > 140 ? `${entry.payload.slice(0, 140)}...` : entry.payload;
    row.innerHTML = `<div><span class="topic">${entry.topic}</span> qos=${entry.qos} retain=${entry.retain}</div><div>${payloadPreview}</div>`;
    trafficEl.appendChild(row);
  });
}

function applySnapshot(snapshot) {
  state.devices = snapshot.devices || {};
  state.traffic = snapshot.traffic || [];
  renderDeviceOptions();
  renderDevices();
  renderTraffic();
  updateStats();
}

function handleEvent(entry) {
  state.traffic.push(entry);
  if (state.traffic.length > 200) {
    state.traffic.shift();
  }
  renderTraffic();
  updateStats();
}

function handleDevices(devices) {
  state.devices = devices;
  renderDeviceOptions();
  renderDevices();
  updateStats();
}

const wsUrl = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;
const ws = new WebSocket(wsUrl);

ws.addEventListener("open", () => {
  setBrokerStatus("connecting", false);
});

ws.addEventListener("close", () => {
  setBrokerStatus("offline", false);
});

ws.addEventListener("message", (event) => {
  const payload = JSON.parse(event.data);
  if (payload.type === "snapshot") {
    applySnapshot(payload);
  } else if (payload.type === "event") {
    handleEvent(payload.entry);
  } else if (payload.type === "devices") {
    handleDevices(payload.devices);
  } else if (payload.type === "broker") {
    setBrokerStatus(payload.status, payload.status === "connected");
  }
});

const commandForm = document.getElementById("command-form");
commandForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    type: "command",
    device_id: commandDeviceEl.value,
    command: document.getElementById("command-type").value,
    reason: document.getElementById("command-reason").value,
  };
  ws.send(JSON.stringify(payload));
  commandForm.reset();
});

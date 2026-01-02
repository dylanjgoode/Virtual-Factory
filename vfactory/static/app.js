const state = {
  devices: {},
  traffic: [],
  meta: {},
  brokerStatus: "disconnected",
  concepts: {
    qos0: false,
    qos1: false,
    retained: false,
    lwt: false,
    commands: false,
    alarms: false,
  },
  filters: {
    category: "all",
    qos: "any",
    retain: "any",
    text: "",
  },
};

const devicesEl = document.getElementById("devices");
const trafficEl = document.getElementById("traffic");
const totalDevicesEl = document.getElementById("total-devices");
const onlineDevicesEl = document.getElementById("online-devices");
const trafficCountEl = document.getElementById("traffic-count");
const commandDeviceEl = document.getElementById("command-device");
const brokerStatusEl = document.getElementById("broker-status");
const conceptsEl = document.getElementById("concepts");
const brokerMetaEl = document.getElementById("broker-meta");
const guideMetaEl = document.querySelector(".guide-meta");
const filterCategoryEl = document.getElementById("filter-category");
const filterQosEl = document.getElementById("filter-qos");
const filterRetainEl = document.getElementById("filter-retain");
const filterTextEl = document.getElementById("filter-text");

function replaceTemplate(text) {
  return text
    .replaceAll("{base_topic}", state.meta.base_topic || "factory")
    .replaceAll("{broker_port}", state.meta.broker_port || "1883");
}

function brokerSuffix() {
  if (!state.meta.broker_host || !state.meta.broker_port) {
    return "";
  }
  return ` (${state.meta.broker_host}:${state.meta.broker_port})`;
}

function setBrokerStatus(text, online) {
  brokerStatusEl.querySelector("span:last-child").textContent = `Broker: ${text}${brokerSuffix()}`;
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

function topicCategory(topic) {
  const parts = topic.split("/");
  if (state.meta.base_topic && parts[0] === state.meta.base_topic) {
    return parts[1] || "";
  }
  return parts[0] || "";
}

function renderConcepts() {
  if (!conceptsEl) {
    return;
  }
  conceptsEl.querySelectorAll("[data-concept]").forEach((el) => {
    const key = el.getAttribute("data-concept");
    if (state.concepts[key]) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });
}

function renderMeta() {
  if (!brokerMetaEl) {
    return;
  }
  const base = state.meta.base_topic || "--";
  const host = state.meta.broker_host || "--";
  const port = state.meta.broker_port || "--";
  brokerMetaEl.textContent = `Base topic: ${base} | Broker: ${host}:${port}`;
}

function renderGuideMeta() {
  if (!guideMetaEl) {
    return;
  }
  const template = guideMetaEl.getAttribute("data-template") || guideMetaEl.textContent;
  guideMetaEl.textContent = replaceTemplate(template);
}

function updateConcepts(entry) {
  if (entry.qos === 0) {
    state.concepts.qos0 = true;
  }
  if (entry.qos === 1) {
    state.concepts.qos1 = true;
  }
  if (entry.retain) {
    state.concepts.retained = true;
  }
  const category = topicCategory(entry.topic);
  if (category === "status") {
    state.concepts.lwt = true;
  }
  if (category === "commands") {
    state.concepts.commands = true;
  }
  if (category === "alarms") {
    state.concepts.alarms = true;
  }
}

function renderExercises() {
  document.querySelectorAll(".exercise-code[data-template]").forEach((codeEl) => {
    const template = codeEl.getAttribute("data-template");
    const command = replaceTemplate(template);
    codeEl.textContent = command;
    const button = codeEl.parentElement?.parentElement?.querySelector("[data-copy]");
    if (button) {
      button.setAttribute("data-copy", command);
    }
  });
}

function renderTooltips() {
  document.querySelectorAll("[data-tooltip]").forEach((el) => {
    const template = el.getAttribute("data-tooltip");
    if (!template) {
      return;
    }
    el.setAttribute("data-tooltip", replaceTemplate(template));
  });
}

function applyFilters(entries) {
  const text = state.filters.text.toLowerCase();
  return entries.filter((entry) => {
    if (state.filters.category !== "all") {
      const category = topicCategory(entry.topic);
      if (category !== state.filters.category) {
        return false;
      }
    }
    if (state.filters.qos !== "any" && String(entry.qos) !== state.filters.qos) {
      return false;
    }
    if (state.filters.retain !== "any") {
      const wantRetained = state.filters.retain === "retained";
      if (Boolean(entry.retain) !== wantRetained) {
        return false;
      }
    }
    if (text && !entry.topic.toLowerCase().includes(text) && !entry.payload.toLowerCase().includes(text)) {
      return false;
    }
    return true;
  });
}

function setupFilters() {
  if (!filterCategoryEl) {
    return;
  }
  const update = () => {
    state.filters.category = filterCategoryEl.value;
    state.filters.qos = filterQosEl.value;
    state.filters.retain = filterRetainEl.value;
    state.filters.text = filterTextEl.value.trim();
    renderTraffic();
  };
  filterCategoryEl.addEventListener("change", update);
  filterQosEl.addEventListener("change", update);
  filterRetainEl.addEventListener("change", update);
  filterTextEl.addEventListener("input", update);
}

function setupCopyButtons() {
  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const text = button.getAttribute("data-copy");
      if (!text) {
        return;
      }
      try {
        await navigator.clipboard.writeText(text);
      } catch (error) {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      button.classList.add("copied");
      button.textContent = "Copied";
      setTimeout(() => {
        button.classList.remove("copied");
        button.textContent = "Copy";
      }, 1600);
    });
  });
}

function setupTabs() {
  const tabs = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll(".tab-panel");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");
      tabs.forEach((btn) => {
        const active = btn === tab;
        btn.classList.toggle("active", active);
        btn.setAttribute("aria-selected", active ? "true" : "false");
      });
      panels.forEach((panel) => {
        panel.classList.toggle("active", panel.getAttribute("data-panel") === target);
      });
    });
  });
}

function setupSubTabs() {
  document.querySelectorAll(".subtabs").forEach((groupEl) => {
    const groupName = groupEl.getAttribute("data-tab-group");
    if (!groupName) {
      return;
    }
    const panelsContainer = document.querySelector(`.subtab-panels[data-tab-group="${groupName}"]`);
    if (!panelsContainer) {
      return;
    }
    const tabs = groupEl.querySelectorAll(".subtab");
    const panels = panelsContainer.querySelectorAll(".subtab-panel");
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const target = tab.getAttribute("data-subtab");
        tabs.forEach((btn) => {
          const active = btn === tab;
          btn.classList.toggle("active", active);
          btn.setAttribute("aria-selected", active ? "true" : "false");
        });
        panels.forEach((panel) => {
          panel.classList.toggle("active", panel.getAttribute("data-subpanel") === target);
        });
      });
    });
  });
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
  const entries = applyFilters(state.traffic).slice(-60).reverse();
  entries.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "traffic-entry";
    const payloadPreview = entry.payload.length > 140 ? `${entry.payload.slice(0, 140)}...` : entry.payload;
    const category = topicCategory(entry.topic);
    row.innerHTML = `<div><span class="topic">${entry.topic}</span> <span class="meta-chip">${category}</span> qos=${entry.qos} retain=${entry.retain}</div><div>${payloadPreview}</div>`;
    trafficEl.appendChild(row);
  });
}

function applySnapshot(snapshot) {
  state.devices = snapshot.devices || {};
  state.traffic = snapshot.traffic || [];
  state.meta = snapshot.meta || {};
  state.brokerStatus = snapshot.broker_status || "disconnected";
  state.concepts = {
    qos0: false,
    qos1: false,
    retained: false,
    lwt: false,
    commands: false,
    alarms: false,
  };
  state.traffic.forEach(updateConcepts);
  renderDeviceOptions();
  renderDevices();
  renderTraffic();
  updateStats();
  renderMeta();
  renderGuideMeta();
  renderExercises();
  renderTooltips();
  renderConcepts();
  setBrokerStatus(state.brokerStatus, state.brokerStatus === "connected");
}

function handleEvent(entry) {
  state.traffic.push(entry);
  if (state.traffic.length > 200) {
    state.traffic.shift();
  }
  updateConcepts(entry);
  renderTraffic();
  updateStats();
  renderConcepts();
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
  setBrokerStatus("ws connected", false);
});

ws.addEventListener("close", () => {
  setBrokerStatus("ws disconnected", false);
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
    state.brokerStatus = payload.status;
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

setupFilters();
setupCopyButtons();
setupTabs();
setupSubTabs();

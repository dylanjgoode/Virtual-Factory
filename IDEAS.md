## Story Time:

Tour of the factory - flow animated video, this is the factory floor, this is the user, these are the machines, this is what they do, this is why it's important to instrument telemetry data, this is why we use MQTT sometimes.

## Feature ideas

  - Device drill‑down panel with sensor history sparklines and last‑updated timestamps, plus a command log per device.
  - Scenario controls in the UI: simulate faults, change telemetry rate, or force offline/LWT without CLI.
  Questions / assumptions

  ## Improvements
  - High: Broker connectivity is ambiguous: UI shows “ws connected” even when the broker is down, and the command form stays
    active with no error feedback. Suggest gating the form on broker status and adding a failure toast or inline error. vfactory/
    static/app.js
  - Medium: UI templates default to port 1883, but your project defaults to 1884, so initial command examples can be wrong before
    meta arrives. Suggest defaulting to 1884 or showing “—” until the snapshot arrives. vfactory/static/app.js
  - Medium: Empty states are silent. Devices/traffic panes render blank until data arrives, which looks broken. Suggest explicit
    empty-state copy and a “Start the sandbox” CTA. vfactory/static/index.html, vfactory/static/app.js
  - Medium: Tooltip content is CSS-only (::after) and not screen-reader friendly; also small touch target. Suggest a real tooltip

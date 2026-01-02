import argparse
import asyncio
import json
import pathlib
from collections import deque

from aiohttp import web

from vfactory.common import QOS_COMMAND, connect, create_client, json_dumps, log, now_ts, topic


STATIC_DIR = pathlib.Path(__file__).parent / "static"


class DashboardState:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.devices: dict[str, dict] = {}
        self.traffic = deque(maxlen=200)
        self.websockets: set[web.WebSocketResponse] = set()
        self.mqtt = None

    def update_device(self, device_id: str) -> dict:
        device = self.devices.get(device_id)
        if not device:
            device = {
                "device_id": device_id,
                "device_type": "unknown",
                "status": "unknown",
                "state": "unknown",
                "sensors": {},
                "last_alarm": None,
                "last_seen": None,
            }
            self.devices[device_id] = device
        return device

    def record_traffic(self, entry: dict) -> None:
        self.traffic.append(entry)

    def snapshot(self) -> dict:
        return {
            "type": "snapshot",
            "devices": self.devices,
            "traffic": list(self.traffic),
        }

    async def broadcast(self, payload: dict) -> None:
        if not self.websockets:
            return
        dead = set()
        for ws in self.websockets:
            try:
                await ws.send_str(json.dumps(payload))
            except ConnectionResetError:
                dead.add(ws)
        for ws in dead:
            self.websockets.discard(ws)


async def index(_request: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC_DIR / "index.html")


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    state: DashboardState = request.app["state"]
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)

    state.websockets.add(ws)
    await ws.send_str(json.dumps(state.snapshot()))

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                payload = json.loads(msg.data)
            except json.JSONDecodeError:
                continue
            if payload.get("type") == "command":
                device_id = payload.get("device_id")
                command = payload.get("command")
                if device_id and command:
                    command_payload = {
                        "command": command,
                        "device_id": device_id,
                        "reason": payload.get("reason", "dashboard"),
                        "ts": now_ts(),
                    }
                    state.mqtt.publish(
                        topic(f"commands/dashboard/{device_id}"),
                        json_dumps(command_payload),
                        qos=QOS_COMMAND,
                        retain=False,
                    )
        elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.ERROR):
            break

    state.websockets.discard(ws)
    return ws


def start_mqtt(state: DashboardState) -> None:
    client = create_client(client_id="dashboard", clean_session=True)
    state.mqtt = client

    def on_connect(_client, _userdata, _flags, rc):
        if rc == 0:
            log("dashboard", "connected")
            client.subscribe(topic("#"), qos=1)
            asyncio.run_coroutine_threadsafe(
                state.broadcast({"type": "broker", "status": "connected"}), state.loop
            )
        else:
            log("dashboard", f"connect failed rc={rc}")

    def on_message(_client, _userdata, msg):
        entry = {
            "ts": now_ts(),
            "topic": msg.topic,
            "qos": msg.qos,
            "retain": msg.retain,
            "payload": msg.payload.decode("utf-8", errors="replace"),
        }
        try:
            payload = json.loads(entry["payload"])
        except json.JSONDecodeError:
            payload = None

        parts = msg.topic.split("/")
        if len(parts) >= 3:
            category = parts[1]
            if category == "commands" and len(parts) >= 4:
                device_id = parts[3]
            else:
                device_id = parts[2]
            device = state.update_device(device_id)
            device["last_seen"] = entry["ts"]
            if payload and isinstance(payload, dict):
                device["device_type"] = payload.get("device_type", device.get("device_type"))
                if category == "status":
                    device["status"] = payload.get("status", device.get("status"))
                elif category == "state":
                    device["state"] = payload.get("state", device.get("state"))
                elif category == "telemetry" and len(parts) >= 4:
                    sensor = parts[3]
                    device["sensors"][sensor] = {
                        "value": payload.get("value"),
                        "unit": payload.get("unit"),
                        "ts": payload.get("ts"),
                    }
                elif category == "alarms":
                    device["last_alarm"] = payload

        state.record_traffic(entry)
        asyncio.run_coroutine_threadsafe(state.broadcast({"type": "event", "entry": entry}), state.loop)
        asyncio.run_coroutine_threadsafe(state.broadcast({"type": "devices", "devices": state.devices}), state.loop)

    def on_disconnect(_client, _userdata, rc):
        if rc != 0:
            log("dashboard", f"disconnected rc={rc}")
        asyncio.run_coroutine_threadsafe(
            state.broadcast({"type": "broker", "status": "disconnected"}), state.loop
        )

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    connect(client)
    client.loop_start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Virtual Factory dashboard")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    state = DashboardState(loop)
    start_mqtt(state)

    app = web.Application()
    app["state"] = state
    app.router.add_get("/", index)
    app.router.add_get("/ws", ws_handler)
    app.router.add_static("/static", STATIC_DIR)
    async def on_cleanup(app: web.Application) -> None:
        mqtt_client = app["state"].mqtt
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

    app.on_cleanup.append(on_cleanup)

    log("dashboard", f"serving on http://{args.host}:{args.port}")
    web.run_app(app, host=args.host, port=args.port, loop=loop)


if __name__ == "__main__":
    main()

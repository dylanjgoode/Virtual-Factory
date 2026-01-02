import argparse
import json
import os
import random
import time

from vfactory.common import (
    QOS_ALARM,
    QOS_COMMAND,
    QOS_STATE,
    QOS_STATUS,
    QOS_TELEMETRY,
    connect,
    create_client,
    json_dumps,
    log,
    now_ts,
    topic,
)
from vfactory.sim_config import ENV_STATION, MACHINES


STATE_OPTIONS = ["running", "idle", "maintenance"]


def pick_state(current: str) -> str:
    weights = {
        "running": 0.65,
        "idle": 0.25,
        "maintenance": 0.1,
    }
    if current == "maintenance":
        weights["maintenance"] = 0.25
        weights["running"] = 0.5
    roll = random.random()
    cumulative = 0.0
    for state, weight in weights.items():
        cumulative += weight
        if roll <= cumulative:
            return state
    return current


def simulate_value(sensor: dict, anomaly: bool) -> float:
    value = random.gauss(sensor["base"], sensor["variance"])
    if anomaly and random.random() < 0.06:
        if "alarm_high" in sensor:
            value = sensor["alarm_high"] + random.uniform(1.0, 6.0)
        elif "alarm_low" in sensor:
            value = sensor["alarm_low"] - random.uniform(1.0, 6.0)
    return round(max(value, 0.0), 2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Virtual Factory device simulator")
    parser.add_argument("--device", required=True, help="Device id (e.g., conveyor, robot_arm, press, env_station)")
    parser.add_argument("--crash-after", type=float, default=None, help="Crash after N seconds to trigger LWT")
    parser.add_argument("--anomaly", action="store_true", help="Enable random sensor anomalies")
    args = parser.parse_args()

    if args.device == ENV_STATION["device_id"]:
        config = ENV_STATION
    else:
        config = MACHINES.get(args.device)

    if not config:
        raise SystemExit(f"Unknown device: {args.device}")

    device_id = args.device
    sensors = config["sensors"]
    interval = config.get("interval", 1.5)
    state_interval = config.get("state_interval", 10.0)
    device_type = config.get("type", "environment")

    status_topic = topic(f"status/{device_id}")
    lwt_payload = {"device_id": device_id, "status": "offline", "ts": now_ts()}

    client = create_client(
        client_id=device_id,
        clean_session=True,
        lwt_topic=status_topic,
        lwt_payload=lwt_payload,
        lwt_qos=QOS_STATUS,
        lwt_retain=True,
    )

    state = "running"
    seq = 0

    def publish_state() -> None:
        payload = {
            "device_id": device_id,
            "device_type": device_type,
            "state": state,
            "ts": now_ts(),
        }
        client.publish(topic(f"state/{device_id}"), json_dumps(payload), qos=QOS_STATE, retain=True)

    def on_connect(_client, _userdata, _flags, rc):
        if rc == 0:
            log(device_id, "connected")
            client.subscribe(topic(f"commands/controller/{device_id}"), qos=QOS_COMMAND)
            client.subscribe(topic(f"commands/dashboard/{device_id}"), qos=QOS_COMMAND)
            online_payload = {"device_id": device_id, "status": "online", "ts": now_ts()}
            client.publish(status_topic, json_dumps(online_payload), qos=QOS_STATUS, retain=True)
            publish_state()
        else:
            log(device_id, f"connect failed rc={rc}")

    def on_message(_client, _userdata, msg):
        nonlocal state
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {"raw": msg.payload.decode("utf-8", errors="replace")}

        command = payload.get("command")
        if command == "stop":
            state = "idle"
        elif command == "start":
            state = "running"
        elif command == "maintenance":
            state = "maintenance"
        log(device_id, f"command {command} from {msg.topic}")
        publish_state()

    client.on_connect = on_connect
    client.on_message = on_message

    connect(client)
    client.loop_start()

    last_state = time.time()
    last_telemetry = time.time()
    start_time = time.time()

    try:
        while True:
            now = time.time()

            if now - last_state >= state_interval:
                state = pick_state(state)
                publish_state()
                last_state = now

            if now - last_telemetry >= interval:
                for sensor in sensors:
                    seq += 1
                    value = simulate_value(sensor, args.anomaly)
                    payload = {
                        "device_id": device_id,
                        "device_type": device_type,
                        "sensor": sensor["name"],
                        "unit": sensor["unit"],
                        "value": value,
                        "seq": seq,
                        "ts": now_ts(),
                    }
                    client.publish(
                        topic(f"telemetry/{device_id}/{sensor['name']}"),
                        json_dumps(payload),
                        qos=QOS_TELEMETRY,
                        retain=False,
                    )

                    alarm_high = sensor.get("alarm_high")
                    alarm_low = sensor.get("alarm_low")
                    alarm = None
                    if alarm_high is not None and value >= alarm_high:
                        alarm = {"limit": alarm_high, "type": "high"}
                    elif alarm_low is not None and value <= alarm_low:
                        alarm = {"limit": alarm_low, "type": "low"}

                    if alarm:
                        alarm_payload = {
                            "device_id": device_id,
                            "device_type": device_type,
                            "sensor": sensor["name"],
                            "unit": sensor["unit"],
                            "value": value,
                            "limit": alarm["limit"],
                            "alarm_type": alarm["type"],
                            "severity": "warning",
                            "ts": now_ts(),
                        }
                        client.publish(
                            topic(f"alarms/{device_id}/{sensor['name']}"),
                            json_dumps(alarm_payload),
                            qos=QOS_ALARM,
                            retain=False,
                        )

                last_telemetry = now

            if args.crash_after and now - start_time >= args.crash_after:
                log(device_id, "simulating crash")
                os._exit(1)

            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        log(device_id, "shutdown")


if __name__ == "__main__":
    main()

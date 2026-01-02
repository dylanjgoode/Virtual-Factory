import argparse
import json
import time

from vfactory.common import (
    QOS_COMMAND,
    connect,
    create_client,
    json_dumps,
    log,
    now_ts,
    topic,
)


def choose_command(alarm: dict) -> tuple[str, str]:
    sensor = alarm.get("sensor")
    alarm_type = alarm.get("alarm_type")
    if alarm_type == "high" and sensor in {"temperature", "pressure", "current"}:
        return "stop", "critical threshold"
    if alarm_type == "low":
        return "maintenance", "low threshold"
    return "maintenance", "alarm triggered"


def main() -> None:
    parser = argparse.ArgumentParser(description="Virtual Factory central controller")
    parser.add_argument("--session", choices=["clean", "persistent"], default="clean")
    parser.add_argument("--client-id", default="controller")
    args = parser.parse_args()

    clean_session = args.session == "clean"
    client = create_client(client_id=args.client_id, clean_session=clean_session)

    command_seq = 0

    def on_connect(_client, _userdata, flags, rc):
        if rc == 0:
            session_present = flags.get("session present") or flags.get("session_present")
            log("controller", f"connected (session_present={session_present})")
            client.subscribe(topic("telemetry/#"), qos=1)
            client.subscribe(topic("alarms/#"), qos=1)
            client.subscribe(topic("status/#"), qos=1)
            client.subscribe(topic("state/#"), qos=1)
        else:
            log("controller", f"connect failed rc={rc}")

    def on_message(_client, _userdata, msg):
        nonlocal command_seq
        if msg.topic.startswith(topic("alarms/")):
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
            except json.JSONDecodeError:
                log("controller", "invalid alarm payload")
                return

            device_id = payload.get("device_id")
            command, reason = choose_command(payload)
            command_seq += 1
            command_payload = {
                "command": command,
                "reason": reason,
                "command_id": command_seq,
                "device_id": device_id,
                "ts": now_ts(),
            }
            command_topic = topic(f"commands/controller/{device_id}")
            client.publish(command_topic, json_dumps(command_payload), qos=QOS_COMMAND, retain=False)
            log("controller", f"sent {command} to {device_id} ({payload.get('sensor')})")
        elif msg.topic.startswith(topic("status/")):
            log("controller", f"status {msg.payload.decode('utf-8', errors='replace')}")
        elif msg.topic.startswith(topic("state/")):
            log("controller", f"state {msg.payload.decode('utf-8', errors='replace')}")

    client.on_connect = on_connect
    client.on_message = on_message

    connect(client)
    client.loop_start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        log("controller", "shutdown")


if __name__ == "__main__":
    main()

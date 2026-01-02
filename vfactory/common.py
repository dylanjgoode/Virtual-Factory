import json
import os
from datetime import datetime

import paho.mqtt.client as mqtt

BASE_TOPIC = os.getenv("VF_BASE_TOPIC", "factory")
BROKER_HOST = os.getenv("VF_BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("VF_BROKER_PORT", "1883"))
KEEPALIVE = int(os.getenv("VF_KEEPALIVE", "30"))

QOS_TELEMETRY = 0
QOS_ALARM = 1
QOS_STATE = 1
QOS_STATUS = 1
QOS_COMMAND = 1


def now_ts() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def topic(path: str) -> str:
    return f"{BASE_TOPIC}/{path}"


def json_dumps(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"))


def log(prefix: str, message: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {prefix}: {message}", flush=True)


def create_client(
    client_id: str,
    clean_session: bool = True,
    lwt_topic: str | None = None,
    lwt_payload: dict | None = None,
    lwt_qos: int = QOS_STATUS,
    lwt_retain: bool = True,
) -> mqtt.Client:
    client = mqtt.Client(client_id=client_id, clean_session=clean_session, protocol=mqtt.MQTTv311)
    if lwt_topic and lwt_payload is not None:
        client.will_set(lwt_topic, payload=json_dumps(lwt_payload), qos=lwt_qos, retain=lwt_retain)
    return client


def connect(client: mqtt.Client) -> None:
    client.connect(BROKER_HOST, BROKER_PORT, KEEPALIVE)

import argparse
import time

from vfactory.common import connect, create_client, log, topic


UNAUTHORIZED_PUB = topic("commands/controller/press")
UNAUTHORIZED_SUB = topic("admin/#")


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger ACL rejections")
    parser.add_argument("--mode", choices=["pub", "sub", "both"], default="both")
    args = parser.parse_args()

    client = create_client(client_id="intruder", clean_session=True)

    def on_connect(_client, _userdata, _flags, rc):
        if rc != 0:
            log("intruder", f"connect failed rc={rc}")
            return

        if args.mode in {"pub", "both"}:
            info = client.publish(UNAUTHORIZED_PUB, "{\"command\":\"stop\"}", qos=1)
            if info.rc != 0:
                log("intruder", f"publish rejected rc={info.rc}")
            else:
                log("intruder", f"publish attempted to {UNAUTHORIZED_PUB}")

        if args.mode in {"sub", "both"}:
            rc, _mid = client.subscribe(UNAUTHORIZED_SUB, qos=1)
            if rc != 0:
                log("intruder", f"subscribe rejected rc={rc}")
            else:
                log("intruder", f"subscribe attempted to {UNAUTHORIZED_SUB}")

    def on_subscribe(_client, _userdata, _mid, granted_qos):
        if 128 in granted_qos:
            log("intruder", "broker rejected subscription (granted_qos=128)")

    def on_disconnect(_client, _userdata, rc):
        if rc != 0:
            log("intruder", f"disconnected rc={rc}")

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_disconnect = on_disconnect

    connect(client)
    client.loop_start()

    try:
        time.sleep(2.0)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

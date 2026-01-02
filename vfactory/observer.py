import argparse
import time

from vfactory.common import connect, create_client, log, topic


def main() -> None:
    parser = argparse.ArgumentParser(description="MQTT traffic observer")
    parser.add_argument("--client-id", default="observer")
    parser.add_argument("--topic", default=topic("#"))
    parser.add_argument("--qos", type=int, default=1)
    args = parser.parse_args()

    client = create_client(client_id=args.client_id, clean_session=True)

    def on_connect(_client, _userdata, _flags, rc):
        if rc == 0:
            log("observer", "connected")
            client.subscribe(args.topic, qos=args.qos)
        else:
            log("observer", f"connect failed rc={rc}")

    def on_message(_client, _userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        log("observer", f"{msg.topic} qos={msg.qos} retain={msg.retain} {payload}")

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
        log("observer", "shutdown")


if __name__ == "__main__":
    main()

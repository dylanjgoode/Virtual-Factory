import argparse
import json
import sys
import time

from vfactory.common import connect, create_client, log


def publish(args: argparse.Namespace) -> None:
    client = create_client(client_id=args.client_id, clean_session=True)

    def on_connect(_client, _userdata, _flags, rc):
        if rc != 0:
            log("cli", f"connect failed rc={rc}")
            return
        payload = args.message
        if args.json:
            payload = json.dumps(json.loads(args.message))
        info = client.publish(args.topic, payload, qos=args.qos, retain=args.retain)
        if info.rc != 0:
            log("cli", f"publish error rc={info.rc}")
        else:
            log("cli", f"published to {args.topic}")
        client.disconnect()

    client.on_connect = on_connect
    connect(client)
    client.loop_forever()


def subscribe(args: argparse.Namespace) -> None:
    client = create_client(client_id=args.client_id, clean_session=True)

    def on_connect(_client, _userdata, _flags, rc):
        if rc == 0:
            log("cli", f"subscribing {args.topic}")
            client.subscribe(args.topic, qos=args.qos)
        else:
            log("cli", f"connect failed rc={rc}")

    def on_message(_client, _userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        log("cli", f"{msg.topic} qos={msg.qos} retain={msg.retain} {payload}")

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


def main() -> None:
    parser = argparse.ArgumentParser(description="MQTT CLI helper")
    subparsers = parser.add_subparsers(dest="command")

    pub_parser = subparsers.add_parser("pub", help="Publish a message")
    pub_parser.add_argument("--topic", required=True)
    pub_parser.add_argument("--message", required=True)
    pub_parser.add_argument("--qos", type=int, default=0)
    pub_parser.add_argument("--retain", action="store_true")
    pub_parser.add_argument("--json", action="store_true", help="Validate message as JSON")
    pub_parser.add_argument("--client-id", default="cli-pub")
    pub_parser.set_defaults(func=publish)

    sub_parser = subparsers.add_parser("sub", help="Subscribe to a topic")
    sub_parser.add_argument("--topic", required=True)
    sub_parser.add_argument("--qos", type=int, default=0)
    sub_parser.add_argument("--client-id", default="cli-sub")
    sub_parser.set_defaults(func=subscribe)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

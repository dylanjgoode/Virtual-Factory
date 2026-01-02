import argparse
import os
import signal
import subprocess
import sys
import time


DEVICES = ["conveyor", "robot_arm", "press", "env_station"]


def start_process(name: str, args: list[str]) -> subprocess.Popen:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen(args, env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Virtual Factory sandbox")
    parser.add_argument("--anomaly", action="store_true", help="Enable sensor anomaly injection")
    parser.add_argument("--controller-session", choices=["clean", "persistent"], default="clean")
    parser.add_argument("--no-dashboard", action="store_true")
    parser.add_argument("--no-observer", action="store_true")
    args = parser.parse_args()

    processes = []

    for device in DEVICES:
        cmd = [sys.executable, "-m", "vfactory.device", "--device", device]
        if args.anomaly:
            cmd.append("--anomaly")
        processes.append((device, start_process(device, cmd)))

    controller_cmd = [
        sys.executable,
        "-m",
        "vfactory.controller",
        "--session",
        args.controller_session,
    ]
    processes.append(("controller", start_process("controller", controller_cmd)))

    if not args.no_observer:
        observer_cmd = [sys.executable, "-m", "vfactory.observer"]
        processes.append(("observer", start_process("observer", observer_cmd)))

    if not args.no_dashboard:
        dashboard_cmd = [sys.executable, "-m", "vfactory.dashboard"]
        processes.append(("dashboard", start_process("dashboard", dashboard_cmd)))

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for name, proc in processes:
            proc.send_signal(signal.SIGINT)
        time.sleep(1.0)
        for name, proc in processes:
            if proc.poll() is None:
                proc.terminate()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()

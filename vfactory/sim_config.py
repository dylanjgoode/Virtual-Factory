MACHINES = {
    "conveyor": {
        "type": "conveyor",
        "interval": 1.2,
        "state_interval": 10.0,
        "sensors": [
            {"name": "temperature", "unit": "C", "base": 42.0, "variance": 2.5, "alarm_high": 65.0},
            {"name": "vibration", "unit": "mm/s", "base": 2.1, "variance": 0.4, "alarm_high": 4.5},
            {"name": "current", "unit": "A", "base": 9.5, "variance": 1.3, "alarm_high": 15.0},
        ],
    },
    "robot_arm": {
        "type": "robot_arm",
        "interval": 1.0,
        "state_interval": 12.0,
        "sensors": [
            {"name": "temperature", "unit": "C", "base": 48.0, "variance": 3.0, "alarm_high": 72.0},
            {"name": "vibration", "unit": "mm/s", "base": 1.6, "variance": 0.3, "alarm_high": 3.8},
            {"name": "current", "unit": "A", "base": 12.0, "variance": 1.5, "alarm_high": 18.0},
            {"name": "torque", "unit": "Nm", "base": 35.0, "variance": 4.0, "alarm_high": 55.0},
        ],
    },
    "press": {
        "type": "press",
        "interval": 1.5,
        "state_interval": 9.0,
        "sensors": [
            {"name": "pressure", "unit": "bar", "base": 120.0, "variance": 6.0, "alarm_high": 150.0},
            {"name": "temperature", "unit": "C", "base": 55.0, "variance": 3.5, "alarm_high": 80.0},
            {"name": "vibration", "unit": "mm/s", "base": 2.4, "variance": 0.5, "alarm_high": 5.0},
        ],
    },
}

ENV_STATION = {
    "device_id": "env_station",
    "interval": 2.0,
    "state_interval": 15.0,
    "sensors": [
        {"name": "ambient_temp", "unit": "C", "base": 23.0, "variance": 1.0, "alarm_high": 30.0},
        {"name": "humidity", "unit": "%", "base": 45.0, "variance": 5.0, "alarm_high": 65.0, "alarm_low": 25.0},
        {"name": "air_quality", "unit": "AQI", "base": 35.0, "variance": 6.0, "alarm_high": 80.0},
        {"name": "noise", "unit": "dB", "base": 58.0, "variance": 4.0, "alarm_high": 75.0},
    ],
}

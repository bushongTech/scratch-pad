import json
import yaml
import time
import socket
import argparse
from loguru import logger
from common.message_broker import BrokerType, MessageBroker

# Template message structure
TemplateData = {
    "Source": "MainControl",
    "Time Stamp": 0,
    "Data": {}
}

# Read directives (optional future feature)
def directives():
    msg = MessageBroker.receive(
        topic="translator-udp-dir", broker_type=BrokerType.LAVINMQ
    )
    if msg is None:
        return

    if isinstance(msg, str):
        try:
            incoming_data = json.loads(msg)
            logger.info(f"Received directive: {incoming_data}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON directive: {msg}")
    elif isinstance(msg, dict):
        logger.info(f"Received directive: {msg}")
    else:
        logger.error(f"Unexpected directive type: {type(msg)}")


# Read commands and send them to LabVIEW
def commands():
    msg = MessageBroker.receive(
        topic="translator-udp", broker_type=BrokerType.LAVINMQ
    )
    if msg is None:
        return

    if isinstance(msg, str):
        try:
            incoming_data = json.loads(msg)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON command: {msg}")
            return
    elif isinstance(msg, dict):
        incoming_data = msg
    else:
        logger.error(f"Unexpected command type: {type(msg)}")
        return

    if incoming_data.get("Source") == "Synnax Console":
        TemplateData["Time Stamp"] = time.time_ns()
        TemplateData["Data"] = incoming_data["Data"]
        message = json.dumps(TemplateData).encode("utf-8")
        sock.sendto(message, (config["DeviceIP"], config["DevicePortRx"]))
        logger.info(f"COMMAND Sent: {TemplateData} -> {config['DeviceIP']}:{config['DevicePortRx']}")


# Start of script
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to config YAML", default="/config/daqcon.yaml")
    args = parser.parse_args()

    # Load config
    try:
        with open(args.config, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        logger.info(f"Loaded config from {args.config}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

    # Start message broker
    MessageBroker(config_file_path="/config/message_broker_config.yaml")

    # Open UDP socket for incoming telemetry
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", config["DevicePortTx"]))
    sock.settimeout(10)
    logger.info(f"Listening for UDP on 0.0.0.0:{config['DevicePortTx']}")

    while True:
        # Receive telemetry from LabVIEW
        try:
            data, address = sock.recvfrom(8046)
            incoming_udp = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error(f"Invalid UDP JSON: {data}")
            continue

        TemplateData["Time Stamp"] = time.time_ns()
        try:
            # Filter out NaNs or invalid packets if necessary
            if all(k in incoming_udp["Data"] for k in ["NC_OH_10MIN", "NC_OH_1MIN", "NC_OH_5MIN"]):
                for k in ["NC_OH_10MIN", "NC_OH_1MIN", "NC_OH_5MIN"]:
                    incoming_udp["Data"][k] = incoming_udp["Data"].get(k, 0) or 0
                TemplateData["Data"] = incoming_udp["Data"]
                message = json.dumps(TemplateData)
                MessageBroker.send(
                    topic="TLM", message=message, broker_type=BrokerType.LAVINMQ
                )
                logger.info(f"SOCKET: Sent to TLM -> {message}")
        except Exception as e:
            logger.error(f"Invalid data from LabVIEW: {incoming_udp} | {e}")

        # Handle any commands from CMD_BC -> LabVIEW
        commands()
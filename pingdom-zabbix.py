#!/usr/bin/env python3

import json
import os
import logging
import sys
from typing import Optional, TypedDict

import requests
from zabbix_utils import ItemValue, Sender

PINGDOM_API_URL = os.environ.get("PINGDOM_API_URL", "https://api.pingdom.com/api/3.1/checks")
PINGDOM_API_TOKEN = os.environ.get("PINGDOM_API_TOKEN")

ZABBIX_SERVER = os.environ.get("ZABBIX_SERVER", "127.0.0.1")
ZABBIX_PORT = int(os.environ.get("ZABBIX_PORT", "10051"))
ZABBIX_HOST = os.environ.get("ZABBIX_HOST", "Pingdom")
ZABBIX_KEY_DISCOVERY = os.environ.get("ZABBIX_KEY_DISCOVERY", "pingdom.checks")
ZABBIX_KEY_STATUS = os.environ.get("ZABBIX_KEY_STATUS", "pingdom.status")
ZABBIX_KEY_RESPTIME = os.environ.get("ZABBIX_KEY_RESPTIME", "pingdom.response_time")

logging.basicConfig(
    format=u'[%(asctime)s] %(levelname)s %(message)s',
    level=logging.DEBUG
)


class Check(TypedDict):
    name: str
    status: str
    resptime: Optional[int] # absent if the check has never run
    lasttesttime: Optional[int] # absent if the check has never run


def pingdom_data(pingdom_response: requests.Response) -> list[Check]:
    return [
        {
            "name": check["name"],
            "status": check["status"],
            "resptime": check.get("lastresponsetime"),
            "lasttesttime": check.get("lasttesttime"),
        }
        for check in pingdom_response.json()["checks"]
    ]


def zabbix_discovery(sender: Sender, checks: list[Check]) -> None:
    # LLD macro {#NAME} is used by dependent Zabbix items to prototype per-check keys
    discovery = json.dumps([{"{#NAME}": check["name"]} for check in checks])
    response = sender.send_value(ZABBIX_HOST, ZABBIX_KEY_DISCOVERY, discovery)
    logging.info(f"discovery: {response}")


# Zabbix stores status as an integer; map Pingdom's string values to numeric codes.
# Unmapped statuses fall back to 3 so they're mapped to the general "unknown" status.
STATUS_MAP = {
    "up":               1,
    "down":             0,
    "unconfirmed_down": 2,
    "unknown":          3,
    "paused":           4,
}

def zabbix_status(sender: Sender, checks: list[Check]) -> None:
    items = [
        ItemValue(
            ZABBIX_HOST,
            f'{ZABBIX_KEY_STATUS}[{check["name"]}]',
            STATUS_MAP.get(check["status"], 3),
            check["lasttesttime"],
        )
        for check in checks
    ]
    logging.debug(items)
    response = sender.send(items)
    logging.info(f"status: {response}")


def zabbix_resptime(sender: Sender, checks: list[Check]) -> None:
    items = [
        ItemValue(
            ZABBIX_HOST,
            f'{ZABBIX_KEY_RESPTIME}[{check["name"]}]',
            check["resptime"],
            check["lasttesttime"],
        )
        for check in checks
    ]
    logging.debug(items)
    response = sender.send(items)
    logging.info(f"resptime: {response}")


if __name__ == "__main__":
    try:
        if not PINGDOM_API_TOKEN:
            raise ValueError("Missing required environment variable: PINGDOM_API_TOKEN")

        res = requests.get(
            PINGDOM_API_URL,
            headers={"Authorization": f"Bearer {PINGDOM_API_TOKEN}"},
            timeout=30,
        )
        res.raise_for_status()

        sender = Sender(server=ZABBIX_SERVER, port=ZABBIX_PORT)
        data = pingdom_data(res)
        zabbix_discovery(sender, data)
        zabbix_status(sender, data)
        zabbix_resptime(sender, data)
    except Exception as e:
        logging.exception(e)
        sys.exit(1)

# pingdom-zabbix.py

Fetches Pingdom check data via the Pingdom API and sends it to Zabbix using
low-level discovery (LLD) along with per-check status and response time items.
Intended to be run on a schedule (e.g., cron).

Inspired by [umflint/pingdom-zabbix](https://github.com/um-flint/pingdom-zabbix), updated for Pingdom API v3.1 and the zabbix_utils Python interface. Tested against Zabbix 7.4.

## Zabbix Setup

A Zabbix host and template (example provided) are required. The default host name is `Pingdom`
(configurable via `ZABBIX_HOST`). The template should use LLD with the
discovery key (default: `pingdom.checks`) to dynamically create per-check
items for status (`pingdom.status[<name>]`) and response time
(`pingdom.response_time[<name>]`).

Status values sent to Zabbix:

| Pingdom status    | Zabbix value |
|-------------------|-------------|
| `up`              | 1           |
| `down`            | 0           |
| `unconfirmed_down`| 2           |
| `unknown`         | 3           |
| `paused`          | 4           |
| *(unmapped)*      | 3           |

## Script Configuration

All configuration is via environment variables:

| Variable               | Default                                      | Required |
|------------------------|----------------------------------------------|----------|
| `PINGDOM_API_TOKEN`    | —                                            | Yes      |
| `PINGDOM_API_URL`      | `https://api.pingdom.com/api/3.1/checks`     | No       |
| `ZABBIX_SERVER`        | `127.0.0.1`                                  | No       |
| `ZABBIX_PORT`          | `10051`                                      | No       |
| `ZABBIX_HOST`          | `Pingdom`                                    | No       |
| `ZABBIX_KEY_DISCOVERY` | `pingdom.checks`                             | No       |
| `ZABBIX_KEY_STATUS`    | `pingdom.status`                             | No       |
| `ZABBIX_KEY_RESPTIME`  | `pingdom.response_time`                      | No       |

## Python Dependencies

```
requests
zabbix_utils
```

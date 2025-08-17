import requests
import os

ZABBIX_URL = os.getenv("ZABBIX_URL", "http://zabbix-web:8080/zabbix/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "Admin")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "zabbix")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Login no Zabbix
payload = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "user": ZABBIX_USER,
        "password": ZABBIX_PASSWORD
    },
    "id": 1
}
auth = requests.post(ZABBIX_URL, json=payload).json().get('result')

# Obter eventos recentes
payload = {
    "jsonrpc": "2.0",
    "method": "event.get",
    "params": {
        "output": "extend",
        "selectHosts": ["host"],
        "value": 1,
        "sortfield": ["clock", "eventid"],
        "sortorder": "DESC",
        "limit": 3
    },
    "auth": auth,
    "id": 2
}
events = requests.post(ZABBIX_URL, json=payload).json().get('result', [])

if events:
    message = "🚨 ALERTA ZABBIX 🚨\n"
    for e in events:
        host = e['hosts'][0]['host'] if e.get('hosts') else 'Desconhecido'
        message += f"Host: {host} | Evento ID: {e['eventid']}\n"

    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            params={"chat_id": TELEGRAM_CHAT_ID, "text": message}
        )

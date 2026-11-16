import asyncio
import base64
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import aiohttp
import yaml

SECRETS_PATH = Path("/config/secrets.yaml")
INTERVALS_URL = "https://intervals.icu/api/v1/athlete/0/wellness"
HA_WS_URL = "ws://127.0.0.1:8123/api/websocket"
SOURCE = "intervals"
DAYS_BACK = 7
TIMEZONE = ZoneInfo("America/Los_Angeles")

METRICS = [
    {"field": "restingHR", "id": "resting_hr", "name": "Resting HR", "unit": "bpm", "unit_class": None},
    {"field": "avgSleepingHR", "id": "avg_sleeping_hr", "name": "Avg Sleeping HR", "unit": "bpm", "unit_class": None},
    {"field": "hrv", "id": "hrv", "name": "HRV", "unit": "ms", "unit_class": "duration"},
    {"field": "sleepSecs", "id": "sleep", "name": "Sleep", "unit": "h", "unit_class": "duration", "scale": 1 / 3600},
    {"field": "steps", "id": "steps", "name": "Steps", "unit": "steps", "unit_class": None},
    {"field": "weight", "id": "weight", "name": "Weight", "unit": "kg", "unit_class": "mass"},
    {"field": "AlcoholicDrinks", "id": "drinks", "name": "Drinks", "unit": "drinks", "unit_class": None, "default": 0},
]


async def fetch_wellness(session, api_key, oldest, newest):
    credentials = base64.b64encode(f"API_KEY:{api_key}".encode()).decode()
    async with session.get(
        INTERVALS_URL,
        params={"oldest": oldest.isoformat(), "newest": newest.isoformat()},
        headers={"Authorization": f"Basic {credentials}"},
    ) as response:
        response.raise_for_status()
        return {record["id"]: record for record in await response.json()}


def day_start(day):
    return datetime(day.year, day.month, day.day, tzinfo=TIMEZONE).isoformat()


def build_stats(metric, records, days, today):
    stats = []
    for day in days:
        value = records.get(day.isoformat(), {}).get(metric["field"])
        if value is None and day < today:
            value = metric.get("default")
        if value is None:
            continue
        value = round(value * metric.get("scale", 1), 2)
        stats.append({"start": day_start(day), "mean": value, "min": value, "max": value})
    return stats


def build_message(message_id, metric, stats):
    return {
        "id": message_id,
        "type": "recorder/import_statistics",
        "metadata": {
            "has_sum": False,
            "mean_type": 1,
            "name": f"Intervals {metric['name']}",
            "source": SOURCE,
            "statistic_id": f"{SOURCE}:{metric['id']}",
            "unit_class": metric["unit_class"],
            "unit_of_measurement": metric["unit"],
        },
        "stats": stats,
    }


async def import_statistics(session, ha_token, messages):
    async with session.ws_connect(HA_WS_URL) as websocket:
        await websocket.receive_json()
        await websocket.send_json({"type": "auth", "access_token": ha_token})
        auth = await websocket.receive_json()
        if auth["type"] != "auth_ok":
            raise RuntimeError(f"Home Assistant auth failed: {auth}")
        for message in messages:
            await websocket.send_json(message)
            result = await websocket.receive_json()
            statistic_id = message["metadata"]["statistic_id"]
            if not result.get("success"):
                raise RuntimeError(f"Import failed for {statistic_id}: {result}")
            print(f"{statistic_id}: {len(message['stats'])} days imported")


async def main():
    secrets = yaml.safe_load(SECRETS_PATH.read_text())
    today = datetime.now(TIMEZONE).date()
    days = [today - timedelta(days=offset) for offset in range(DAYS_BACK, -1, -1)]

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        records = await fetch_wellness(session, secrets["intervals_icu_api_key"], days[0], days[-1])
        messages = []
        for metric in METRICS:
            stats = build_stats(metric, records, days, today)
            if stats:
                messages.append(build_message(len(messages) + 1, metric, stats))
        await import_statistics(session, secrets["intervals_ha_token"], messages)


if __name__ == "__main__":
    asyncio.run(main())
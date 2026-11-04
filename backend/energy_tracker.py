
import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "heater_energy.db"

ELECTRICITY_PRICE = 0.38

POWER_BY_LEVEL = {
    "1": 800,
    "2": 1200,
    "3": 2000,
}

STANDBY_POWER = 0.4


class EnergyTracker:

    def __init__(self):
        self.connection = sqlite3.connect(
            DB_PATH,
            check_same_thread=False
        )
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS daily_usage (
                    date TEXT PRIMARY KEY,
                    energy_kwh REAL DEFAULT 0,
                    heating_seconds REAL DEFAULT 0,
                    standby_seconds REAL DEFAULT 0,
                    cycles INTEGER DEFAULT 0
                )
            """)

            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS tracker_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_timestamp REAL,
                    last_state TEXT,
                    last_power REAL
                )
            """)

    def get_power(self, status):

        if not status:
            return "unknown", STANDBY_POWER

        if not status.get("switch", False):
            return "standby", STANDBY_POWER

        work_state = str(
            status.get("work_state", "")
        ).lower()

        if work_state == "heating":
            level = str(status.get("level", "1"))
            return "heating", POWER_BY_LEVEL.get(level, 800)

        return "standby", STANDBY_POWER

    def update(self, status):

        now = time.time()
        current_state, current_power = self.get_power(status)

        previous = self.connection.execute(
            "SELECT * FROM tracker_state WHERE id = 1"
        ).fetchone()

        today = datetime.now().strftime("%Y-%m-%d")

        if previous and previous["last_timestamp"] is not None:

            elapsed = max(
                0,
                min(now - previous["last_timestamp"], 30)
            )

            previous_state = previous["last_state"]
            previous_power = previous["last_power"]

            energy = (
                previous_power * elapsed
            ) / 3_600_000

            heating_seconds = (
                elapsed if previous_state == "heating" else 0
            )

            standby_seconds = (
                elapsed if previous_state == "standby" else 0
            )

            cycles = int(
                current_state == "heating"
                and previous_state != "heating"
            )

            with self.connection:
                self.connection.execute("""
                    INSERT INTO daily_usage (
                        date, energy_kwh,
                        heating_seconds, standby_seconds, cycles
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET
                        energy_kwh = energy_kwh + excluded.energy_kwh,
                        heating_seconds =
                            heating_seconds + excluded.heating_seconds,
                        standby_seconds =
                            standby_seconds + excluded.standby_seconds,
                        cycles = cycles + excluded.cycles
                """, (
                    today,
                    energy,
                    heating_seconds,
                    standby_seconds,
                    cycles
                ))

        with self.connection:
            self.connection.execute("""
                INSERT INTO tracker_state (
                    id, last_timestamp, last_state, last_power
                )
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    last_timestamp = excluded.last_timestamp,
                    last_state = excluded.last_state,
                    last_power = excluded.last_power
            """, (now, current_state, current_power))

        return self.summary()

    def summary(self):

        today = datetime.now().strftime("%Y-%m-%d")

        row = self.connection.execute(
            "SELECT * FROM daily_usage WHERE date = ?",
            (today,)
        ).fetchone()

        if row is None:
            energy = 0
            heating_seconds = 0
            standby_seconds = 0
            cycles = 0
        else:
            energy = row["energy_kwh"]
            heating_seconds = row["heating_seconds"]
            standby_seconds = row["standby_seconds"]
            cycles = row["cycles"]

        return {
            "date": today,
            "energy_kwh": round(energy, 4),
            "estimated_cost_eur": round(
                energy * ELECTRICITY_PRICE, 4
            ),
            "electricity_price": ELECTRICITY_PRICE,
            "heating_seconds": round(heating_seconds),
            "standby_seconds": round(standby_seconds),
            "heating_hours": round(heating_seconds / 3600, 2),
            "standby_hours": round(standby_seconds / 3600, 2),
            "cycles": cycles,
            "measurement": "estimated"
        }

    def close(self):
        self.connection.close()

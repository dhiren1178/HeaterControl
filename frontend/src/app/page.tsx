
"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

type HeaterStatus = {
  switch: boolean;
  temp_set: number;
  temp_current: number;
  level: string;
  work_state: string;
  countdown_set: string;
  countdown_left: number;
};

type EnergyData = {
  date: string;
  energy_kwh: number;
  estimated_cost_eur: number;
  electricity_price: number;
  heating_seconds: number;
  standby_seconds: number;
  heating_hours: number;
  standby_hours: number;
  cycles: number;
  measurement: string;
};

function formatDuration(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  return `${hours}h ${minutes}m`;
}

export default function Home() {
  const [status, setStatus] = useState<HeaterStatus | null>(null);
  const [energy, setEnergy] = useState<EnergyData | null>(null);
  const [temperature, setTemperature] = useState(22);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [statusResponse, energyResponse] = await Promise.all([
        fetch(`${API_URL}/api/status`, { cache: "no-store" }),
        fetch(`${API_URL}/api/energy`, { cache: "no-store" }),
      ]);

      if (!statusResponse.ok || !energyResponse.ok) {
        throw new Error("Could not retrieve heater information");
      }

      const statusData: HeaterStatus = await statusResponse.json();
      const energyData: EnergyData = await energyResponse.json();

      setStatus(statusData);
      setEnergy(energyData);
      setTemperature(statusData.temp_set);
      setError("");

      setLastUpdated(
        new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Connection failed"
      );
    }
  }, []);

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 10000);

    return () => clearInterval(interval);
  }, [fetchData]);

  async function sendCommand(
    code: string,
    value: string | number | boolean
  ) {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/command`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code, value }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Command failed");
      }

      await fetchData();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Command failed"
      );
    } finally {
      setLoading(false);
    }
  }

  const connected = status !== null;

  return (
    <main className="min-h-screen bg-[#101114] text-white">
      <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8 sm:py-12">

        {/* HEADER */}
        <header className="mb-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 text-xl">
              ♨
            </div>
            <div>
              <h1 className="text-xl font-semibold">HeaterControl</h1>
              <p className="text-xs text-gray-500">LEBENLANG LBL0380</p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2">
            <span className={`h-2 w-2 rounded-full ${
              connected ? "bg-green-400" : "bg-red-400"
            }`} />
            <span className="text-xs text-gray-300">
              {connected ? "Connected" : "Disconnected"}
            </span>
          </div>
        </header>

        {error && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* TEMPERATURE AND POWER */}
        <section className="mb-6 grid gap-6 md:grid-cols-2">
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-[#252832] to-[#17191f] p-8">
            <p className="text-sm text-gray-400">
              CURRENT TEMPERATURE
            </p>

            <div className="mt-5 flex items-start">
              <span className="text-7xl font-light tracking-tighter">
                {status?.temp_current ?? "--"}
              </span>
              <span className="mt-2 text-3xl text-gray-400">°C</span>
            </div>

            <p className="mt-8 text-sm text-gray-400">
              Target: {status ? `${status.temp_set}°C` : "--"}
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-[#1b1d23] p-8">
            <p className="text-sm text-gray-400">HEATER POWER</p>

            <div className="mt-5 flex items-center justify-between">
              <div>
                <p className="text-4xl font-semibold">
                  {status ? (status.switch ? "ON" : "OFF") : "--"}
                </p>
                <p className="mt-2 text-sm text-gray-500">
                  {status?.work_state ?? "Waiting for data"}
                </p>
              </div>

              <button
                disabled={!connected || loading}
                onClick={() =>
                  sendCommand("switch", !status?.switch)
                }
                className={`h-16 w-16 rounded-2xl text-2xl transition disabled:opacity-40 ${
                  status?.switch
                    ? "bg-green-500 text-black"
                    : "bg-white/10 text-white"
                }`}
              >
                ⏻
              </button>
            </div>
          </div>
        </section>

        {/* TEMPERATURE CONTROL */}
        <section className="mb-6 rounded-3xl border border-white/10 bg-[#1b1d23] p-7">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium">Target temperature</h2>
              <p className="mt-1 text-sm text-gray-500">
                Adjust your preferred temperature
              </p>
            </div>
            <span className="text-3xl font-semibold">{temperature}°C</span>
          </div>

          <input
            type="range"
            min="10"
            max="35"
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
            className="mt-8 w-full accent-orange-400"
          />

          <div className="mt-3 flex justify-between text-xs text-gray-500">
            <span>10°C</span>
            <span>35°C</span>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <div className="flex gap-2">
              <button
                disabled={!connected || loading || temperature <= 10}
                onClick={() => setTemperature((t) => t - 1)}
                className="rounded-xl bg-white/10 px-5 py-3"
              >
                −
              </button>
              <button
                disabled={!connected || loading || temperature >= 35}
                onClick={() => setTemperature((t) => t + 1)}
                className="rounded-xl bg-white/10 px-5 py-3"
              >
                +
              </button>
            </div>

            <button
              disabled={!connected || loading}
              onClick={() => sendCommand("temp_set", temperature)}
              className="rounded-xl bg-orange-500 px-6 py-3 text-sm font-semibold hover:bg-orange-400 disabled:opacity-40"
            >
              Apply temperature
            </button>
          </div>
        </section>

        {/* HEATING LEVEL */}
        <section className="mb-6 rounded-3xl border border-white/10 bg-[#1b1d23] p-7">
          <h2 className="text-lg font-medium">Heating level</h2>
          <p className="mt-1 text-sm text-gray-500">
            Choose your preferred heating power
          </p>

          <div className="mt-6 grid grid-cols-3 gap-3">
            {[
              { id: "1", name: "Low", power: "800 W" },
              { id: "2", name: "Medium", power: "1200 W" },
              { id: "3", name: "High", power: "2000 W" },
            ].map((item) => (
              <button
                key={item.id}
                disabled={!connected || loading}
                onClick={() => sendCommand("level", item.id)}
                className={`rounded-2xl border p-5 transition disabled:opacity-40 ${
                  status?.level === item.id
                    ? "border-orange-400 bg-orange-500/15 text-orange-300"
                    : "border-white/10 bg-white/5 text-gray-300"
                }`}
              >
                <span className="block text-2xl font-semibold">
                  {item.id}
                </span>
                <span className="mt-1 block text-xs">{item.name}</span>
                <span className="mt-1 block text-xs text-gray-500">
                  {item.power}
                </span>
              </button>
            ))}
          </div>
        </section>

        {/* COUNTDOWN */}
        <section className="mb-6 rounded-3xl border border-white/10 bg-[#1b1d23] p-7">
          <h2 className="text-lg font-medium">Countdown timer</h2>

          <div className="mt-6 grid grid-cols-3 gap-3 sm:grid-cols-6">
            {["1h", "2h", "3h", "4h", "5h", "6h"].map((timer) => (
              <button
                key={timer}
                disabled={!connected || loading}
                onClick={() => sendCommand("countdown_set", timer)}
                className={`rounded-xl border p-4 text-sm ${
                  status?.countdown_set === timer
                    ? "border-orange-400 bg-orange-500/15 text-orange-300"
                    : "border-white/10 bg-white/5 text-gray-300"
                }`}
              >
                {timer}
              </button>
            ))}
          </div>

          <div className="mt-5 flex items-center justify-between gap-3">
            <p className="text-sm text-gray-400">
              {status?.countdown_left
                ? `${status.countdown_left} minutes remaining`
                : "No active countdown"}
            </p>

            <button
              disabled={!connected || loading}
              onClick={() => sendCommand("countdown_set", "cancel")}
              className="rounded-xl bg-white/10 px-5 py-3 text-sm"
            >
              Cancel timer
            </button>
          </div>
        </section>

        {/* ENERGY MONITOR */}
        <section className="mb-6 rounded-3xl border border-white/10 bg-gradient-to-br from-[#202b28] to-[#171d1c] p-7 sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">
                Electricity consumption
              </h2>
              <p className="mt-1 text-sm text-gray-400">
                Estimated usage today
              </p>
            </div>

            <span className="rounded-full border border-green-400/20 bg-green-400/10 px-3 py-1 text-xs text-green-300">
              Estimated
            </span>
          </div>

          <div className="mt-7 grid grid-cols-2 gap-4">
            <div className="rounded-2xl bg-black/20 p-5">
              <p className="text-xs text-gray-400">ENERGY USED</p>
              <p className="mt-2 text-3xl font-semibold">
                {energy ? energy.energy_kwh.toFixed(3) : "--"}
                <span className="ml-1 text-sm text-gray-400">kWh</span>
              </p>
            </div>

            <div className="rounded-2xl bg-black/20 p-5">
              <p className="text-xs text-gray-400">ESTIMATED COST</p>
              <p className="mt-2 text-3xl font-semibold">
                {energy
                  ? `€${energy.estimated_cost_eur.toFixed(3)}`
                  : "--"}
              </p>
            </div>

            <div className="rounded-2xl bg-black/20 p-5">
              <p className="text-xs text-gray-400">HEATING TIME</p>
              <p className="mt-2 text-xl font-semibold">
                {energy
                  ? formatDuration(energy.heating_seconds)
                  : "--"}
              </p>
            </div>

            <div className="rounded-2xl bg-black/20 p-5">
              <p className="text-xs text-gray-400">STANDBY TIME</p>
              <p className="mt-2 text-xl font-semibold">
                {energy
                  ? formatDuration(energy.standby_seconds)
                  : "--"}
              </p>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-5">
            <div>
              <p className="text-sm text-gray-400">Heating cycles today</p>
              <p className="mt-1 text-xl font-semibold">
                {energy?.cycles ?? "--"}
              </p>
            </div>

            <div className="text-right">
              <p className="text-xs text-gray-400">Electricity price</p>
              <p className="mt-1 text-sm font-medium">
                €{energy?.electricity_price.toFixed(2) ?? "0.38"}/kWh
              </p>
            </div>
          </div>

          <p className="mt-4 text-xs text-gray-500">
            Based on rated heating power and monitored operating time.
            Actual consumption may differ.
          </p>
        </section>

        {/* FOOTER */}
        <footer className="mt-8 flex flex-wrap items-center justify-between gap-3 text-xs text-gray-600">
          <span>HeaterControl · Local dashboard</span>
          <span>Last updated: {lastUpdated || "Waiting..."}</span>
        </footer>
      </div>
    </main>
  );
}

# HeaterControl – Smart Heater Control & Energy Monitoring

A personal software project developed to remotely control and monitor a LEBENLANG LBL0380 smart heater through the Tuya Smart API.

The project provides a custom web dashboard for controlling heater settings, monitoring operating states, and estimating electricity consumption.

## Features

- **Remote Heater Control:** Turn the heater ON/OFF through a custom dashboard.
- **Temperature Control:** Adjust the target temperature between 10°C and 35°C.
- **Heating Levels:** Select among three heating levels.
- **Countdown Timer:** Configure heating timers from 1 to 6 hours.
- **Live Status Monitoring:** Retrieve current temperature, target temperature, power state and operating mode.
- **Energy Consumption Estimation:** Estimate electricity usage based on heating level, operating time and standby time.
- **Cost Estimation:** Calculate estimated electricity costs using a configurable electricity tariff.
- **Persistent Energy Tracking:** Store daily energy statistics using SQLite.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Styling | Tailwind CSS |
| Backend | Python, FastAPI |
| Device Integration | Tuya Smart API |
| Database | SQLite |
| Development Environment | macOS, VS Code |

## Architecture

The Next.js dashboard communicates with a Python FastAPI backend. The backend connects to the Tuya Cloud API to retrieve heater status and send control commands.

The energy monitoring module periodically checks the heater's operating state and estimates electricity consumption using its rated power levels.

## Energy Monitoring

The electricity consumption monitor estimates usage using the following rated power values:

- Level 1: 800 W
- Level 2: 1,200 W
- Level 3: 2,000 W
- Standby: 0.4 W (assumed)

The default electricity tariff is €0.38/kWh.

**Note:** Energy readings are estimates based on rated power and operating time, not direct measurements from an electricity meter.

## Project Structure

```text
HeaterControl/
├── backend/
│   ├── main.py
│   ├── tuya_client.py
│   └── energy_tracker.py
├── frontend/
│   └── src/
│       └── app/
├── .gitignore
└── README.md
```

## Running Locally

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn python-dotenv tuya-connector-python
uvicorn backend.main:app --reload
```

Configure the following environment variables in a local `.env` file:

```env
TUYA_ACCESS_ID=your_access_id
TUYA_ACCESS_SECRET=your_access_secret
TUYA_ENDPOINT=your_tuya_endpoint
TUYA_DEVICE_ID=your_device_id
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 to access the dashboard.

## Security

- Tuya credentials are stored in environment variables.
- The `.env` file must never be committed to Git.
- API access should be protected before exposing the backend publicly.

## Purpose

This project was developed as a personal software engineering project to explore IoT device integration, API communication, full-stack development, and energy consumption monitoring.

---

**Developed by Dhiren Sharma**
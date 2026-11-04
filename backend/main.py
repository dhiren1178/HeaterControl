
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.tuya_client import (
    connect_to_tuya,
    get_heater_status,
    send_command
)

from backend.energy_tracker import EnergyTracker


tracker = EnergyTracker()
api = None


async def monitor_heater():

    while True:
        try:
            status = await asyncio.to_thread(
                get_heater_status, api
            )

            if status:
                tracker.update(status)

        except Exception as error:
            print(f"Energy monitoring error: {error}")

        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):

    global api

    api = await asyncio.to_thread(connect_to_tuya)

    monitor_task = asyncio.create_task(monitor_heater())

    yield

    monitor_task.cancel()

    try:
        await monitor_task
    except asyncio.CancelledError:
        pass

    tracker.close()


app = FastAPI(
    title="LEBENLANG Heater Control",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HeaterCommand(BaseModel):
    code: str
    value: object


@app.get("/")
def home():
    return {
        "message": "Heater Control API is running"
    }


@app.get("/api/status")
def heater_status():

    try:
        status = get_heater_status(api)

        if status is None:
            raise HTTPException(
                status_code=502,
                detail="Could not retrieve heater status"
            )

        return status

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.post("/api/command")
def heater_command(command: HeaterCommand):

    try:
        success = send_command(
            api,
            command.code,
            command.value
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Tuya rejected the command"
            )

        return {
            "success": True,
            "message": "Command sent successfully"
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.get("/api/energy")
def heater_energy():

    return tracker.summary()

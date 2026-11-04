
import os
import json
from dotenv import load_dotenv
from tuya_connector import TuyaOpenAPI

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
ENDPOINT = os.getenv("TUYA_ENDPOINT")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")


# --------------------------------------------------
# CONNECT TO TUYA
# --------------------------------------------------

def connect_to_tuya():

    required = {
        "TUYA_ACCESS_ID": ACCESS_ID,
        "TUYA_ACCESS_SECRET": ACCESS_SECRET,
        "TUYA_ENDPOINT": ENDPOINT,
        "TUYA_DEVICE_ID": DEVICE_ID
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    api = TuyaOpenAPI(
        ENDPOINT,
        ACCESS_ID,
        ACCESS_SECRET
    )

    response = api.connect()

    if not response or not response.get("success"):
        raise RuntimeError(
            f"Tuya authentication failed: {response}"
        )

    print("\nConnected to Tuya successfully!")

    return api


# --------------------------------------------------
# GET HEATER STATUS
# --------------------------------------------------

def get_heater_status(api):

    path = f"/v1.0/iot-03/devices/{DEVICE_ID}/status"

    response = api.get(path)

    if not response.get("success"):
        print("\nStatus request failed:")
        print(json.dumps(response, indent=2))
        return None

    result = response.get("result", [])

    print("\n========== HEATER STATUS ==========")

    status = {}

    for item in result:
        code = item["code"]
        value = item["value"]

        status[code] = value
        print(f"{code:20}: {value}")

    print("===================================\n")

    return status


# --------------------------------------------------
# SEND COMMAND
# --------------------------------------------------

def send_command(api, code, value):

    allowed_commands = {
        "switch",
        "temp_set",
        "level",
        "countdown_set"
    }

    if code not in allowed_commands:
        raise ValueError(f"Unsupported command: {code}")

    if code == "switch" and type(value) is not bool:
        raise ValueError("Switch must be True or False")

    if code == "temp_set":
        if type(value) is not int or not 10 <= value <= 35:
            raise ValueError("Temperature must be between 10 and 35")

    if code == "level":
        if str(value) not in ["1", "2", "3"]:
            raise ValueError("Heating level must be 1, 2 or 3")
        value = str(value)

    if code == "countdown_set":
        allowed_timers = [
            "cancel", "1h", "2h", "3h",
            "4h", "5h", "6h"
        ]

        if value not in allowed_timers:
            raise ValueError("Invalid countdown value")

    path = f"/v1.0/iot-03/devices/{DEVICE_ID}/commands"

    payload = {
        "commands": [
            {
                "code": code,
                "value": value
            }
        ]
    }

    print(f"\nSending command: {code} = {value}")

    response = api.post(path, payload)

    print("\n========== COMMAND RESPONSE ==========")
    print(json.dumps(response, indent=2))
    print("======================================\n")

    if not response.get("success"):
        print("The Tuya API rejected the command.")
        return False

    print("Tuya accepted the command.")

    return True


# --------------------------------------------------
# INDIVIDUAL CONTROLS
# --------------------------------------------------

def set_power(api, enabled):
    return send_command(api, "switch", enabled)


def set_temperature(api, temperature):
    return send_command(api, "temp_set", temperature)


def set_level(api, level):
    return send_command(api, "level", level)


def set_countdown(api, duration):
    return send_command(api, "countdown_set", duration)


# --------------------------------------------------
# COMMAND VERIFICATION
# --------------------------------------------------

def verify_status(api, code, expected_value):

    print("Checking heater status...")

    status = get_heater_status(api)

    if status is None:
        return False

    actual_value = status.get(code)

    print(f"Expected: {expected_value}")
    print(f"Actual:   {actual_value}")

    if actual_value == expected_value:
        print("Status matches expected value.")
        return True

    print("Status does not match yet.")
    print("The device may not have applied the command.")
    return False


# --------------------------------------------------
# MENU
# --------------------------------------------------

def show_menu():

    print("""
====================================
       LEBENLANG HEATER CONTROL
====================================

1. Read heater status
2. Set temperature
3. Set heating level
4. Set countdown timer
5. Turn heater ON
6. Turn heater OFF
7. Cancel countdown
8. Exit

====================================
""")


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------

def main():

    try:

        api = connect_to_tuya()

        while True:

            show_menu()

            choice = input("Choose an option: ").strip()

            try:

                if choice == "1":

                    get_heater_status(api)

                elif choice == "2":

                    temperature = int(
                        input("Enter temperature (10-35): ")
                    )

                    success = set_temperature(api, temperature)

                    if success:
                        verify_status(
                            api,
                            "temp_set",
                            temperature
                        )

                elif choice == "3":

                    level = input(
                        "Enter heating level (1, 2, 3): "
                    ).strip()

                    success = set_level(api, level)

                    if success:
                        verify_status(api, "level", level)

                elif choice == "4":

                    duration = input(
                        "Enter countdown "
                        "(cancel, 1h, 2h, 3h, 4h, 5h, 6h): "
                    ).strip()

                    success = set_countdown(api, duration)

                    if success:
                        print("Countdown command submitted.")
                        get_heater_status(api)

                elif choice == "5":

                    confirm = input(
                        "Turn heater ON? (yes/no): "
                    ).strip().lower()

                    if confirm == "yes":
                        set_power(api, True)
                        get_heater_status(api)

                elif choice == "6":

                    confirm = input(
                        "Turn heater OFF? (yes/no): "
                    ).strip().lower()

                    if confirm == "yes":
                        set_power(api, False)
                        get_heater_status(api)

                elif choice == "7":

                    set_countdown(api, "cancel")
                    get_heater_status(api)

                elif choice == "8":

                    print("Exiting HeaterControl.")
                    break

                else:

                    print("Invalid option. Try again.")

            except ValueError as error:
                print(f"\nInput error: {error}")

            except Exception as error:
                print(f"\nOperation failed: {error}")

    except Exception as error:
        print(f"\nApplication error: {error}")


if __name__ == "__main__":
    main()

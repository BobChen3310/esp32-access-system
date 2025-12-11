from modules.lcd import display_msg
from modules.rfid import read_uid
from modules.network import connect_wifi, connect_mqtt
from modules.access import show_standby, grant_access, deny_access
import urequests, json, time

CONFIG = {
    "WIFI_SSID": "your-wifi-ssid",
    "WIFI_PASS": "your-wifi-password",
    "API_URL": "your-api-url", 
    "DEVICE_TOKEN": "your-device-token",
    "DEVICE_ID": "your-device-id",
    "MQTT_BROKER": "your-mqtt-broker-ip",
    "MQTT_USER": "your-mqtt-broker-username",
    "MQTT_PASS": "your-mqtt-broker-password",
    "MQTT_PORT": "your-mqtt-broker-port"
}

def mqtt_callback(topic, msg):
    if msg == b"OPEN":
        grant_access("Remote")

def main():
    ip = connect_wifi(CONFIG["WIFI_SSID"], CONFIG["WIFI_PASS"])
    if not ip:
        return

    display_msg("WiFi OK", ip)
    time.sleep(2)

    client = connect_mqtt(CONFIG, mqtt_callback)
    if client:
        display_msg("MQTT OK", "System Ready")
    else:
        display_msg("MQTT Error", "Check HiveMQ")
        time.sleep(2)

    show_standby()

    while True:
        try:
            if client:
                client.check_msg()

            uid = read_uid()
            if uid:
                display_msg("Verifying...", uid)

                try:
                    headers = {
                        "Content-Type": "application/json",
                        "x-device-token": CONFIG["DEVICE_TOKEN"]
                    }
                    payload = {
                        "card_uid": uid,
                        "device_id": CONFIG["DEVICE_ID"]
                    }

                    res = urequests.post(
                        CONFIG["API_URL"],
                        headers=headers,
                        data=json.dumps(payload),
                        timeout=5
                    )

                    if res.status_code == 200:
                        body = res.json()
                        if body.get("access") == True:
                            grant_access(body.get("student_id"))
                        else:
                            deny_access()
                    else:
                        deny_access()

                    res.close()
                except:
                    deny_access()

            time.sleep(0.1)

        except OSError:
            print("MQTT Restarting...")
            try:
                client.connect()
                client.subscribe("door/" + CONFIG["DEVICE_ID"])
            except:
                pass

if __name__ == "__main__":
    main()
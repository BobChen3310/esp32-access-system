import network, time
from umqtt.simple import MQTTClient
from .lcd import display_msg

client = None

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        display_msg("System Init...", "Connecting WiFi")
        wlan.connect(ssid, password)
        retry = 0
        while not wlan.isconnected() and retry < 20:
            time.sleep(1)
            retry += 1

    if wlan.isconnected():
        return wlan.ifconfig()[0]
    else:
        display_msg("WiFi Error", "Check Settings")
        return None


def connect_mqtt(cfg, callback):
    global client
    try:
        client = MQTTClient(
            client_id=cfg["DEVICE_ID"],
            server=cfg["MQTT_BROKER"],
            user=cfg["MQTT_USER"],
            password=cfg["MQTT_PASS"],
            port=cfg["MQTT_PORT"],
            keepalive=60,
            ssl=True,
            ssl_params={"server_hostname": cfg["MQTT_BROKER"]}
        )
        client.set_callback(callback)
        client.connect()
        client.subscribe("door/" + cfg["DEVICE_ID"])
        return client
    except Exception as e:
        print("MQTT Error:", e)
        return None
import network
import time
from umqtt.simple import MQTTClient
import ubinascii
import machine

# ===== WiFi =====
WIFI_SSID = "SAL9000_2.4"
WIFI_PASS = "000025671214SK@1820ATH"

# ===== MQTT =====
MQTT_BROKER = "192.168.1.91"   # IP Raspberry Pi
MQTT_PORT = 1883

MQTT_TOPIC = b"robotakia/test"

MQTT_USER = None
MQTT_PASS = None

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0)  # απενεργοποίηση power save (πολύ συχνό fix)
    if not wlan.isconnected():
        print("Connecting WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 20000:
                raise RuntimeError("WiFi timeout")
            time.sleep(0.5)
    print("WiFi OK:", wlan.ifconfig())
    return wlan

def make_client():
    # μοναδικό client id από MAC για να μην σε πετάει ο broker
    cid = b"esp32-" + ubinascii.hexlify(machine.unique_id())
    c = MQTTClient(cid, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASS, keepalive=30)
    c.connect()
    print("Connected to MQTT broker as", cid)
    return c

wlan = wifi_connect()
client = make_client()

counter = 0
last_ok = time.ticks_ms()

while True:
    try:
        # αν χάθηκε WiFi, ξαναμπαίνουμε
        if not wlan.isconnected():
            wlan = wifi_connect()
            client = make_client()

        msg = "Hello from ESP32 MicroPython {}".format(counter)
        client.publish(MQTT_TOPIC, msg)
        print("Published:", msg)

        counter += 1
        last_ok = time.ticks_ms()
        time.sleep(5)

    except OSError as e:
        print("MQTT/WiFi error:", e)

        # προσπάθησε καθαρό reconnect MQTT
        try:
            client.disconnect()
        except:
            pass

        time.sleep(2)
        try:
            client = make_client()
        except Exception as e2:
            print("Reconnect failed:", e2)
            # αν δεν μπορεί να κάνει reconnect, ξανασύνδεση WiFi
            try:
                wlan.disconnect()
            except:
                pass
            time.sleep(2)
            wlan = wifi_connect()
            client = make_client()
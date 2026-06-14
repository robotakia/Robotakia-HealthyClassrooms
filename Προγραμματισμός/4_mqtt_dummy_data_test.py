import network, time, machine, ubinascii
from umqtt.simple import MQTTClient
import ujson
import urandom  # σε MicroPython υπάρχει random ως urandom

WIFI_SSID = "SAL9000_2.4"
WIFI_PASS = "000025671214SK@1820ATH"

MQTT_BROKER = "192.168.1.91"   # IP του Raspberry Pi
MQTT_PORT = 1883
TOPIC = b"classroom/air/telemetry"

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 20000:
                raise RuntimeError("WiFi timeout")
            time.sleep(0.5)
    print("WiFi OK:", wlan.ifconfig())
    return wlan

def mqtt_connect():
    cid = b"esp32-" + ubinascii.hexlify(machine.unique_id())
    c = MQTTClient(cid, MQTT_BROKER, port=MQTT_PORT, keepalive=30)
    c.connect()
    print("MQTT OK as", cid)
    return c

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

wlan = wifi_connect()
client = mqtt_connect()

temp = 23.0
hum = 45.0

seq = 0
while True:
    # dummy “κινήσεις” με μικρό θόρυβο
    temp += (urandom.getrandbits(8) / 255.0 - 0.5) * 0.4
    hum  += (urandom.getrandbits(8) / 255.0 - 0.5) * 1.0
    temp = clamp(temp, 18.0, 30.0)
    hum  = clamp(hum, 25.0, 75.0)

    # dummy MQ2 values
    smoke    = 200 + (urandom.getrandbits(10) % 200)   # 200..399
    lpg      = 150 + (urandom.getrandbits(10) % 250)   # 150..399
    methane  = 120 + (urandom.getrandbits(10) % 220)   # 120..339
    hydrogen = 100 + (urandom.getrandbits(10) % 200)   # 100..299

    # dummy “air_quality” flag
    air_quality = 0 if smoke > 320 else 1  # 0=Χαμηλή, 1=Καλή

    noise_adc = 800 + (urandom.getrandbits(10) % 1400)  # 800..2199

    payload = {
        "device": "classroom-esp32-1",
        "seq": seq,
        "ts_ms": time.ticks_ms(),
        "temperature_c": round(temp, 1),
        "humidity_pct": round(hum, 1),
        "smoke": smoke,
        "lpg": lpg,
        "methane": methane,
        "hydrogen": hydrogen,
        "air_quality": air_quality,
        "noise_adc": noise_adc
    }

    # απλή ένδειξη “πότε αερίζουμε”
    payload["advice"] = "VENTILATE" if air_quality == 0 else "OK"

    msg = ujson.dumps(payload)
    client.publish(TOPIC, msg)
    print("Published:", msg)

    seq += 1
    time.sleep(5)

import network
import time
import machine
import ubinascii
import ujson
import dht
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# -------- Ρυθμίσεις Hardware & Pins --------
DHT_PIN = 15          # Pin για DHT11
MQ2_PIN = 4         # Ψηφιακό Pin για MQ2
NOISE_ADC_PIN = 34    # Αναλογικό Pin για θόρυβο

# Αρχικοποίηση Αισθητήρων
dht_sensor = dht.DHT11(Pin(DHT_PIN))
MQ2_digital = Pin(MQ2_PIN, Pin.IN)

# Ρύθμιση ADC για τον θόρυβο (0-3.3V range)
noise_adc = ADC(Pin(NOISE_ADC_PIN))
noise_adc.atten(ADC.ATTN_11DB)
noise_adc.width(ADC.WIDTH_12BIT)

# -------- Ρυθμίσεις Δικτύου --------
WIFI_SSID = "REPLACE_WITH_YOURS"
WIFI_PASS = "REPLACE_WITH_YOURS"
MQTT_BROKER = "REPLACE_WITH_YOURS"
MQTT_PORT = 1883
TOPIC = b"classroom/air/telemetry"

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Σύνδεση στο WiFi...")
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

# Σύνδεση
wlan = wifi_connect()
client = mqtt_connect()

seq = 0
print("Έναρξη πραγματικών μετρήσεων...\n")

while True:
    try:
        # 1. Μέτρηση DHT11 (Θερμοκρασία/Υγρασία)
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()
        except OSError:
            print("Σφάλμα DHT11 - Χρήση προηγούμενων τιμών")
            temp, hum = 0.0, 0.0

        # 2. Μέτρηση MQ2 (Ποιότητα Αέρα)
        # Σημείωση: 0 = Χαμηλή ποιότητα (ανιχνεύτηκε αέριο), 1 = Καλή
        air_quality_stat = MQ2_digital.value()
        
        # 3. Μέτρηση Θορύβου (ADC)
        noise_val = noise_adc.read()

        # Δημιουργία Payload
        payload = {
            "device": "classroom-esp32-1",
            "seq": seq,
            "ts_ms": time.ticks_ms(),
            "temperature_c": round(float(temp), 1),
            "humidity_pct": round(float(hum), 1),
            "air_quality": air_quality_stat,
            "noise_adc": noise_val,
        }

        # Συμβουλή αερισμού βασισμένη στον MQ2
        payload["advice"] = "VENTILATE" if air_quality_stat == 0 else "OK"

        # Αποστολή μέσω MQTT
        msg = ujson.dumps(payload)
        client.publish(TOPIC, msg)
        print(f"[{seq}] Published: {msg}")

        seq += 1
        time.sleep(5)

    except Exception as e:
        print("Σφάλμα κύριου βρόχου:", e)
        time.sleep(2)
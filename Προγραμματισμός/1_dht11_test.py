import time
from machine import Pin
import dht

# -------- Ρυθμίσεις αισθητήρων --------
DHT_PIN = 15          # Pin που συνδέεται το DATA του DHT11
MQ135_PIN = 4         # Pin που συνδέεται το DO του MQ135

dht_sensor = dht.DHT11(Pin(DHT_PIN))
mq135_sensor = Pin(MQ135_PIN, Pin.IN)

print("Έναρξη μετρήσεων...\n")

try:
    while True:
        # Διαβάζουμε DHT11
        try:
            dht_sensor.measure()
            temperature = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            print(f"Θερμοκρασία: {temperature:.1f} °C")
            print(f"Υγρασία: {humidity:.1f} %")
        except OSError as e:
            print("Σφάλμα ανάγνωσης DHT11")

        # Διαβάζουμε MQ-135
        air_quality = mq135_sensor.value()
        if air_quality == 0:
            print("Ποιότητα αέρα: Χαμηλή")
        else:
            print("Ποιότητα αέρα: Καλή")

        print("---------------------")
        time.sleep(5)

except KeyboardInterrupt:
    print("Τερματισμός προγράμματος")
    
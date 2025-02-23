import time
import dht
from machine import Pin, ADC, PWM
import network
from umqtt.simple import MQTTClient

# Paramètres du point d'accès
WIFI_SSID = "abc"
WIFI_PASSWORD = "petitlouis"

# Paramètres du serveur MQTT
MQTT_CLIENT_ID = "projet"
MQTT_BROKER = "node02.myqtthub.com"
MQTT_PORT = 1883
MQTT_USER = "raphaelbaguelin"
MQTT_PASSWORD = "Raph192837465"
MQTT_TOPIC_TEMPERATURE = "temperature"
MQTT_TOPIC_HUMIDITE = "humidite"
MQTT_TOPIC_LUMINOSITE = "luminosite"


# Pin des capteurs
dht_sensor = dht.DHT11(Pin(15)) # Capteur DHT digital
ldr = ADC(Pin(34)) # Capteur LDR analogique
# Pin des LEDs
led_bleue = Pin(25, Pin.OUT)  # LED pour la l'humidité
led_verte = Pin(26, Pin.OUT)  # LED pour luminosité
led_rouge = Pin(27, Pin.OUT)  # LED pour la température
# Pin du buzzer
buzzer = PWM(Pin(14), freq=1000, duty=0)  # Initialisation du buzzer avec PWM

def play_buzzer(bips):
    for _ in range(bips):  # Joue 'bips' nombres de bips
        buzzer.duty(512)  # Active le buzzer (50% de duty cycle)
        time.sleep(0.2)   # Temps du bip
        buzzer.duty(0)    # Désactive le buzzer
        time.sleep(0.2)   # Pause entre les bips

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    print("Connexion au WiFi en cours...")
    while not wlan.isconnected():
        time.sleep(1)

    print("WiFi connect\u00e9!")
    print("Adresse IP :", wlan.ifconfig()[0])
    play_buzzer(3)
    return wlan

def connect_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, keepalive=60, ssl=False)
    client.connect()
    print("Connect\u00e9 au serveur MQTT")
    return client

wlan = connect_wifi()

client = connect_mqtt()

while True:
    # Surveillance état wifi
    if not wlan.isconnected():
        print("Wifi déconnecté")
        play_buzzer(2)
        while not wlan.isconnected():
            time.sleep(1)
        print("Reconnecté au Wifi")
        play_buzzer(3)
        client = connect_mqtt()
    # Lecture des données du capteur
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidite = dht_sensor.humidity()
    luminosite = round((ldr.read()/4095)*100, 1)  # ldr.read() : valeur analogique (0 à 4095)
    
    # Contrôle des LEDs
    led_verte.value(luminosite < 50)  # Allume si luminosité < 50%
    led_bleue.value(humidite > 70)   # Allume si humidité > 70%
    led_rouge.value(temperature < 19)  # Allume si température < 19°C

    # Publication des données sur MQTT
    client.publish(MQTT_TOPIC_TEMPERATURE, str(temperature))
    client.publish(MQTT_TOPIC_HUMIDITE, str(humidite))
    client.publish(MQTT_TOPIC_LUMINOSITE, str(luminosite))


    print(f"Temp\u00e9rature : {temperature} \u00b0C, Humidit\u00e9 : {humidite} %, Luminosit\u00e9 : {luminosite} %")

    # Pause avant la prochaine lecture
    time.sleep(5)

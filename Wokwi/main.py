# -*- coding: utf-8 -*-
"""
📡 Projet IoT Amilora - Surveillance Environnementale
Auteur: Francis Okechukwu
Description : Collecte de données DHT22 et transmission sécurisée via MQTT
"""

# ======================== #
#   📚 LIBRARIES IMPORT   #
# ======================== #
import network
import ujson
import time
import gc
import machine
import dht
from machine import Pin
from umqtt.simple import MQTTClient

# ======================== #
#   ⚙️ CONFIGURATION      #
# ======================== #

# 🖥️ Identification de l'appareil
DEVICE_ID = "Id01"

# 📶 Paramètres WiFi
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

# ☁️ Configuration MQTT (HiveMQ Cloud)
MQTT_BROKER = "280cab4fcbbd4de48b2a833de011802e.s1.eu.hivemq.cloud"
MQTT_PORT = 8883  # Port SSL/TLS
MQTT_USERNAME = "oussama"
MQTT_PASSWORD = "Wac@1937"
MQTT_TOPIC_TELEMETRY = "iot/telemetry"
MQTT_TOPIC_ERRORS = "iot/errors"

# 🌡️ Capteur DHT22
DHT_PIN = Pin(15)
dht_sensor = dht.DHT22(DHT_PIN)

# 💡 LED de statut
STATUS_LED = Pin(2, Pin.OUT)

# ======================== #
#   📡 FONCTIONS RESEAU   #
# ======================== #

def connect_wifi():
    """
    Établit la connexion WiFi avec gestion des erreurs
    """
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

    if not wifi.isconnected():
        print("Connexion au WiFi...")
        wifi.connect(WIFI_SSID, WIFI_PASSWORD)

        # Tentative de connexion pendant 15 secondes
        for _ in range(15):
            if wifi.isconnected():
                break
            print(".", end="")
            time.sleep(1)

        if not wifi.isconnected():
            raise RuntimeError("Échec de la connexion WiFi!")

    print("\n✅ WiFi connecté! IP:", wifi.ifconfig()[0])

def connect_mqtt():
    """
    Configure et connecte le client MQTT avec SSL
    """
    global mqtt_client
    gc.collect()  # Nettoyage mémoire

    try:
        # Création du client MQTT sécurisé
        mqtt_client = MQTTClient(
            client_id=DEVICE_ID,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            user=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            ssl=True,
            ssl_params={'server_hostname': MQTT_BROKER}
        )

        # Configuration des callback
        mqtt_client.set_callback(mqtt_callback)
        mqtt_client.connect()

        # Abonnement aux topics
        mqtt_client.subscribe(MQTT_TOPIC_TELEMETRY)
        print("✅ Connecté au broker MQTT et abonné aux topics")

        return True
    except Exception as e:
        print(f"❌ Erreur MQTT: {str(e)}")
        return False

def mqtt_callback(topic, message):
    """
    Gère les messages entrants MQTT
    """
    print(f"\n📩 Message reçu [{topic.decode()}]: {message.decode()}")

# ======================== #
#   🌡️ FONCTIONS CAPTEUR #
# ======================== #

def read_sensor():
    """
    Lit le capteur DHT22 avec réessais automatiques
    Retourne les données ou None en cas d'échec
    """
    for attempt in range(3):  # 3 tentatives
        try:
            dht_sensor.measure()
            return {
                "temp": dht_sensor.temperature(),
                "humidity": dht_sensor.humidity()
            }
        except Exception as e:
            print(f"⚠️ Erreur capteur (tentative {attempt+1}/3): {str(e)}")
            time.sleep(1)
    return None

# ======================== #
#   📨 FONCTIONS DONNÉES  #
# ======================== #

def send_telemetry(data):
    """
    Envoie les données de télémétrie au broker MQTT
    """
    payload = ujson.dumps({
        "device": DEVICE_ID,
        "timestamp": time.time(),
        "data": data
    })

    try:
        mqtt_client.publish(MQTT_TOPIC_TELEMETRY, payload)
        print(f"📨 Données envoyées: {payload}")
    except Exception as e:
        print(f"❌ Échec envoi télémétrie: {str(e)}")
        raise

def log_error(error):
    """
    Log les erreurs sur le topic dédié
    """
    try:
        payload = ujson.dumps({
            "device": DEVICE_ID,
            "error": str(error),
            "timestamp": time.time()
        })
        mqtt_client.publish(MQTT_TOPIC_ERRORS, payload)
    except:
        print("❌ Échec d'enregistrement de l'erreur")

# ======================== #
#   🎮 FONCTION PRINCIPALE #
# ======================== #

def main():
    """
    Boucle principale du programme
    """
    last_data = None
    led_state = False

    # Initialisation des connexions
    connect_wifi()

    if not connect_mqtt():
        machine.reset()

    while True:
        try:
            # Maintenance connexion MQTT
            mqtt_client.check_msg()

            # Lecture capteur avec feedback LED
            STATUS_LED.on()
            sensor_data = read_sensor()
            STATUS_LED.off()

            if sensor_data:
                # Envoi uniquement si nouvelles données
                if sensor_data != last_data:
                    send_telemetry(sensor_data)
                    last_data = sensor_data
                else:
                    print("🔄 Données identiques - Pas d'envoi")

            # Délai entre les lectures
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ Erreur critique: {str(e)}")
            log_error(e)
            time.sleep(10)
            machine.reset()

# ======================== #
#   🚀 LANCEMENT PROGRAMME #
# ======================== #
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Arrêt manuel")
    finally:
        machine.reset()
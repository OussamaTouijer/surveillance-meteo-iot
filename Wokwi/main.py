from machine import Pin
from umqtt.simple import MQTTClient
import ujson
import network
import utime as time
import dht

# Device Setup
DEVICE_ID = "Id01"

# WiFi Setup
WIFI_SSID       = "Wokwi-GUEST"
WIFI_PASSWORD   = ""

# MQTT Setup
MQTT_BROKER             = "08db0f1e29fb4484b93a955454a805e8.s1.eu.hivemq.cloud"
#MQTT_BROKER             = "broker.mqtt-dashboard.com"
MQTT_CLIENT             = DEVICE_ID
MQTT_TELEMETRY_TOPIC    = "iot/telemetry"

# DHT Sensor Setup
DHT_PIN = Pin(15)

FLASH_LED   = Pin(2, Pin.OUT)

# Methods
def did_recieve_callback(topic, message):
    print('\n\nData Recieved! \ntopic = {0}, message = {1}'.format(topic, message))
    # Disable all lamp-related logic
    if topic == MQTT_CONTROL_TOPIC.encode():
        if message == ('{0}/status'.format(DEVICE_ID)).encode() or message == ('status').encode():
            global telemetry_data_old
            mqtt_client_publish(MQTT_TELEMETRY_TOPIC, telemetry_data_old)
        else:
            return

def mqtt_connect():
    print("Connecting to MQTT broker ...", end="")
    mqtt_client = MQTTClient(MQTT_CLIENT, MQTT_BROKER, user="assalanass", password="Anass12345",ssl=True ,ssl_params={'server_hostname':MQTT_BROKER})
    #mqtt_client = MQTTClient(MQTT_CLIENT, MQTT_BROKER, user="", password=")
    
    mqtt_client.set_callback(did_recieve_callback)
    mqtt_client.connect()
    print("Connected.")
    return mqtt_client

def create_json_data(temperature, humidity):
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "temp": temperature,
        "humidity": humidity,
        "type": "sensor"
    })
    return data

def mqtt_client_publish(topic, data):
    print("\nUpdating MQTT Broker...")
    mqtt_client.publish(topic, data)
    print(data)


# Application Logic

# Connect to WiFi
wifi_client = network.WLAN(network.STA_IF)
wifi_client.active(True)
print("Connecting device to WiFi")
wifi_client.connect(WIFI_SSID, WIFI_PASSWORD)

# Wait until WiFi is Connected
while not wifi_client.isconnected():
    print("Connecting")
    time.sleep(0.1)
print("WiFi Connected!")
print(wifi_client.ifconfig())

# Connect to MQTT
mqtt_client = mqtt_connect()
dht_sensor = dht.DHT22(DHT_PIN)
telemetry_data_old = ""

while True:
    mqtt_client.check_msg()
    print(". ", end="")

    FLASH_LED.on()
    try:
      dht_sensor.measure()
    except:
      pass
    
    time.sleep(0.2)
    FLASH_LED.off()

    telemetry_data_new = create_json_data(dht_sensor.temperature(), dht_sensor.humidity())

    if telemetry_data_new != telemetry_data_old:
        mqtt_client_publish(MQTT_TELEMETRY_TOPIC, telemetry_data_new)
        telemetry_data_old = telemetry_data_new

    time.sleep(0.1)

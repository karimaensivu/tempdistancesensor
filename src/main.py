# Complete project details at https://RandomNerdTutorials.com/micropython-hc-sr04-ultrasonic-esp32-esp8266/
from machine import Pin, SoftI2C
import ssd1306, time
from hcsr04 import HCSR04
from time import sleep
from umqtt.simple import MQTTClient
import dht
import urequests as requests
import json


CLIENT_NAME = 'serverroom'
BROKER_ADDR = 'insert-ip-here'
mqttc = MQTTClient(CLIENT_NAME, BROKER_ADDR, keepalive=60)
mqttc.connect()

sensor_temp = dht.DHT11(Pin(19))

# ESP32 Pin assignment 
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
sensor_dist = HCSR04(trigger_pin=5, echo_pin=18, echo_timeout_us=10000)


oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
BTN_TOPIC = 'serverroom/distance'
BTN_TOPIC2 = 'serverroom/temperature'

lasttemp = 0
lasthum = 0
lastdist = 0
retVal = True


def get_url():
    post_url = 'https://virtual--karitraining.mevisio.com/endpoints/esp32IoT'
    
    return post_url

def dataToMevisio(temp,distance,humidity):
    post_data = { "temp": temp, "distance": distance, "humidity": humidity}
    header_data = {"authorization": 'retracted-for-reasons', "Content-Type": 'application/json'}
    print(post_data)
    req = requests.post(get_url(), json=post_data, headers=header_data)
    req.status_code
    req.close()

def compareValues(newtemp,newdist,newhum,oldtemp,olddist,oldhum):
    if newtemp == oldtemp:
        if newhum == oldhum:
            if newdist == olddist:
                return False
            else:
                return True
        else:
            return True
    else:
        return True

while True:
  oled.fill(0)
  #oled.show()
  distance = sensor_dist.distance_mm()
  print('Distance:', distance, 'mm')
  oled.text("Distance "+str(distance), 0, 16)
  try:
    sleep(0)
    sensor_temp.measure()
    temp = sensor_temp.temperature()
    hum = sensor_temp.humidity()
    temp_f = temp * (9/5) + 32.0
    print('Temperature: %3.1f C' %temp)
    print('Temperature: %3.1f F' %temp_f)
    print('Humidity: %3.1f %%' %hum)
  except OSError as e:
    print('Failed to read sensor.')
  
  
  
  oled.text('Temp ' +str(temp) + ' C', 0, 32)
  oled.text('Humidity '+str(hum), 0, 48)

  mqttc.publish( BTN_TOPIC, str(distance).encode() )
  mqttc.publish( BTN_TOPIC2, str(temp).encode())
  
  if distance < 0:
    print('Measuring error')
    retVal = compareValues(temp,0,hum,lasttemp,lastdist,lasthum)
    lastdist = 0
  elif distance > 1200:
    if distance < 1600:
      print('Door closed')
      retVal = compareValues(temp,3,hum,lasttemp,lastdist,lasthum)
      lastdist = 3
    else:
      print('Door open')
      retVal = compareValues(temp,2,hum,lasttemp,lastdist,lasthum)
      lastdist = 2
  else:
    print('someone in the room')
    retVal = compareValues(temp,1,hum,lasttemp,lastdist,lasthum)
    lastdist = 1
    
  lasthum = hum
  lasttemp = temp
  if retVal:
      dataToMevisio(temp, distance, hum)
  
  oled.show()
  sleep(15)
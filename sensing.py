# 17번 = 불꽃 감지 (input)
# 27번 = 온도 센서 (input)
# 22번 = 피에조 부저 (output)

import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import os
import socket # 통신을 위한 소켓. RPI가 서버로 동작. 후에 앱과 연동됨.
from twilio.rest import Client # 문자 전송 모듈
import requests # 서버에 전송 요청

fire_pin, temp_pin, buzzer_pin = 17, 27, 22

GPIO.setmode(GPIO.BCM) # GPIO 핀맵 사용
GPIO.setup(fire_pin, GPIO.IN) # 불꽃

temp_sensor = Adafruit_DHT.DHT11 # 온도 센서 객체 생성

GPIO.setup(buzzer_pin, GPIO.OUT) # 부저
GPIO.setwarnings(False) # 경고 무시

temp_thr = 25 # 온도 경계값. 특정 온도로 변경하고 싶으면 이 변수 변경할 것. 테스트 시 25도를 기준으로 함

pwm = GPIO.PWM(buzzer_pin, 1) # 부저 핀 지정, 주파수 지정.

# 메세지 전송을 위한 SID, 토큰, 클라이언트 객체 생성
account_sid = 'Input twilio SID'
auth_token = 'Input twilio AUTH TOKEN'
client = Client(account_sid, auth_token)

# 촬영 시작
os.system('sudo motion n &') # motion 스트리밍 커맨드

# http://203.253.128.177:7575/#!/monitor
# /Mobius/Fire_sensing로 접근 가능
# 온도 값 저장
url_temp = 'http://203.253.128.177:7579/Mobius/Fire_sensing/Temp' 

headers_temp =	{
        'Accept':'application/json',
        'X-M2M-RI':'12345',
        'X-M2M-Origin':'Fire_sensing',
        'Content-Type':'application/vnd.onem2m-res+json; ty=4'
}

# 불꽃 감지 센서 값 저장
url_fire = 'http://203.253.128.177:7579/Mobius/Fire_sensing/Fire'
headers_fire =	{
        'Accept':'application/json',
        'X-M2M-RI':'12345',
        'X-M2M-Origin':'Fire_sensing',
        'Content-Type':'application/vnd.onem2m-res+json; ty=4'
}

while(1):
    # 불꽃 센서
    print(f"The value of fire : {GPIO.input(fire_pin)}")

    # 섭씨, 습도
    hum, temp = Adafruit_DHT.read_retry(temp_sensor, temp_pin)   # 센서 객체에서 센서 값(습도, 온도) 읽기
    print(f"The value of Temp : {temp:0.1f}")

    data_temp =	{ # 지속적으로 데이터 갱신
        "m2m:cin": {
            "con": temp
        }
    }

    if (GPIO.input(fire_pin) == 1): # 화재 발생 시
        data_fire =	{
            "m2m:cin": {
                "con": "화재 발생"
            }
        }
    else:
        data_fire =	{
            "m2m:cin": {
                "con": "정상"
            }
        }

    requests.post(url_temp, headers=headers_temp, json=data_temp) # 서버에 온도 데이터 저장
    requests.post(url_fire, headers=headers_fire, json=data_fire) # 서버에 불꽃 신호 데이터 저장

    # 불꽃이 감지되거나 특정 온도 이상일 때
    if (GPIO.input(fire_pin) == True and (temp  >= temp_thr)):
        # 이 구간에 화재 감지 동작.

        print("fire detected.") 

        print("Send message")
        # 해당 메세지 객체 생성시 메시지 전송됨
        message = client.messages.create(
            body='화재가 감지되었습니다!',
            from_='+<--Virtual number(sender)--> ',
            to='+<--Receiver phone number-->' 
        )

        pwm.start(50)

        # for문 두개 -> 사이렌
        for i in range(300, 750):
            pwm.ChangeFrequency(i)
            time.sleep(0.01) # 1.5초간

        for i in range(750, 300, -1):
            pwm.ChangeFrequency(i)
            time.sleep(0.01) # 1.5초간
        
        pwm.stop() # 소리 중단
        
    else:
        print("nothing happened.")

    time.sleep(0.5) # 최소한의 딜레이를 걸어야 라파가 안뻗음.
#!/usr/bin/python
import spidev as SPI
import mercury

import RPi.GPIO as GPIO
import time


#initalize the led
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
led = 13
GPIO.setup(led, GPIO.OUT)

#initialize the distance sensor
GPIO_TRIGGER = 19
GPIO_ECHO = 26
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

reader = mercury.Reader("tmr:///dev/ttyS0")
reader.set_region("EU3")
reader.set_read_plan([1], "GEN2")

def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance

def read_card():
    reader = mercury.Reader("tmr:///dev/ttyS0")
    reader.set_region("EU3")
    reader.set_read_plan([1], "GEN2")
    data=reader.read()

    if(data):
        #GPIO.output(buzzer,GPIO.HIGH)
        b = data
        s = str(b)[1:-1]
        x = s.split("(")
        x = x[1].split(")")
        x = x[0]
        x = str(x)[1:-1]
        x = x.lstrip('\'')
        print(x)
        
        # when data is detected, turn on the led
        GPIO.output(led, GPIO.HIGH)

    else:
        #GPIO.output(buzzer,GPIO.LOW)
        print("no data")

        # when no data is detected, turn off the led
        GPIO.output(led, GPIO.LOW)
    

if __name__ == '__main__':
    try:
        while True:
            dist = distance()
            if dist <= 20:
                read_card()
            #print ("Measured Distance = %.1f cm" % dist)
            time.sleep(0.5)
            GPIO.output(led, GPIO.LOW)
 
        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
        
    
 

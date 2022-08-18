#!/usr/bin/python
import spidev as SPI
import mercury

import RPi.GPIO as GPIO
import time
import pandas as pd

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

def initReader():
    reader = mercury.Reader("tmr:///dev/ttyS0")
    reader.set_region("EU3")
    reader.set_read_plan([1], "GEN2")
    return reader

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
    reader = initReader()
    data = reader.read()

    if(data):
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

        # write the data to log file if the data is not already in the file
        with open('tag_reads.txt', 'a+') as f:
            if x not in f.read():
                f.write(x + '\n')
                f.close()
                print("data written to file")
            elif x in f.read():
                print("data already in file")
                f.close()

    else:
        print("no data")

        # when no data is detected, turn off the led
        GPIO.output(led, GPIO.LOW)
    
def authenticate():
    username = str(input("Enter your username: "))
    password = str(input("Enter your password: "))

    # read the data from the excel file
    usersFile = pd.read_excel('users.xls')

    # check if user is in the file
    if username in str(usersFile['username']):
        # check if password is correct
        if password == usersFile.loc[usersFile['username'] == username]['password'].values[0]:
            print("User authenticated")
            return True
        else:
            print("Password incorrect")
            return False
    else:
        print("User not found")
        return False


def register():
    username = str(input("Enter your username: "))

    # read the data from the file
    usersFile = pd.read_excel('users.xls')

    # check if username is already in the file
    if username in str(usersFile['username']):
        print("User already exists")
        return False
    else:
        password = input("Enter your password: ")
        # add the user to the file
        append_df_to_excel(pd.DataFrame([[username, password]], columns=['username', 'password']), 'users.xls')
        print("User registered")
        return True

def append_df_to_excel(df, excel_path):
    df_excel = pd.read_excel(excel_path)
    result = pd.concat([df_excel, df], ignore_index=True)
    result.to_excel(excel_path, index=False)

if __name__ == '__main__':
    try:
        choice = input("1. Authenticate\n2. Register\n3. Read card\n4. Exit\n")
        if str(choice) == "1":
            authenticate()
        elif choice == "2":
            register()
        elif choice == "3":
            while True:
                dist = distance()
                if dist <= 20:
                    read_card()
                #print ("Measured Distance = %.1f cm" % dist)
                time.sleep(0.5)
                GPIO.output(led, GPIO.LOW)
        elif choice == "4":
            print("Exiting")
            GPIO.cleanup()
    # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
        
    
 

#!/usr/bin/python
import spidev as SPI
import mercury

import RPi.GPIO as GPIO
import time
import pandas as pd
import datetime
import sqlite3 as sql
import shutil

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

username = ""

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

def read_card(checkIn):
    reader = initReader()
    data = reader.read()

    global username

    tagFile = pd.read_excel('tags.xls')

    # ask if user wants to check in or out


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


        if checkIn == "i":
            # write tag, current time, username and check in to the file
            append_df_to_excel(pd.DataFrame([[x, datetime.datetime.now(), username, "in"]], columns=['tag', 'time', 'user', 'in/out']), 'tags.xls')
        if checkIn == "o":
            # write tag, current time, username and check out to the file
            append_df_to_excel(pd.DataFrame([[x, datetime.datetime.now(), username, "out"]], columns=['tag', 'time', 'user', 'in/out']), 'tags.xls')
    
    else:
        print("no data")

        # when no data is detected, turn off the led
        GPIO.output(led, GPIO.LOW)
    
def authenticate():
    global username
    username = str(input("Enter your username: "))
    password = str(input("Enter your password: "))

    # check if username is in database.db
    conn = sql.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = '" + username + "'")
    if c.fetchone():
        c.execute("SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'")
        if c.fetchone():
            return True
        else:
            print("Incorrect password")
            return False
    else:
        print("Username does not exist")
        return False

def asset_check():
    # create table in database.db called assets
    conn = sql.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag INTEGER,
        time TEXT
        )''')
    conn.commit()

    # read tags
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

        # check if tag is already in database.db and if the timestamp is less than 30 seconds old
        conn = sql.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM assets WHERE tag = '" + x + "'")
        if c.fetchone():
            c.execute("SELECT * FROM assets WHERE tag = '" + x + "' AND time > datetime('now', '-30 seconds')")
            if c.fetchone():
                print("Tag already in database")
            else:
                # update tag and timestamp in database.db
                c.execute("UPDATE assets SET time = datetime('now') WHERE tag = '" + x + "'")
                conn.commit()
                conn.close()

        else:
            # write tag, current time to the database.db
            c.execute("INSERT INTO assets (tag, time) VALUES ('" + x + "', datetime('now'))")
            conn.commit()
            conn.close()

def register():
    username = str(input("Enter your username: "))

    # check if username is in database.db
    conn = sql.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = '" + username + "'")
    if c.fetchone():
        print("Username already exists")
        return False
    else:
        password = str(input("Enter your password: "))
        c.execute("INSERT INTO users (username, password) VALUES ('" + username + "', '" + password + "')")
        conn.commit()
        conn.close()
        return True

def append_df_to_excel(df, excel_path):
    df_excel = pd.read_excel(excel_path)
    result = pd.concat([df_excel, df], ignore_index=True, sort=True)
    result.to_excel(excel_path, index=False)

def create_database():
    #save database.db as a backup

    backup()

    conn = sql.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
        )''')
    conn.commit()
    conn.close()

def backup():
    shutil.copy('database.db', 'backup.db')
    
if __name__ == '__main__':
    try:
        create_database()
        choice = str(input("1. Authenticate\n2. Register\n3. Assets\n 4. Exit\n"))
        if str(choice) == "1":
            if authenticate():
                checkIn = input("Checking in or out? (i/o): ")
                while True:
                    dist = distance()
                    if dist <= 20:
                        read_card(checkIn)
                    #print ("Measured Distance = %.1f cm" % dist)
                    time.sleep(0.5)
                    GPIO.output(led, GPIO.LOW)
        elif choice == "2":
            register()
        elif choice == "3":
            if authenticate():
                while True:
                    dist = distance()
                    if dist <= 20:
                        asset_check()
                    time.sleep(0.5)
        else:
            print("Exiting")
            GPIO.cleanup()
    # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
        
    
 

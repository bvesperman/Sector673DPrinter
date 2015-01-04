#!/usr/bin/python
import sys
import time 
import datetime 
import RPi.GPIO as io 
import select
import SectorAdminSite
import RFIDDataAccess
import subprocess
import glob
import os
import Adafruit_CharLCDPlate
from Adafruit_I2C import Adafruit_I2C

class MachineLogic:

    rfid =0
    machineID = 7
    isbusy = False
    
    grams = 0
    lcd = Adafruit_CharLCDPlate.Adafruit_CharLCDPlate()
    prev = -1
    btn = ((lcd.SELECT, 'Select'),
           (lcd.LEFT  , 'Left'  ),
           (lcd.UP    , 'Up'    ),
           (lcd.DOWN  , 'Down'  ),
           (lcd.RIGHT , 'Right' ))
    authService = SectorAdminSite.SectorAdmin()
    lastpush = datetime.datetime.now()
    access = RFIDDataAccess.DataAccess()

    def Busy(self):
        return self.isbusy
    
    def Setup(self):

        io.setmode(io.BCM)

        self.lcd.begin(16, 2)	
        self.LCDRefresh = True
        self.currentstate = "IDLE"

    #// If a job has recently ended, report it
    def ReportJob(self):

        #newest = max(glob.iglob('/home/pi/ImageLog/*.jpg'), key=os.path.getctime)
        print(newest)
        jpgfile = open(newest).read()
        self.authService.AddMachinePayment(int(self.rfid),self.jobtime,self.machineID, '3D print for {0}'.format(self.jobtime),jpgfile)

    
    def CaptureImage(self):
        subprocess.call("/home/pi/grabPic.sh")

    def DoUnAuthorizedContinuousWork(self):
        self.CheckButton()
        self.UpdateLCD()
        timelapse = (datetime.datetime.now()-self.lastpush)
        if (timelapse.seconds > 30):
           self.grams = 0
           self.LCDRefresh = True
           self.currentstate = "IDLE"
           self.lastpush = datetime.datetime.now() + datetime.timedelta(days=10)

    def DoAuthorizedWork(self):
        user = self.access.GetUserByRFID(self.rfid)
        self.fullname = user
        self.authService.AddMachinePayment(int(self.rfid),self.grams,self.machineID, '3D print for {0}'.format(self.grams),"")
        self.currentstate = "PAYMENT"
        self.LCDRefresh = True
	

    def UpdateLCD(self):
        if self.LCDRefresh == True:
            if self.grams > 0:
                self.lcd.clear()
                self.lcd.message("grams:" + "{0}".format(self.grams) + "\n" + "Due:$" + "{0:0.2f}".format(float(self.grams)/18) )
            if self.currentstate== "PAYMENT":
                self.lcd.clear()
                self.lcd.message("  Thank You   \n" + self.fullname)
                self.grams = 0
                self.LCDRefresh = True
                self.currentstate = "IDLE"
                self.lastpush = datetime.datetime.now() + datetime.timedelta(days=10)
	        time.sleep(10)
                self.lcd.clear() 
                self.lcd.message(" Push Up/Down \nTo Set Weight ")

            elif self.currentstate== "ON":
                self.lcd.clear() 
                self.lcd.message("  Please Swipe  \n    RFID Tag   ")
            elif self.currentstate== "IDLE":
                self.lcd.clear() 
                self.lcd.message(" Push Up/Down \nTo Set Weight ")
                #self.lcd.message("  Please Turn  \n  On Machine ")


            self.LCDRefresh = False

            

    def SetBillingAccount(self, rfid):
        self.fullname = ''
        data = self.authService.GetUserByRFID(rfid)            
        self.fullname = data['FirstName'] + ' ' +data['LastName']
        print(self.fullname)
        self.billingRFID = rfid
              
        self.LCDRefresh = True


    def CheckButton(self):
        for self.b in self.btn:
	    if self.lcd.buttonPressed(self.b[0]):
                #if self.b is not self.prev:
		    print(self.b[1])

		    if self.b[1] == "Down":
                       if(self.grams != 0 ):
                          self.grams = self.grams - 1
                          print(self.grams)
                       self.lastpush = datetime.datetime.now()
                       self.LCDRefresh = True
		    if self.b[1] == "Up":                  
                       self.grams = self.grams + 1
                       print(self.grams)
                       self.lastpush = datetime.datetime.now()
                       self.LCDRefresh = True

		    #self.prev = self.b
                    self.LCDRefresh = True
                    self.currentstate = "INUSE"
             
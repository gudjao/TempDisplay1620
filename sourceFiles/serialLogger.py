import serial
import datetime
import ConfigParser
from time import sleep
import copy
import wx

import numpy as np
import time as time
import re
import binascii

CONFIG_PATH = 'tempDisplayConfig.txt'
COM_PORT = '/dev/ttyUSB0'
lockString = 'SYST:PASS:CDIS'
unlockString = 'SYST:PASS:CEN '
lockStatus = 'SYST:PASS:CEN:STAT?'
timeSet = 'SYST:TIME '
TIMEOUT_VALUE = 1.00

configDone = False
while not configDone:
    try:
        parser = ConfigParser.SafeConfigParser()
        parser.read(CONFIG_PATH)
        load = parser.get

        MAX_TEMP = float(load('Alarms', 'Temp max'))
        MIN_TEMP = float(load('Alarms', 'Temp min'))
        MAX_RH =  float(load('Alarms', 'RH max'))
        MIN_RH =  float(load('Alarms', 'RH min'))
        BAUDRATE = int(load('Device', 'Baudrate'))

        configDone = True
    except ConfigParser.NoSectionError:
        configDone = False
        import makeConfigFile
        makeConfigFile.createFile(CONFIG_PATH)
        print 'Config File Created'

def emptyLoggerBuffer(logger):
    received = 'x'
    while not(received == ''):
        received = logger.readline()

def errorCheck(currentReading, attempts,  oldReading = 'none'):
    if type(currentReading) == str:
        print 'String Detected!!!'
        return False
    elif oldReading == 'none':
        if (currentReading.tempF < 30) or (currentReading.tempF > 100):
            print 'Temp Range Error!!!'
            return False
        elif (currentReading.RH <10) or (currentReading.RH > 100):
            print 'RH range Error!!!'
            return False
        else:
            return True
    elif attempts > 0:
        if (abs(oldReading.tempF - currentReading.tempF)< 0.25) and (abs(oldReading.RH - currentReading.RH)<0.25):
            'Consecutive out of range readings!!!'
            return True
        else:
            if (currentReading.tempF < 30) or (currentReading.tempF > 100):
                print 'Temp Range Error!'
                return False
            elif (currentReading.RH <10) or (currentReading.RH > 100):
                print 'RH Range Error!'
                return False
            else:
                return True
    else:
        return (abs(oldReading.tempF - currentReading.tempF)< 5.0) and (abs(oldReading.RH - currentReading.RH)<5.0)


def getLocation(logger):
    logger.write("sens1:iden?\n")
    values = logger.readline()
    values = "".join(values.split())
    values = values.upper()
    return values

def getTempRH(logger):
    done = False
    repeatErrors = 0
    readRequest = "read?1\n"
    while not done:
        wx.Yield()
        logger.write(readRequest)
        rcvdString = logger.readline()
        wx.Yield()
        readings = "".join(rcvdString.split())   #get rid of spaces
        values = readings.split(",")            #convert to array of delimted strings
        done = True
        try:
            assert len(values) == 2
        except AssertionError:
            print 'Invalid reading!', datetime.datetime.now().strftime('%Y-%m%d %H:%M:%S')
            print '        Received: "', str(rcvdString), '"'
            done = False
            repeatErrors += 1
            logger.close()
            logger.open()
            logger.flush
            logger.flushInput
            logger.flushOutput
            wx.Yield()
        if repeatErrors >1:
            print 'Timed Out(Get RH)'
            return 'Timed Out!'
        else:
            emptyLoggerBuffer(logger)
        if done:
            try:
                x = float(values[1])
            except ValueError:
                print 'float temp Value error'
                print '      Received: "', str(values), '"'
                sleep(.125)
                logger.flushInput()
                logger.flushOutput()
                done = False
        if done:
            try:
                assert x > 0                #IF the 1620 is still in boot it will return 0.0 for temp and RH
            except AssertionError:
                print 'rh assertion error'
                done = False
    print values
    return values
    
    
def getDateTime(logger):
    done = False
    while not done:
        logger.write("syst:date?\n")
        unitDate = logger.readline()
        unitDate = "".join(unitDate.split())
        logger.write("syst:time?\n")
        unitTime = logger.readline()
        unitTime = "".join(unitTime.split())
        values = unitDate + ',' + unitTime
        done = True
        try:
            values = datetime.datetime.strptime(values, "%Y,%m,%d,%H,%M,%S")
        except ValueError:
            done = False
    return values

def getLoggerRecords():
    rcvdString = 'blank'
    idLocation = '1ID'
    loggerID = 'noData'
    records = []
    prevReadingTime = False
    
    with serial.Serial(COM_PORT, baudrate = BAUDRATE, timeout = 60) as logger:
        print 'Waiting for input'
        while rcvdString != '':
            rcvdString = logger.readline()
            if rcvdString != '':
                readings = "".join(rcvdString.split())   #get rid of spaces
                values = readings.split(",")            #convert to array of delimted strings
                if len(values) == 1:
                    values = values[0].split(":")
                    if values[0] == idLocation:
                        if values[1] == '':
                            idLocation = '2ID'
                        else:
                            loggerID = '"' + values[1] + '"'
                            print 'Logger ID: ', loggerID
                            logger.timeout = 15
                            wx.Yield()
                else:
                    values.append(loggerID)
                    record = reading()
                    unit = values[2]
                    if unit == "C":
                        record.tempC = float(values[1])
                        record.tempF = convertCtoF(record.tempC)
                    else:
                        record.tempF = float(values[1])
                        record.tempC = convertFtoC(record.tempF)
                    record.RH = float(values[3])
                    record.dateTime = datetime.datetime.strptime(values[0], '%m-%d-%Y%H:%M:%S')
                    record.location = values[len(values)-1]
                    record = getAlarms(record)
                    if prevReadingTime:
                        record.continuous = ((record.dateTime - prevReadingTime) < datetime.timedelta(minutes = 15))
                    else:
                        record.continuous = False
                    prevReadingTime = copy.deepcopy(record.dateTime)
                    if errorCheck(record, 0):
                        records.append(record)
                        #print record.location, record.tempF, record.RH, record.dateTime, record.continuous 
    return records
      
    

def getTempUnit(logger):
    done = False
    while not done:
        logger.write("unit:temp?\n")
        values = logger.readline()
        values = "".join(values.split())
        values = str(values)
        done = True
        try:
            assert values in ['C', 'F']
        except AssertionError:
            print 'Temp Unit assertion error'
            print '     Received: "', str(values), '"'
            sleep(5)
            done = False
    return values


def convertCtoF(tempC):
    tempC = float(tempC)
    tempF = (tempC * 1.8)+ 32.0
    tempF = "{0:.2f}".format(tempF)
    tempF = float(tempF)
    return tempF

def convertFtoC(tempF):
    tempF = float(tempF)
    tempC = (tempF - 32.0 )/1.8
    tempC = "{0:.2f}".format(tempC)
    tempC = float(tempC)
    return tempC

def getAlarms(rec):
    if rec.tempF > MAX_TEMP:
        rec.alarmTempHigh = True

    if rec.tempF < MIN_TEMP:
        rec.alarmTempLow = True

    if rec.RH > MAX_RH:
        rec.alarmRHHigh = True

    if rec.RH < MIN_RH:
        rec.alarmRHLow = True

    rec.alarm = (rec.alarmTempHigh or rec.alarmTempLow or
                 rec.alarmRHHigh or rec.alarmRHLow)
    return rec

def getReading(lastReading):
    done = False
    attempts = 0
    record = reading()
    with serial.Serial(COM_PORT, baudrate = BAUDRATE, timeout = TIMEOUT_VALUE) as logger:
        logger.flushInput()
        logger.flushOutput()
        rcvd = getTempRH(logger)
        while not done:
            wx.Yield()
            repeat = attempts > 0
            if repeat:
                badReading = copy.deepcopy(record)
            if rcvd == 'Timed Out!':
                print 'Reading Timed Out(getReading)'
                return 'Timeout Error'
            unit = getTempUnit(logger)
            wx.Yield()
            if unit == "C":
                record.tempC = float(rcvd[0])
                record.tempF = convertCtoF(record.tempC)
            else:
                record.tempF = float(rcvd[0])
                record.tempC = convertFtoC(record.tempF)
            record.RH = float(rcvd[1])
            if repeat:
                done = errorCheck(record, attempts, badReading)
            else:
                done = errorCheck(record, attempts, lastReading)
            attempts = attempts + 1
        record.dateTime = getDateTime(logger)
        wx.Yield()
        record.continuous = (record.dateTime - lastReading.dateTime) < datetime.timedelta(minutes = 15)
        record.location = getLocation(logger)
        wx.Yield()
        record = getAlarms(record)            
    return record

def getSingleReading():
    record = reading()
    attempts = 0
    badReading = False
    with serial.Serial(COM_PORT, baudrate = BAUDRATE, timeout = TIMEOUT_VALUE) as logger:
        logger.flushInput()
        logger.flushOutput()
        done = False
        rhSuccess = False
        emptyLoggerBuffer(logger)
        while not done:
            repeat = attempts > 0
            if repeat:
                badReading = copy.deepcopy(record)
            done = True
            while not rhSuccess:
                rhSuccess = True
                rcvd = getTempRH(logger)
                if  rcvd == 'Timed Out!':
                    if attempts < 5:
                        attempts += 1
                        rhSuccess = False
                    else:
                        print 'Reading Timed Out(getSingleReading)', attempts
                        return 'Timeout Error'
            unit = getTempUnit(logger)
            if unit == "C":
                record.tempC = float(rcvd[0])
                record.tempF = convertCtoF(record.tempC)
            else:
                record.tempF = float(rcvd[0])
                record.tempC = convertFtoC(record.tempF)

            record.RH = float(rcvd[1])
            if badReading:
                done = errorCheck(record, attempts, badReading)
            else:
                done = errorCheck(record, attempts)
            attempts = attempts + 1
        record.dateTime = getDateTime(logger)
        record.location = getLocation(logger)
        record = getAlarms(record)
        record.continuous = False            
    return record

def setLocation(password, name):
    with serial.Serial(COM_PORT, baudrate = BAUDRATE, timeout = TIMEOUT_VALUE) as logger:
        logger.flushInput()
        logger.flushOutput()
        logger.write(unlockString + password + '\n')
        logger.write(lockStatus + '\n')
        value = logger.readline()
        try:
            value = int(value)
        except ValueError:
            return('Invalid Status')
        try:
            assert(value == 1)
        except AssertionError:
            return('Wrong Password')
        logger.write("sens1:iden " + name + "\n")
        logger.write(lockString + '\n')
        return(0)

def setTime(password):
    password = str(password)
    with serial.Serial(COM_PORT, baudrate = BAUDRATE, timeout = TIMEOUT_VALUE) as logger:
        logger.flushInput()
        logger.flushOutput()
        logger.write(unlockString + password + '\n')
        logger.write(lockStatus + '\n')
        value = logger.readline()
        try:
            value = int(value)
        except ValueError:
            return('Invalid Status')
        try:
            assert(value == 1)
        except AssertionError:
            return('Wrong Password')
        
        sysTime = datetime.datetime.now()
        hh = str(sysTime.hour)
        mm = str(sysTime.minute)
        ss = str(sysTime.second)
        timeString = hh + ',' + mm + ',' + ss
        logger.write(timeSet + timeString + '\n')
        logger.write(lockString + '\n')
    return(0)


def reset():
    with serial.Serial(COM_PORT, baudrate = BAUDRATE, timeout = TIMEOUT_VALUE) as logger:
        logger.flushInput()
        logger.flushOutput()
        logger.write('*TST?\n')
        x = ''
        while x == '':
            x = logger.readline()
    return x

def readRecords():
    now = datetime.datetime.now()
    then = now - datetime.timedelta(days = 1)
    #dateRange = ('dat:rec:open ' + then.strftime('%Y,%m,%d,0,0,0,') + now.strftime('%Y,%m,%d,0,0,0'))
    dateRange = 'DAT:REC:OPEN 2019,9,7,22,50,0,2019,9,8,23,0,0'
    x = ''
    m = 'null'
    print 'Date Range: ', dateRange
    with serial.Serial(COM_PORT, timeout = TIMEOUT_VALUE) as logger:
        logger.flushInput()
        logger.flushOutput()
        logger.write(dateRange + '\n')
        lines = []
        tempLines = []
        tempLine = ''
        line = ''
        newLines = ''
        
        openBytes = 0
        overallBytes = 0
        tempBytes = 0
        
        m = ''
        done = 0
        while True :
            logger.write('DAT:REC:OPEN?\n')
            line = logger.readline().rstrip()
            print 'Response: ' + line
            openBytes = int(line)
            groups = int(openBytes / 256)
            remainder = openBytes - (groups * 256)
            print 'Groups: ', groups
            print 'Remainder: ', remainder
            if groups > 0 :
                group = 1
                while group <= groups :
                    group = group + 1
                    tempBytes = 0
                    tempLines = []
                    tempLine = ''
                    logger.write('DAT:REC:READ? 256\n')
                    print 'Group: ', group - 1
                    while True:
                        tempLine = logger.readline()
                        line = re.sub(r'.*#11', '', tempLine)
                        lines.append(line)
                        tempBytes = tempBytes + len(line)
                        if tempBytes >= 256 :
                            newLines = ''.join(lines)
                            overallBytes = overallBytes + tempBytes
                            print 'Size: ', tempBytes
                            break
                lastBytes = str(remainder)
                tempBytes = 0
                tempLines = []
                tempLine = ''
                logger.write('DAT:REC:READ? ' + lastBytes + '\n')
                print 'Remainder: ', remainder
                while True:
                    tempLine = logger.readline()
                    line = re.sub(r'.*#11','', ''.join(tempLine))
                    lines.append(line)
                    tempBytes = tempBytes + len(line)
                    print 'Size ' , tempBytes
                    if tempBytes >= remainder :
                        newLines = ''.join(lines)
                        overallBytes = overallBytes + tempBytes
                        print 'Size ' , tempBytes
                        print 'DONE'
                        break
                print 'Overall size: ', overallBytes
                print 'Output: ', newLines
                f = open('test_file.rec', 'wb')
                f.write(newLines)
                f.close
            else :
                break
        return
    return x

def openRecords(daysBack = 1):
    now = datetime.datetime.now()
    then = now - datetime.timedelta(days = daysBack)
    dateRange = ('dat:rec:open ' + then.strftime('%Y,%m,%d,0,0,0,')
                 + now.strftime('%Y,%m,%d,0,0,0'))
    x = ''
    m = 'null'
    with serial.Serial(COM_PORT, timeout = TIMEOUT_VALUE) as logger:
        logger.flushInput()
        logger.flushOutput()
        logger.write(dateRange + '\n')
        while not m == '':
            logger.write('dat:rec:read?\n')
            m = logger.read(1000)
            x += m
    return x

class reading():
    location =''
    tempF = ''
    tempC = ''
    RH = ''
    dateTime = ''
    alarm = False
    alarmTempHigh = False
    alarmTempLow = False
    alarmRHHigh = False
    alarmRHLow = False
    continuous = False

    def printReading(self):
        print '  Location: ', self.location
        print '    Temp F: ' , self.tempF
        print '    Temp C: ' , self.tempC
        print '        RH: ' , self.RH
        print '  DateTime: ' , self.dateTime
        print '    Alarms: ' , self.alarm
        print ' T-H Alarm: ', self.alarmTempHigh
        print ' T-L Alarm: ', self.alarmTempLow
        print ' H-H Alarm: ', self.alarmRHHigh
        print ' H-L Alarm: ', self.alarmRHLow
        print 'Continuous: ', self.continuous
        
            

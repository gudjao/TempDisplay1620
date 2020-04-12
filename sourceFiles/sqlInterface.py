import datetime
import sqlite3 as database
from serialLogger import reading, convertFtoC
from copy import deepcopy

DATE_SEARCH = 'select * from readings where dateTime > '
END_DATE_SEARCH = ' AND datetime < '
AREA_SEARCH = ' group by datetime having location = '
SEARCH_ORDER = ' order by datetime'

def __init__(*args,**kargs):
    pass

def getAllRecords(numHours, location):
    currentTime = datetime.datetime.now()
    searchTime = currentTime - datetime.timedelta(hours = numHours)
    record = reading()
    with database.connect('envDatabase.db') as conn:
        db = conn.cursor()
        tempArray = []
        rhArray = []
        dateArray = []
        searchPhrase = DATE_SEARCH + searchTime.strftime('%Y%m%d%H%M%S') + AREA_SEARCH + "'" +  location + "'" + SEARCH_ORDER
        try:
            for row in db.execute(searchPhrase):
                result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
                splitResult = result.split(',')
                splitResult[0] = str(splitResult[0]).replace('L', '')
                dateArray.append(datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S'))
                tempArray.append(float(splitResult[2]))
                rhArray.append(float(splitResult[3]))
        except:
            pass
        
    if len(tempArray) > 0:
        record.dateTime = datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S')
        record.location = splitResult[1]
        record.tempF = float(splitResult[2])
        record.tempC = convertFtoC(record.tempF)
        record.RH = float(splitResult[3])
        record.alarm = bool(int(splitResult[4]))
        record.alarmTempHigh = bool(int(splitResult[5]))
        record.alarmTempLow = bool(int(splitResult[6]))
        record.alarmRHHigh = bool(int(splitResult[7]))
        record.alarmRHLow = bool(int(splitResult[8]))
        record.continuous = bool(int(splitResult[9]))    
    return (tempArray, rhArray, dateArray, record)

def getCurrentRecords(numHours, location):
    currentTime = datetime.datetime.now()
    searchTime = currentTime - datetime.timedelta(hours = numHours)
    record = reading()
    with database.connect('envDatabase.db') as conn:
        db = conn.cursor()
        tempArray = []
        rhArray = []
        dateArray = []
        searchPhrase = DATE_SEARCH + searchTime.strftime('%Y%m%d%H%M%S') + AREA_SEARCH + "'" + location + "'" + SEARCH_ORDER
        try:
            for row in db.execute(searchPhrase):
                result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
                splitResult = result.split(',')
                if int(splitResult[9]) == 0:
                    tempArray[:] = []
                    rhArray[:] = []
                    dateArray[:] = []

                splitResult[0] = str(splitResult[0]).replace('L', '')
                dateArray.append(datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S'))
                tempArray.append(float(splitResult[2]))
                rhArray.append(float(splitResult[3]))
        except database.OperationalError:
            createTable()
            print 'Table Created!'

    if len(tempArray) > 0:
        record.dateTime = datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S')
        record.location = splitResult[1]
        record.tempF = float(splitResult[2])
        record.tempC = convertFtoC(record.tempF)
        record.RH = float(splitResult[3])
        record.alarm = bool(int(splitResult[4]))
        record.alarmTempHigh = bool(int(splitResult[5]))
        record.alarmTempLow = bool(int(splitResult[6]))
        record.alarmRHHigh = bool(int(splitResult[7]))
        record.alarmRHLow = bool(int(splitResult[8]))
        record.continuous = bool(int(splitResult[9]))
        if (datetime.datetime.now() - record.dateTime).seconds > 900:  #if more than 15 minutes have elapsed since the last record.
            tempArray[:] = []
            rhArray[:] = []
            dateArray[:] = []          
    return (tempArray, rhArray, dateArray, record)

def getRecordsByRange(startDate, endDate, location):
    with database.connect('envDatabase.db') as conn:
        db = conn.cursor()
        tempArray = []
        rhArray = []
        dateArray = []
        searchPhrase = (DATE_SEARCH + startDate.strftime('%Y%m%d%H%M%S') + END_DATE_SEARCH
                        + endDate.strftime('%Y%m%d%H%M%S') + AREA_SEARCH + "'" +  location + "'" + SEARCH_ORDER)
        try: 
            for row in db.execute(searchPhrase):
                result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
                splitResult = result.split(',')
                splitResult[0] = str(splitResult[0]).replace('L', '')
                dateArray.append(datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S'))
                tempArray.append(float(splitResult[2]))
                rhArray.append(float(splitResult[3]))
        except:
            pass
            
    return(tempArray, rhArray, dateArray)

def getFullRecordsByRange(startDate, endDate, location):
    record = reading()
    records = []
    with database.connect('envDatabase.db') as conn:
        db = conn.cursor()
        searchPhrase = (DATE_SEARCH + startDate.strftime('%Y%m%d%H%M%S') + END_DATE_SEARCH
                        + endDate.strftime('%Y%m%d%H%M%S') + AREA_SEARCH + "'" +  location + "'" + SEARCH_ORDER)
        #print searchPhrase
        try:
            for row in db.execute(searchPhrase):
                result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
                splitResult = result.split(',')
                splitResult[0] = str(splitResult[0]).replace('L', '')
                record.dateTime = datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S')
                record.location = splitResult[1]
                record.tempF = float(splitResult[2])
                record.tempC = convertFtoC(record.tempF)
                record.RH = float(splitResult[3])
                record.alarm = bool(splitResult[4])
                record.alarmTempHigh = bool(int(splitResult[5]))
                record.alarmTempLow = bool(int(splitResult[6]))
                record.alarmRHHigh = bool(int(splitResult[7]))
                record.alarmRHLow = bool(int(splitResult[8]))
                record.continuous = bool(int(splitResult[9]))
                records.append(deepcopy(record))
        except:
            pass
    return records

def addRecord(record):
    with database.connect('envDatabase.db') as conn:
        db = conn.cursor()
        readingTime = int(record.dateTime.strftime('%Y%m%d%H%M%S'))
        location = record.location
        tempF = record.tempF
        RH = record.RH
        alarm = int(record.alarm)
        alarmTH = int(record.alarmTempHigh)
        alarmTL = int(record.alarmTempLow)
        alarmRHH = int(record.alarmRHHigh)
        alarmRHL = int(record.alarmRHLow)
        continuous = int(record.continuous)
        db.execute('INSERT INTO readings (dateTime, location, tempF, rh, alarm, alarmTHigh, alarmTLow, alarmRHHigh, alarmRHLow, continuous) VALUES(?,?,?,?,?,?,?,?,?,?)',
               (readingTime, location, tempF, RH, alarm, alarmTH, alarmTL, alarmRHH, alarmRHL, continuous))
        conn.commit()

def addManyRecords(records):
    #print len(records)
    with database.connect('envDatabase.db') as conn:
        db = conn.cursor()
        while range(len(records)):
            this = records.pop()
            readingTime = int(this.dateTime.strftime('%Y%m%d%H%M%S'))
            location = this.location.replace(' ', '')
            tempF = this.tempF
            RH = this.RH
            alarm = int(this.alarm)
            alarmTH = int(this.alarmTempHigh)
            alarmTL = int(this.alarmTempLow)
            alarmRHH = int(this.alarmRHHigh)
            alarmRHL = int(this.alarmRHLow)
            continuous = int(this.continuous)
            db.execute('INSERT INTO readings (dateTime, location, tempF, rh, alarm, alarmTHigh, alarmTLow, alarmRHHigh, alarmRHLow, continuous) VALUES(?,?,?,?,?,?,?,?,?,?)',
                   (readingTime, location, tempF, RH, alarm, alarmTH, alarmTL, alarmRHH, alarmRHL, continuous))
        conn.commit()
        
def createTable():
    with database.connect('envDatabase.db') as conn:
        db = conn.cursor()
        db.execute("CREATE TABLE readings(dateTime INT, location TEXT, tempF REAL, rh REAL, alarm INT, alarmTHigh INT, alarmTLow INT, alarmRHHigh INT, alarmRHLow INT, continuous INT)")
        conn.commit()

def getLastRecord():
    record = reading()
    with database.connect('envDatabase.db') as conn:
        db = conn.cursor()
        for row in db.execute('SELECT * FROM readings ORDER BY dateTime DESC LIMIT 1'):
            result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","")
            splitResult = result.split(',')
            splitResult[0] = str(splitResult[0]).replace('L', '')
        record.dateTime = datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S')
        record.location = splitResult[1]
        record.tempF = float(splitResult[2])
        record.tempC = convertFtoC(record.tempF)
        record.RH = float(splitResult[3])
        record.alarm = bool(int(splitResult[4]))
        record.alarmTempHigh = bool(int(splitResult[5]))
        record.alarmTempLow = bool(int(splitResult[6]))
        record.alarmRHHigh = bool(int(splitResult[7]))
        record.alarmRHLow = bool(int(splitResult[8]))
        record.continuous = bool(int(splitResult[9]))
    return record

def storeBatchRecords(records):
    print 'Processing ', len(records), ' records for local storage'
    firstDateTime = records[0].dateTime - datetime.timedelta(minutes = 30)
    lastDateTime = records[len(records)-1].dateTime + datetime.timedelta(minutes = 30)
    locations = []
    recordsByLocation = []    
    storedDatesByLocation = []
    storeThese = []
    while len(records):
        currentRecord = records.pop(0)
        if currentRecord.location not in locations:
            locations.append(currentRecord.location)
            recordsByLocation.append([])
            storedDatesByLocation.append([])
        recordsByLocation[locations.index(currentRecord.location)].append(currentRecord)
    for i in range(len(locations)):
        records = getFullRecordsByRange(firstDateTime, lastDateTime, locations[i])
        print "Found " , len(records), ' for this location.'
        for m in range(len(records)):
            storedDatesByLocation[i].append(records[m].dateTime)
    for i in range(len(recordsByLocation)):
        records = recordsByLocation[i]
        while len(records) > 0:
            currentRecord = records.pop(0)
            if currentRecord.dateTime not in storedDatesByLocation[i]:
                storeThese.append(currentRecord)
    if len(storeThese):
        print 'Storing ', len(storeThese), ' records'
        addManyRecords(storeThese)    
    print 'Done adding records to local storage.'                       

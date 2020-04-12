import ConfigParser
import datetime
import MySQLdb as mysql
from serialLogger import reading, convertFtoC
from copy import deepcopy
import sqlInterface as localDb
import  wx

DATE_SEARCH = 'select * from readings where datetime > '
END_DATE_SEARCH = ' AND datetime < '
AREA_SEARCH = ' group by datetime having location = '
SEARCH_ORDER = ' order by datetime'
CONFIG_PATH = 'tempDisplayConfig.txt'

parser = ConfigParser.SafeConfigParser()
try:
    parser.read(CONFIG_PATH)
    load = parser.get
    SERVER_A = str(load('Network', 'ServerA address'))
    SERVER_B = str(load('Network', 'ServerB address'))

except ConfigParser.NoSectionError:
    SERVER_A = '127.0.0.1'
    SERVER_B = '127.0.0.1'

def __init__(*args,**kargs):
    pass

def getAllRecords(numHours, location):
    currentTime = datetime.datetime.now()
    searchTime = currentTime - datetime.timedelta(hours = numHours)
    record = reading()
    networkResult = True
    tempArray = []
    rhArray = []
    dateArray = []
    searchString =  """ select * from readings where datetime > {0} having location = {1} order by datetime"""
    searchPhrase = searchString.format(searchTime.strftime('%Y%m%d%H%M%S'), "'" + location + "'")
    print searchPhrase
    try:
        conn = mysql.Connect(SERVER_A, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
        db = conn.cursor()
    except mysql.OperationalError:
        try:
            conn = mysql.Connect(SERVER_B, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
            db = conn.cursor()
        except mysql.OperationalError:
            networkResult = False
    if networkResult:
        db.execute(searchPhrase)
        for row in db.fetchall():
            result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
            splitResult = result.split(',')
            splitResult.pop(0)
            splitResult[0] = str(splitResult[0]).replace('L', '')
            dateArray.append(datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S'))
            tempArray.append(float(splitResult[2]))
            rhArray.append(float(splitResult[3]))
        conn.close()

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
        else:
            return localDb.getAllRecords(numHours, location)
    else:
        return localDb.getAllRecords(numHours, location)

    return (tempArray, rhArray, dateArray, record)


def getCurrentRecords(numHours, location):
    currentTime = datetime.datetime.now()
    searchTime = currentTime - datetime.timedelta(hours = numHours)
    record = reading()
    tempArray = []
    rhArray = []
    dateArray = []
    searchString = """select * from readings where datetime > {0} having location = '{1}' order by datetime"""
    searchPhrase = searchString.format(searchTime.strftime('%Y%m%d%H%M%S'), location)
    print searchPhrase
    networkResult = True
    try:
        conn = mysql.Connect(SERVER_A, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
        db = conn.cursor()
    except mysql.OperationalError:
        print 'Server A connection failure.  Trying server B...'
        try:
            conn = mysql.Connect(SERVER_B, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
            print 'Server B connection successful.'
            db = conn.cursor()
        except mysql.OperationalError:
            networkResult = False
    if networkResult:
        db.execute(searchPhrase)
        for row in db.fetchall():
            result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '').replace(' ', '')
            splitResult = result.split(',')
            splitResult.pop(0)
            if int(splitResult[9]) == 0:
                tempArray[:] = []
                rhArray[:] = []
                dateArray[:] = []

            splitResult[0] = str(splitResult[0]).replace('L', '')
            dateArray.append(datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S'))
            tempArray.append(float(splitResult[2]))
            rhArray.append(float(splitResult[3]))
        conn.close()


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
        else:
            return localDb.getCurrentRecords(numHours, location)
    else:
        return localDb.getCurrentRecords(numHours, location)

    return (tempArray, rhArray, dateArray, record)

def getRecordsByRange(startDate, endDate, location):
    tempArray = []
    rhArray = []
    dateArray = []
    searchString = """select * from readings where datetime > {0}  AND datetime < {1} having location = '{2}' order by datetime"""
    searchPhrase = searchString.format(startDate.strftime('%Y%m%d%H%M%S'), endDate.strftime('%Y%m%d%H%M%S'), location)
    print searchPhrase
    networkResult = True
    try:
        conn = mysql.Connect(SERVER_A, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
        db = conn.cursor()
    except mysql.OperationalError:
        print 'Server A connection failure.  Trying server B...'
        try:
            conn = mysql.Connect(SERVER_B, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
            print 'Server B connection successful.'
            db = conn.cursor()
        except mysql.OperationalError:
            networkResult = False

    if networkResult:
        db.execute(searchPhrase)
        for row in db.fetchall():
            result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
            splitResult = result.split(',')
            splitResult.pop(0)
            splitResult[0] = str(splitResult[0]).replace('L', '')
            dateArray.append(datetime.datetime.strptime(splitResult[0],'%Y%m%d%H%M%S'))
            tempArray.append(float(splitResult[2]))
            rhArray.append(float(splitResult[3]))
        conn.close()
        if len(tempArray) == 0:
            return localDb.getRecordsByRange(startDate, endDate, location)
    else:
        return localDb.getRecordsByRange(startDate, endDate, location)

    return(tempArray, rhArray, dateArray)

def getFullRecordsByRange(startDate, endDate, location):
    record = reading()
    records = []
    networkResult = True
    searchString = """select * from readings where datetime > {0}  AND datetime < {1} having location = '{2}' order by datetime"""
    searchPhrase = searchString.format(startDate.strftime('%Y%m%d%H%M%S'), endDate.strftime('%Y%m%d%H%M%S'), location)
    print searchPhrase
    try:
        conn = mysql.Connect(SERVER_A, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
        db = conn.cursor()
    except mysql.OperationalError:
        print 'Server A connection failure.  Trying server B...'
        try:
            conn = mysql.Connect(SERVER_B, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
            print 'Server B connection successful.'
            db = conn.cursor()
        except mysql.OperationalError:
            networkResult = False

    if networkResult:
        db.execute(searchPhrase)
        for row in db.fetchall():
            result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
            splitResult = result.split(',')
            splitResult.pop(0)
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
            records.append(deepcopy(record))
        conn.close()
    if len(records) == 0:
        return localDb.getFullRecordsByRange(startDate, endDate, location)

    return records

def getNetworkFullRecordsByRange(startDate, endDate, location):
    record = reading()
    records = []
    networkResult = True
    searchString = """SELECT * FROM readings WHERE datetime > {0} AND datetime < {1} HAVING location = '{2}'"""
    searchPhrase =searchString.format(startDate.strftime('%Y%m%d%H%M%S'), endDate.strftime('%Y%m%d%H%M%S'), location)
    #print searchPhrase
    try:
        conn = mysql.Connect(SERVER_A, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 60)
        db = conn.cursor()
    except mysql.OperationalError:
        print 'Server A connection failure.  Trying server B...'
        try:
            conn = mysql.Connect(SERVER_B, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 60)
            print 'Server B connection successful.'
            db = conn.cursor()
        except mysql.OperationalError:
            networkResult = False
    if networkResult:
        db.execute(searchPhrase)
        for row in db.fetchall():
            result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
            splitResult = result.split(',')
            splitResult.pop(0)
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
            records.append(deepcopy(record))
        conn.close()
    return records

def addRecord(record):
    networkStatus = 0
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
    wx.Yield()
    localDb.addRecord(record)

    try:
        conn = mysql.Connect(SERVER_A, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
        wx.Yield()
        db = conn.cursor()
        db.execute('INSERT INTO readings (dateTime, location, tempF, rh, alarm, alarmTHigh, alarmTLow, alarmRHHigh, alarmRHLow, continuous) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                   (readingTime, location, tempF, RH, alarm, alarmTH, alarmTL, alarmRHH, alarmRHL, continuous))
        conn.commit()
    except mysql.OperationalError:
            wx.Yield()
            print 'Network SQL connection failure!  Record saved on local storage only!'
            neworkStatus = 2
    conn.close()
    return networkStatus

def addManyRecords(records):
    try:
        conn = mysql.Connect(SERVER_A, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
        print 'Server A connection successful.'
        db = conn.cursor()
    except mysql.OperationalError:
        print 'Network SQL connection failure!  Record saved on local storage only!'
        return 2

    for i in range(len(records)):
        readingTime = int(records[i].dateTime.strftime('%Y%m%d%H%M%S'))
        location = records[i].location
        tempF = records[i].tempF
        RH = records[i].RH
        alarm = int(records[i].alarm)
        alarmTH = int(records[i].alarmTempHigh)
        alarmTL = int(records[i].alarmTempLow)
        alarmRHH = int(records[i].alarmRHHigh)
        alarmRHL = int(records[i].alarmRHLow)
        continuous = int(records[i].continuous)
        db.execute('INSERT INTO readings (dateTime, location, tempF, rh, alarm, alarmTHigh, alarmTLow, alarmRHHigh, alarmRHLow, continuous) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                   (readingTime, location, tempF, RH, alarm, alarmTH, alarmTL, alarmRHH, alarmRHL, continuous))
    conn.commit()
    conn.close()
    return 1

def discoTest():
    msg = []
    start = datetime.datetime.now()
    try:
        conn = mysql.Connect(SERVER_A, '', 'LEM1620', 'envDatabase', connect_timeout = 30)
        msg.append('Server A Connected')

    except mysql.OperationalError:
        msg.append('Trying Server B')

        try:
            conn = mysql.Connect(SERVER_B, '', 'LEM1620', 'envDatabase', connect_timeout = 30)
            msg.append('Server B Connected')

        except mysql.OperationalError:
            msg.append('No Network Connection')
            msg.append('Test Failed')
            end = datetime.datetime.now() - start
            msg.append(end)
            return msg

    end = datetime.datetime.now() - start
    msg.append(end)
    msg.append('Test Complete.  Would be successful')
    return msg

def getLastRecord():
    record = reading()
    networkResult = True
    searchPhrase = ('SELECT * FROM readings WHERE location = ' + "'" +  location + "'" + 'ORDER BY dateTime DESC LIMIT 1')
    try:
        conn = mysql.Connect(SERVER_A, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
        db = conn.cursor()

    except mysql.OperationalError:
        print 'Server A connection failure.  Trying server B...'
        try:
            conn = mysql.Connect(SERVER_B, 'pi', 'LEM1620', 'envDatabase', connect_timeout = 30)
            print 'Server B connection successful.'
            db = conn.cursor()

        except mysql.OperationalError:
            networkResult = False
            print 'Network SQL connection failure!  Using local storage only!'
            conn = databse.connect('envDatabase.db')
            db = conn.cursor()

    if networkResult:
        db.execute(searchPhrase)
        for row in db.fetchall():
            result = str(row).replace('(','').replace(')','').replace('u\'','').replace("'","").replace(' ', '')
            splitResult = result.split(',')
            splitResult.pop(0)
            splitResult[0] = str(splitResult[0]).replace('L', '')

        conn.close()
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
    print 'Processing ', len(records), ' records for network storage'
    firstDateTime = records[0].dateTime - datetime.timedelta(minutes = 30)
    lastDateTime = records[len(records)-1].dateTime + datetime.timedelta(minutes = 30)
    locations = []
    recordsByLocation = []
    storedDatesByLocation = []
    storeThese = []
    toLocal = deepcopy(records)
    localDb.storeBatchRecords(toLocal)
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
    print 'Done adding records to network'

def syncDatabases(numDays, location):
    networkDates = []
    localDates = []
    networkStore = []
    localStore = []
    endDate = datetime.datetime.now()
    startDate = endDate - datetime.timedelta(days = numDays)
    print "Syncing databases between ", startDate, " and ", endDate,  " for location " , location, "."
    print "Getting network values, this may take some time."
    networkValues = getNetworkFullRecordsByRange(startDate, endDate, location)
    print "Found ", len(networkValues), " records in the network database"
    print "Getting local values.  This should be faster"
    localValues = localDb.getFullRecordsByRange(startDate, endDate, location)
    print "Found ", len(localValues), " in the local database."
    print "Comparing retrieved values.  This may take a while."

    for i in range(len(networkValues)):
        networkDates.append(networkValues[i].dateTime)
    for i in range(len(localValues)):
        localDates.append(localValues[i].dateTime)
    while len(networkValues):
        this = networkValues.pop()
        if this.dateTime not in localDates:
            localStore.append(this)
    while len(localValues):
        this = localValues.pop()
        if this.dateTime not in networkDates:
            networkStore.append(this)
    print "Evaluation complete"
    print "Adding ", len(networkStore), " to network database and ", len(localStore), " to local database."
    addManyRecords(networkStore)
    localDb.addManyRecords(localStore)
    print "Syncronization complete"

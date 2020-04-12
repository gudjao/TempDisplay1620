import  tempDisplay/sourceFiles/networkSqlInterface as sql

print """           ENVIRONMENTAL DATABASE SYNCRONIZATION TOOL
 You should only need to use this when setting up a new server or montior unit.
 The program will automatically reconcile out of sync data for the last 7 days within 24 hours.

 When promted input the number of days back and the location you would like to sync.
 Entering QUIT for either value will end this program.\n\n"""

done = 'QUIT'
numDays = 0

while numDays == 0:
    entry = raw_input('Number of days back to sync: ')
    if ((entry.upper()).find('QUIT')) >= 0:
        exit
    try:
        numDays = int(entry)
    except ValueError:
        print 'Number of days must be an integer.  You entered "', entry, '".'
    if numDays <= 0:
        print 'Number of days must be greater than 0.'
        numDays = 0

entry = raw_input('Location to sync: ')
location = entry.upper()
if location.find(done ) >= 0:
    quit

location.replace("'", '')
location.replace('"', '')
location = '"'+ location + '"'
sql.syncDatabases(numDays, location)


 
 


def createFile(fileName):
    fileName = str(fileName)
    with open(fileName, 'w') as configfile:
        write = configfile.write
        write(';This is the configuration file for the 1620 display program \n')
        write(';It is advisable to backup this file before making any changes \n')
        write('\n')
        write('[Version]\n')
        write('config version = 1.0\n')
        write('\n')
        write(';When entering times, us 24 hour HHMM format e.g. 0700 or 1630\n')
        write(';For Air Force folks 7 A.M. is 0700 and 4:30 P.M. is 1630\n')
        write('\n')
        write('[Times]\n')
        write('TV on = 0600\n')
        write('TV off = 1730\n')
        write('Duty start = 0700\n')
        write('Duty stop  = 1630\n')
        write('Short day = 7 ; Do you have a regularly shortend duty day 0 = Monday ... 6 = Sunday 7 = No Short Day\n')
        write('Hours short = 1 ; How many hours early do you leave on the short day .5 = 30 minutes, 1 = 1 hour\n')
        write('End of day sound = True ;Play a sound at the end of the duty day\n')
        write('\n')
        write('[Device]\n')
        write('Update frequency = 7000 ;how often to take a reading from the 1620 in milliseconds\n')
        write('Record time = 300000 ;how often to store a record in milliseconds\n')
        write('Max reading age = 30 ;how old a reading can be before an error displayed\n')
        write('Stored hours = 8 ;number of hours to store for the stats display\n')
        write('1620 password = 1620\n')
        write('Display correction = 2.65 ;Use this to correct for diffrent screen formats\n')
        write('Baudrate = 57600 ; The device baudrate setting\n')
        write('\n')
        write('[Alarms]\n')
        write(';These settings are in %RH\n')
        write('RH max = 50.0\n')
        write('RH min = 20.0\n')
        write('RH nominal = 35.0\n')
        write('RH tolerance = 15.0\n')
        write('RH borderline = 3.0 ; the threshold to turn the screen yellow\n')
        write('\n')
        write(';These settings are in Fahrenheit Degrees\n')
        write('Temp max = 79.0\n')
        write('Temp min = 67.0\n')
        write('Temp nominal = 73.0\n')
        write('Temp tolerance = 6.0\n')
        write('Temp borderline = 1.0\n')
        write('\n')
        write('[Network]\n')
        write('Use network time = True ;set to True if network time service is availible.  False relies on the 1620 clock.\n')
        write('Use network storage = True ;set True if running a network database server.  Falsie uses local storage only.\n')
        write('ServerA address = 192.168.0.10\n')
        write('ServerB address = 192.168.0.11\n')
        
        

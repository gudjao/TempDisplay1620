from subprocess import call
import serialLogger as logger

def setTime():
        try:
                strTime = logger.getSingleReading().dateTime.strftime("%Y/%m/%d %H:%M:%S")
        except:
                return False
        call(["sudo", "date", "-s", strTime])
        call (["xset", "s", "noblank"])
        call (["xset", "s", "off"])
        call (["xset", "-dpms"])
        return True
	

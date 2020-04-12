import subprocess

def ootContinues():
        subprocess.Popen(["omxplayer", "/home/pi/tempDisplay/media/ootContinues.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def ootNotification():
        subprocess.Popen(["omxplayer", "/home/pi/tempDisplay/media/ootNotification.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def quittinTime():
        subprocess.Popen(["omxplayer", "/home/pi/tempDisplay/media/quittinTime.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                        



        

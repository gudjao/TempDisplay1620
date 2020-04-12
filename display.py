# -*- coding: utf-8 -*-
# import library modules
import copy
import ConfigParser
import datetime
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plot
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
     FigureCanvasWxAgg as FigureCanvas, \
     FigureManager
from subprocess import call
import time
import wx
import wx.lib.agw.aui as agw
#from agw import advancedsplash as AS
import wx.aui
import thread

# import local modules
from sourceFiles import soundAlerts as alert
from sourceFiles import serialLogger as logger
from sourceFiles import setSystTime as setTime
from sourceFiles import wxGrapher as staticGrapher
from multiprocessing import Pool


AFFIRMATIVE = ['True', 'true', 'Yes', 'yes', '1']
NEGATIVE = ['', 'False', 'false', 'No', 'no', '0']
CONFIG_PATH = 'tempDisplayConfig.txt'

pool = Pool()

done = False
while not done:
    try:
        parser = ConfigParser.SafeConfigParser()
        parser.read(CONFIG_PATH)
        load = parser.get

        CONTINUTIY_TIME  = int(load('Device', 'Max reading age'))
        DISPLAY_UPDATE_TIME = int(load('Device', 'Update frequency'))
        DATA_RECORD_TIME = int(load('Device', 'Record time'))
        DATA_HOURS = int(load('Device', 'Stored hours'))
        startTime = time.strptime(load('Times', 'TV on'), '%H%M')
        DTY_START_HRS = startTime.tm_hour
        DTY_START_MINS = startTime.tm_min
        stopTime = time.strptime(load('Times', 'TV off'), '%H%M')
        DTY_STOP_HRS = stopTime.tm_hour
        DTY_STOP_MINS = stopTime.tm_min
        QUITTIN_TIME = load('Times', 'Duty stop')
        SHORT_DAY = int(load('Times', 'Short day'))
        SHORT_HOURS = float(load('Times', 'Hours short'))
        END_OF_DAY_SIGNAL =  (load('Times', 'End of day sound') in AFFIRMATIVE)

        ENV_OUT_COLOR = load('Color', 'Env out background')
        ENV_IN_COLOR = load('Color', 'Env in background')
        ENV_BORDERLINE_COLOR = load('Color', 'Env borderline background')
        
        ENV_OUT_FONT_COLOR = load('Color', 'Env out font')
        ENV_IN_FONT_COLOR = load('Color', 'Env in font')
        ENV_BORDERLINE_FONT_COLOR = load('Color', 'Env borderline font')
        
        RH_BORDERLINE_LEVEL = float(load('Alarms', 'RH borderline'))
        RH_MAX = float(load('Alarms', 'RH max'))
        RH_MIN = float(load('Alarms', 'RH min'))
        RH_NOMINAL = float(load('Alarms', 'RH nominal'))
        RH_TOLERANCE = float(load('Alarms', 'RH tolerance'))
        TEMP_NOMINAL = float(load('Alarms', 'Temp nominal'))
        TEMP_TOLERANCE = float(load('Alarms', 'Temp tolerance'))
        TEMP_MAX = float(load('Alarms', 'Temp max'))
        TEMP_MIN = float(load('Alarms', 'Temp min'))
        TEMPF_BORDERLINE_LEVEL = float(load('Alarms', 'Temp borderline'))

        USE_NETWORK_TIME = (load('Network', 'Use network time') in AFFIRMATIVE)
        LOGGER_PASSWORD = load('Device', '1620 password')
        DISPLAY_RATIO_CORRECTION = float(load('Device', 'Display correction'))
        if (load('Network', 'Use network storage') in AFFIRMATIVE):
            from sourceFiles import networkSqlInterface as sql
            print 'Using Network Database!'
        else:
            from sourceFiles import sqlInterface as sql
            print 'Local Storage Only!'
        done = True
    except ConfigParser.NoSectionError:
        done = False
        from sourceFiles import makeConfigFile
        makeConfigFile.createFile(CONFIG_PATH)
        print 'Config File Created'

class DisplayFrame(wx.Frame):

    def __init__(self, parent, id=-1, title='Environmental Data',
                 pos=wx.DefaultPosition, size=(700, 500),
                 style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        #Define Variables
        self._mgr = wx.aui.AuiManager(self)
        self._mgr.SetDockSizeConstraint(.85,.85)
        self.tempArray = []
        self.rhArray = []
        self.dateArray = []
        self.tMax = 0
        self.tMin = 0
        self.rhMax = 0
        self.rhMin = 0
        self.readingTimer = wx.Timer(self, 1)
        self.storageTimer = wx.Timer(self, 3)
        self.clockTimer = wx.Timer(self, 2)
        self.disableScreenSaverTimer = wx.Timer(self, 4)
        self.enableScreenSaverTimer = wx.Timer(self, 5)
        self.displaySize = wx.DisplaySize()
        self.displayWidth = self.displaySize[0]
        self.displayHeight = self.displaySize[1]
        self.resolution = wx.ScreenDC().GetPPI()
        self.graphingAvailiable = True
        self.lastRecordTime = ''
        self.lastStoredRecord = ''
        self.missedReadings = 0

        # Turn off screenSaver
        self.disbleScreenSaver()
        #Sync the system time with the 1620
        #The setTime.setTime pulls a reading from the 1620 to minimize the delay
        if not setTime.setTime():
            errMsg = wx.MessageDialog(self, 'The envrionmental monitor is not responding. \n Verify the connection to the display module. \n Press "OK" to retry or "Cancel to close the program"',
                                      'No Data Received', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
            retry = errMsg.ShowModal() == wx.ID_OK
            if retry:
                if not setTime.setTime():
                    repeatErrMsg = wx.MessageDialog(self, 'The envrionmental monitor is still not responding. \n Rebooting the display module usually fixes this \n Press "OK" to reboot or "Cancel to close the program"',
                                                    'No Data Received', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
                    reboot = repeatErrMsg.ShowModal() == wx.ID_OK
                    if reboot:
                        call (["sudo", "reboot"])
                    else:
                         self._mgr.UnInit()
                         # delete the frame
                         self.Destroy()
                         quit()
            else:
                 self._mgr.UnInit()
                 self.Destroy()
                 quit()

        #Get the intial reading from the 1620 so we have some data to work with
        self.record = logger.getSingleReading()

        # Populate Arrays
        data = sql.getCurrentRecords(DATA_HOURS, self.record.location)
        if len(data[0]) > 0:
            self.tempArray = data[0]
            self.rhArray = data[1]
            self.dateArray = data[2]
            self.lastStoredRecord = data[3]
            self.record = logger.getReading(self.lastStoredRecord)

        #Build Menu Bar
        menuBar = wx.MenuBar()
        fileButton = wx.Menu()
        viewButton = wx.Menu()

        #Add Panels
        self.mainPanel = wx.Panel(self)
        self.secondPanel = wx.Panel(self, size = (self.displayWidth,self.displayHeight))
        self.nb = agw.AuiNotebook(self.secondPanel, size = (self.displayWidth,self.displayHeight/DISPLAY_RATIO_CORRECTION))
        self.nb.SetAGWWindowStyleFlag(agw.AUI_NB_BOTTOM)
        self.nb.SetArtProvider( agw.VC71TabArt() )
        self.statsPage = wx.Panel(self)
        self.utilityPage = wx.Panel(self)
        self.fxPage = wx.Panel(self)
        self.graphPage = wx.Panel(self)
        self.quitPage = wx.Panel(self)

        #Create the page for the the realTime graph
        self.graphFigure = Figure(((self.displayWidth)/self.resolution[0],(self.displayHeight*.47)/self.resolution[1]))
        self.graphCanvas = FigureCanvas(self.graphPage, -1, self.graphFigure)
        self.figmgr = FigureManager(self.graphCanvas, 1, self)

        #The utility page buttons
        self.deviceColLabel = wx.StaticText(self.utilityPage, wx.ID_ANY,'    1620 Interface     ')
        self.piColLabel = wx.StaticText(self.utilityPage, wx.ID_ANY,'  Raspberry Pi Control ')
        self.shutDownButton = wx.Button(self.utilityPage, wx.ID_ANY,'           Shut Down           ')
        self.restartButton = wx.Button(self.utilityPage, wx.ID_ANY,'             Restart                ')
        self.ejectDriveButton = wx.Button(self.utilityPage, wx.ID_ANY,'      Eject Flash Drive      ')
        self.fullScreenButton = wx.Button(self.utilityPage, wx.ID_ANY,'Toggle Full Screen Mode')
        self.replaceSensorButton = wx.Button(self.utilityPage, wx.ID_ANY,'       Replace Sensor      ')
        self.getStoredDataButton = wx.Button(self.utilityPage, wx.ID_ANY,'   Get Data From 1620  ')

        #The view data page
        createGraphLabel = wx.StaticText(self.fxPage, -1, 'Create Graph')
        self.tempCheckBox = wx.CheckBox(self.fxPage, wx.ID_ANY, 'Temp '+ u"\u00b0" +'F')
        self.tempCheckBox.SetValue(True)
        self.rhCheckBox = wx.CheckBox(self.fxPage, wx.ID_ANY, '%RH')
        self.rhCheckBox.SetValue(True)
        self.startDateLabel = wx.StaticText(self.fxPage, -1,('From '))
        self.startDatePicker = wx.DatePickerCtrl(self.fxPage)
        self.endDateLabel = wx.StaticText(self.fxPage, -1, 'To      ')
        self.endDatePicker = wx.DatePickerCtrl(self.fxPage)
        self.graph12 = wx.Button(self.fxPage, wx.ID_ANY, 'Past 12 Hours')
        self.graph24 = wx.Button(self.fxPage, wx.ID_ANY, 'Past 24 Hours')
        self.graph168 = wx.Button(self.fxPage, wx.ID_ANY, '  Past 7 Days  ')
        self.graphRange = wx.Button(self.fxPage, wx.ID_ANY, '       Custom Range      ')

        #Page sizers are here
        deviceCol = wx.BoxSizer(wx.VERTICAL)
        piCol = wx.BoxSizer(wx.VERTICAL)
        utilitySizer = wx.BoxSizer(wx.HORIZONTAL)
        fxColLeft = wx.BoxSizer(wx.VERTICAL)
        fxColRight = wx.BoxSizer(wx.VERTICAL)
        fxRowOne = wx.BoxSizer(wx.HORIZONTAL)
        fxRowFour = wx.BoxSizer(wx.HORIZONTAL)
        fxRowFive = wx.BoxSizer(wx.HORIZONTAL)
        fxMainBox = wx.BoxSizer(wx.VERTICAL)
        fxTop = wx.BoxSizer(wx.HORIZONTAL)
        fxBottom = wx.BoxSizer(wx.HORIZONTAL)
        fxStartRow = wx.BoxSizer(wx.HORIZONTAL)
        fxEndRow = wx.BoxSizer(wx.HORIZONTAL)
        topBox = wx.BoxSizer(wx.VERTICAL)
        lowerBox = wx.BoxSizer(wx.VERTICAL)
        quitTimeBox = wx.BoxSizer(wx.VERTICAL)
        self.graphBox = wx.BoxSizer(wx.VERTICAL)

        #Define the program fonts
        TEMP_FONT = wx.Font((self.displayWidth/12.75), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL)
        RH_FONT = wx.Font((self.displayWidth/12.75), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL)
        DATE_FONT = wx.Font((self.displayWidth/16), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL)
        TIME_FONT = wx.Font((self.displayWidth/20), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL)
        DELTA_FONT = wx.Font((self.displayWidth/25), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL)
        UTILITY_FONT = wx.Font((self.displayWidth/65), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.NORMAL)

        #Add data to Main Display
        tempString = self.createTempString()
        self.tempText = wx.StaticText(self.mainPanel, -1, tempString)
        self.tempText.SetFont(TEMP_FONT)
        self.tempText.SetForegroundColour('Black')

        self.rhText = wx.StaticText(self.mainPanel, -1, self.createRhString())
        self.rhText.SetFont(RH_FONT)
        self.rhText.SetForegroundColour('Black')

        self.clockText = wx.StaticText(self.mainPanel, -1, datetime.datetime.now().strftime('%Y/%m/%d   %H:%M:%S'))
        self.clockText.SetFont(DATE_FONT)
        self.clockText.SetForegroundColour('Black')

        topBox.Add(self.tempText, 1, wx.CENTRE)
        topBox.Add(self.rhText, 1, wx.CENTRE)
        topBox.Add(self.clockText, 1, wx.CENTRE)

        #Add stuff to the View data page
        createGraphLabel.SetFont(UTILITY_FONT)
        fxMainBox.Add(createGraphLabel, 1, wx.CENTRE)
        fxRowOne.Add(self.tempCheckBox, 1, wx.CENTRE)
        fxRowOne.Add(self.rhCheckBox, 1, wx.CENTRE)

        #Add stuff to the utility page
        self.deviceColLabel.SetFont(UTILITY_FONT)
        self.piColLabel.SetFont(UTILITY_FONT)
        piCol.Add(self.piColLabel, 1, wx.CENTRE)
        piCol.Add(self.ejectDriveButton,1, wx.CENTRE)
        piCol.Add(self.shutDownButton, 1, wx.CENTRE)
        piCol.Add(self.restartButton, 1, wx.CENTRE)
        piCol.Add(self.fullScreenButton, 1, wx.CENTRE)
        deviceCol.Add(self.deviceColLabel, 1, wx.CENTRE)
        deviceCol.Add(self.replaceSensorButton, 1, wx.CENTRE)
        deviceCol.Add(self.getStoredDataButton, 1, wx.CENTRE)
        utilitySizer.Add(piCol,1)
        utilitySizer.Add(deviceCol,1)

        #More stuff for the View Data page
        fxStartRow.Add(self.startDateLabel, .65, wx.LEFT)
        fxStartRow.Add(self.startDatePicker, 2, wx.CENTRE|wx.EXPAND)
        fxEndRow.Add(self.endDateLabel, .65, wx.LEFT)
        fxEndRow.Add(self.endDatePicker, 2, wx.CENTRE | wx.EXPAND)
        fxColRight.Add(fxStartRow, 1, wx.CENTRE | wx.EXPAND)
        fxColRight.Add(fxEndRow, 1, wx.CENTRE | wx.EXPAND)
        fxColRight.Add(self.graphRange, 1, wx.CENTRE | wx.EXPAND)
        fxColLeft.Add(self.graph12, 1, wx.CENTRE)
        fxColLeft.Add(self.graph24, 1, wx.CENTRE)
        fxColLeft.Add(self.graph168, 1, wx.CENTRE)

        fxBottom.Add(fxColLeft, 2, wx.CENTRE)
        fxBottom.Add(fxColRight, 2, wx.CENTRE)
        fxMainBox.Add(fxRowOne, 1, wx.CENTRE)
        fxMainBox.Add(fxBottom, 4, wx.CENTRE)

        self.utilityPage.SetSizer(utilitySizer)

        self.fxPage.SetSizer(fxMainBox)

        self.mainPanel.SetSizer(topBox)

        #Items for the menu bar
        exitItem = fileButton.Append(wx.ID_EXIT, 'Quit\tctrl+Q', 'Status Message')
        maximizeItem = viewButton.Append(wx.ID_ANY, 'Maximize\tF11' , 'Status Message')
        fullScreenItem = viewButton.Append(wx.ID_ANY, 'Full Screen\tF12', 'Status Message')

        # Add Data to 8 hour Block
        self.timeSpanString = ''
        self.tempMaxString = ''
        self.tempMinString = ''

        self.timeSpanText = wx.StaticText(self.statsPage, 1, self.timeSpanString)
        self.tempMaxText = wx.StaticText(self.statsPage, 2, self.tempMaxString)
        self.tempMinText = wx.StaticText(self.statsPage, 3, self.tempMinString)
        self.timeSpanText.SetFont(DELTA_FONT)
        self.tempMaxText.SetFont(DELTA_FONT)
        self.tempMinText.SetFont(DELTA_FONT)

        lowerBox.Add(self.timeSpanText)
        lowerBox.Add(self.tempMaxText,0, wx.ALIGN_RIGHT)
        lowerBox.Add(self.tempMinText, 0, wx.ALIGN_RIGHT )

        self.statsPage.SetSizer(lowerBox)

        #Quittin Time Countdown
        self.quitLabel = wx.StaticText(self.quitPage, -1, 'Go home in:')
        self.quitTimeLabel = wx.StaticText(self.quitPage, -1, self.calculateQuittinTime())
        self.quitLabel.SetFont(TIME_FONT)
        self.quitTimeLabel.SetFont(TIME_FONT)
        quitTimeBox.Add(self.quitLabel, 0, wx.CENTRE)
        quitTimeBox.Add(self.quitTimeLabel,0, wx.CENTRE)
        self.quitPage.SetSizer(quitTimeBox)

        #Finalize the live graph
        self.graphBox.Add(self.graphCanvas, 1, wx.RIGHT| wx.TOP | wx.GROW)
        self.graphPage.SetSizer(self.graphBox)
        self.CreateLiveGraph()

        #Add Items to the menu bar
        menuBar.Append(fileButton, 'File')
        menuBar.Append(viewButton, 'View')
        self.SetMenuBar(menuBar)
        self._mgr.AddPane(self.secondPanel,wx.aui.AuiPaneInfo().Bottom().BestSize(wx.Size(self.displayWidth, self.displayHeight*.45))
                          .CloseButton(False).CaptionVisible(False))
        self.secondPanel.SetBackgroundColour('limeGreen')
        self._mgr.AddPane(self.mainPanel,wx.aui.AuiPaneInfo().Center().BestSize(wx.Size(self.displayWidth, self.displayHeight))
                          .CloseButton(False).CaptionVisible(False))

        #Status bar is the one on the bottom of the page
        self.CreateStatusBar()
        self.UpdateStatusText()
        self.storeRecord()
        self.setBackgroundColor()

        #put the built pages in the notebook
        self.nb.AddPage(self.quitPage, ' ', wx.EXPAND)
        self.nb.AddPage(self.utilityPage, 'Utility', wx.EXPAND)
        self.nb.AddPage(self.fxPage, 'View Data', wx.EXPAND)
        self.nb.AddPage(self.graphPage, 'Live Graph', wx.EXPAND)
        self.nb.AddPage(self.statsPage, '8 Hour Min/Max', wx.EXPAND)

        self._mgr.Update()

        #Start Timers
        self.clockTimer.Start(1000)
        self.readingTimer.Start(DISPLAY_UPDATE_TIME)
        self.storageTimer.Start(DATA_RECORD_TIME)

        #Event Bindings
        self.Bind(wx.EVT_MENU, self.OnClose, exitItem)
        self.Bind(wx.EVT_MENU, self.OnMaximize, maximizeItem)
        self.Bind(wx.EVT_MENU, self.OnFullScreen, fullScreenItem)
        self.Bind(wx.EVT_TIMER, self.OnClockTimer, self.clockTimer)
        self.Bind(wx.EVT_TIMER, self.OnReadingTimer, self.readingTimer)
        self.Bind(wx.EVT_TIMER, self.OnStorageTimer, self.storageTimer)
        self.Bind(wx.EVT_TIMER, self.OnDisableScreenSaverTimer, self.disableScreenSaverTimer)
        self.Bind(wx.EVT_TIMER, self.OnEnableScreenSaverTimer, self.enableScreenSaverTimer)
        self.Bind(wx.EVT_BUTTON, self.OnGraph12, self.graph12)
        self.Bind(wx.EVT_BUTTON, self.OnGraph24, self.graph24)
        self.Bind(wx.EVT_BUTTON, self.OnGraph168, self.graph168)
        self.Bind(wx.EVT_BUTTON, self.OnGraphRange, self.graphRange)
        self.Bind(wx.EVT_BUTTON, self.Restart, self.restartButton)
        self.Bind(wx.EVT_BUTTON, self.ShutDown, self.shutDownButton)
        self.Bind(wx.EVT_BUTTON, self.EjectDrive, self.ejectDriveButton)
        self.Bind(wx.EVT_BUTTON, self.OnReplaceSensor, self.replaceSensorButton)
        self.Bind(wx.EVT_BUTTON, self.OnGetStoredData, self.getStoredDataButton)
        self.Bind(wx.EVT_BUTTON, self.OnMaximize, self.fullScreenButton)

    def adjustTime(self):
        if USE_NETWORK_TIME:
            returnValue = logger.setTime(LOGGER_PASSWORD)
            try:
                assert returnValue == 0
            except AssertionError:
                print '1620 Time Set Error'
                ###Throw error###################################work to be done here!!!#############################################################################
        else:
            setTime.SetTime()

    def calculateQuittinTime(self):
        now = datetime.datetime.now()
        today = now.date()
        quitTimeStr = now.strftime('%Y/%m/%d') + ' ' + QUITTIN_TIME
        quittinTime = datetime.datetime.strptime(quitTimeStr, '%Y/%m/%d %H%M')
        if now.weekday() == SHORT_DAY:
            quittinTime = quittinTime - datetime.timedelta(hours = SHORT_HOURS)

        quitDiff = quittinTime - now
        quitDelta = quitDiff.seconds
        if quitDiff.days < 0:
            outputStr = 'Seriously, go home.'
        else:
            countDownHrs = str(quitDelta/3600)
            countDownMins = str((quitDelta%3600)/60)
            countDownSecs = str((quitDelta%3600)%60)
            countDownStr = countDownHrs + ':' + countDownMins + ':' + countDownSecs
            countDownTime = datetime.datetime.strptime(countDownStr, '%H:%M:%S')
            outputStr = countDownTime.strftime('%H:%M:%S')
            if END_OF_DAY_SIGNAL and (quitDelta == 3):
                alert.quittinTime()
        return outputStr

    def calculateTimerValue(self, dys, hrs, mins):
        now = datetime.datetime.now()
        today = now.date()
        midnight = datetime.datetime.strptime(now.strftime('%Y/%m/%d'),'%Y/%m/%d')
        startTime = midnight + datetime.timedelta(days = dys, hours = hrs, minutes = mins)
        timerValue = (startTime - now).seconds * 1000
        return timerValue

    def CreateLiveGraph(self, *args): #builds the initial live graph
        self.ax1=self.graphFigure.add_subplot(111, axisbg = '#eaeaea')
        self.graphFigure.tight_layout()
        self.graphFigure.subplots_adjust(left=.075)
        self.graphFigure.subplots_adjust(right=.935)
        self.graphFigure.subplots_adjust(bottom=.2)
        self.ax1.yaxis.tick_left()# w/o this the ticks are echoed on the right side
        self.ax2=self.graphFigure.add_subplot(111,sharex=self.ax1,frameon=False)
        self.ax2.set_xlabel(' ')
        self.ax2.yaxis.set_label_position('right')
        self.ax2.yaxis.tick_right()

        self.graphFigure.patch.set_facecolor('#eaeaea')
        self.UpdateLiveGraph()

    def UpdateLiveGraph(self): #updates the data on the existing graph
        self.graphingAvailiable = False
        self.ax1.clear()
        self.ax2.clear()
        self.ax1.set_ylabel('Temp F', color = 'red')
        self.ax2.set_ylabel('RH %', color = 'blue')
        self.ax1.plot(self.dateArray, self.tempArray, color = 'red', lw = 2.5)
        self.ax2.plot(self.dateArray, self.rhArray, color = 'blue', lw = 2.5)
        for tl in self.ax1.get_yticklabels():
            tl.set_color('red')

        for tl in self.ax2.get_yticklabels():
            tl.set_color('blue')
        if self.tMax > TEMP_MAX:
            self.ax1.axhline(TEMP_MAX, color = 'red', ls = '--')
        if self.tMin< TEMP_MIN:
            self.ax1.axhline(TEMP_MIN, color = 'red', ls = '--')
        if self.rhMax > RH_MAX:
            self.ax2.axhline(RH_MAX, color = 'blue', ls = '--')
        if self.rhMin < RH_MIN:
            self.ax2.axhline(RH_MIN, color = 'blue', ls = '--')
        matplotlib.rcParams.update({'font.size': 22})
        plot.grid(color = 'white', ls = '-')
        self.graphCanvas.draw()
        self.graphingAvailiable = True

    def createRhString(self):
        return str("{0:.1f}".format(self.record.RH) + '% RH')

    def createTempString(self):

        tempF = ("{0:.2f}".format(self.record.tempF))
        tempC = ("{0:.2f}".format(self.record.tempC))
        tempString = str(tempF) + u"\u00b0" +'F' +  '    ' + str(tempC) + u"\u00b0" +'C'
        return tempString

    def convertCtoF(self, tempC):
        tempC = float(tempC)
        tempF = (tempC * 1.8)+ 32.0
        tempF = "{0:.2f}".format(tempF)
        tempF = float(tempF)
        return tempF

    def convertFtoC(self, tempF):
        tempF = float(tempF)
        tempC = (tempF - 32.0 )/1.8
        tempC = "{0:.2f}".format(tempC)
        tempC = float(tempC)
        return tempC

    def disbleScreenSaver(self):  #this turns off the system power save settings to keep the screen from going black
        call(['xset', 's', 'reset'])
        call(['xset', '-dpms'])
        call(['xset', 's', 'off'])
        self.enableScreenSaverTimer.Start(self.calculateTimerValue(0, DTY_STOP_HRS, DTY_STOP_MINS), oneShot = True)

    def enableScreenSaver(self):  #turns the screen black at night
        call (["xset", "dpms", "force", "off"])
        self.disableScreenSaverTimer.Start(self.calculateTimerValue(1, DTY_START_HRS, DTY_START_MINS), oneShot = True)

    def EjectDrive(self, event):  #unmounts sda1 usb memory device
        call (["umount", "/dev/sda1"])

    def GetPlotParameters(self):  #pulls the plot parameter from the view data page to build a static graph
        if self.tempCheckBox.GetValue() and self.rhCheckBox.GetValue():
            plotWhat = 'Both'
        elif self.tempCheckBox.GetValue():
            plotWhat = 'Temp'
        elif self.rhCheckBox.GetValue():
            plotWhat = 'Humidity'
        else:
            plotWhat = 'Both'

        return plotWhat

    def OnAbout(self, evt):
        about = wx.AboutDialogInfo()
        about.Name = "EDDMS Interface/Display Module"
        about.Version = "2.1"
        about.Copyright = "(C) 2017 William Pierce"
        about.Description = wordwrap(
            "The Interface/Display is part of the Environmental Data Display and Management System (EDDMS) application suite. \n \n"
            "This application interfaces with the environmental monitor to log and display temperature and humidity data.", 900, wx.ClientDC(self))
        about.Developers = ["William Pierce"]
        about.License = "License Data Goes Here."
        wx.AboutBox(about)

    def OnClockTimer(self, event):  #events that happen every second
        time = datetime.datetime.now()
        timeString = time.strftime('%Y/%m/%d  %H:%M:%S')
        self.clockText.SetLabel(timeString)
        self.quitTimeLabel.SetLabel(self.calculateQuittinTime())
        self.timeDiff =  (time - self.record.dateTime).seconds
        if self.timeDiff > CONTINUTIY_TIME and self.readingTimer.IsRunning():
            if self.missedReadings == 0:
                self.adjustTime()
            else:
                self.tempText.SetLabel('Check 1620 Cable')
                self.rhText.SetLabel(str(self.timeDiff))
                if self.timeDiff > 600:
                    call (["sudo", "reboot"])
                elif self.timeDiff > 900 and len(self.tempArray) > 0:
                    print 'Readings too old', self.record.dateTime, time
                    print 'Emptying lists!'
                    self.dateArray[:] = []
                    self.tempArray[:] = []
                    self.rhArray[:] = []
                    self.statsPage.SetBackgroundColour('Black')
            self.missedReadings +=1
        else:
            self.missedReadings = 0

    def OnClose(self, event):  # events that happen on program shutdown
        # deinitialize the frame manager
        self.clockTimer.Stop()
        self.readingTimer.Stop()
        self.storageTimer.Stop()
        self._mgr.UnInit()
        # delete the frame
        self.Destroy()
        quit()

    def OnEnableScreenSaverTimer(self, event):
        self.enableScreenSaver()

    def OnDisableScreenSaverTimer(self, event):
        self.disbleScreenSaver()
        self.adjustTime()

    def OnFullScreen(self, event):
        self.Show()
        self.ShowFullScreen(True, wx.FULLSCREEN_NOMENUBAR)

    def OnGraph12(self, event):#the create 12 hour graph button was pressed
        staticGrapher.MakeGraph(self.record.location, 12, self.GetPlotParameters(), TEMP_MIN, TEMP_MAX, RH_MIN, RH_MAX)

    def OnGraph24(self, event):#the create 24 hour graph button was pressed
        staticGrapher.MakeGraph(self.record.location, 24, self.GetPlotParameters(), TEMP_MIN, TEMP_MAX, RH_MIN, RH_MAX)

    def OnGraph168(self, event):#the create 7 day graph button was pressed
        staticGrapher.MakeGraph(self.record.location, 168, self.GetPlotParameters(), TEMP_MIN, TEMP_MAX, RH_MIN, RH_MAX)

    def OnGraphRange(self, event):#the create custom graph button was pressed
        startRange = self.startDatePicker.GetValue()
        endRange = self.endDatePicker.GetValue()
        startRange =  map(str,startRange.FormatISODate().split('-'))
        startRange = startRange[0] + startRange[1] + startRange[2]
        startRange = datetime.datetime.strptime(startRange, '%Y%m%d')
        endRange =  map(str,endRange.FormatISODate().split('-'))
        endRange = endRange[0] + endRange[1] + endRange[2]
        endRange = datetime.datetime.strptime(endRange, '%Y%m%d') + datetime.timedelta(hours = 23 , minutes = 59, seconds = 59)
        staticGrapher.MakeGraph(self.record.location, (startRange, endRange), self.GetPlotParameters(), TEMP_MIN, TEMP_MAX, RH_MIN, RH_MAX)

    def OnGetStoredData(self, event):
        self.PauseMeas()
        logger.readRecords()  
        return
    
        startDlg = wx.MessageDialog(self, 'Set up the 1620 data over the serial port: \n [Data] \n [Data Record] \n [Data Print] \n [Serial] \n [Text] \n *Start Date* \n *End Date* \n DO NOT press enter the main display indicates paused.',                                  'Set up Data', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
        noDataDlg = wx.MessageDialog(self, 'No data received.  You may need to adjust your start dates.',
                                     'No Data', wx.OK | wx.ICON_ERROR)
        successDlg = wx.MessageDialog(self, 'Data Store completed successfully.\n Press [ENTER] on the 1620 display to ensure that the data file is closed properly.', 'Operation complete', wx.OK | wx.ICON_INFORMATION)
        confirmDateDlg = wx. MessageDialog(self, 'When the main display indicates " Paused: Reading", press [Enter] twice to start sending data.', 'Ready for Data',  wx.ICON_INFORMATION)
        keepGoing = startDlg.ShowModal() == wx.ID_OK
        startDlg.Destroy()
        if keepGoing:
            confirmDateDlg.ShowModal()
            confirmDateDlg.Destroy()
            time.sleep(2)
            opStart = self.PauseMeas()
            print "Getting Data"
            self.rhText.SetLabel('Reading')
            self.SetStatusText(' Reading 1620 Data')
            retrieved = logger.getLoggerRecords()
            time.sleep(10)
            if len(retrieved)> 0:
                self.rhText.SetLabel('Storing')
                self.SetStatusText('Storing Data')
                sql.storeBatchRecords(retrieved)
                print "Fetch and Store Complete"
            else:
                noDataDlg.ShowModal()
                noDataDlg.Destroy()
            self.ResumeMeas(opStart)
            successDlg.ShowModal()

    def OnMaximize(self, event):
        self.ShowFullScreen(not self.IsFullScreen(), wx.FULLSCREEN_NOMENUBAR)
        self.Show()
        self.Maximize(not self.IsMaximized())

    def OnReadingTimer(self, event):#time to take a reading from the logger
            self.TakeReading()

    def TakeReading(self):#Take a reading from the logger and update the main display
        self.oldRecord = copy.deepcopy(self.record)
        try:
            self.record = logger.getReading(self.record)
            assert type(self.record) == type(self.oldRecord)
        except AssertionError:
            self.record = self.oldRecord
        self.tempText.SetLabel(self.createTempString())
        self.rhText.SetLabel(self.createRhString())
        self.setBackgroundColor()
        if self.record.alarm:
            if not self.oldRecord.alarm:
                alert.ootNotification()
        if len(self.tempArray) == 0:
            self.storeRecord()
        elif self.record.tempF > self.tMax or self.record.tempF < self.tMin:
            self.storeRecord()
        elif self.record.RH > self.rhMax or self.record.RH < self.rhMin:
            self.storeRecord()

        arraySize = len(self.tempArray)
        if arraySize > 0:
            timeSpan = self.dateArray[arraySize -1] - self.dateArray[0]
            spanSecs = timeSpan.seconds
            spanHours = str(spanSecs / 3600)
            spanMins =str((spanSecs % 3600) // 60)
            self.timeSpanString = 'Past '+ spanHours + ' Hours and ' + spanMins + ' Minutes: '
        self.UpdateStatusText()

    def OnReplaceSensor(self, event):#change out a logger sensor
        chdlg = wx.MessageDialog(self, 'Replace the sensor then press OK.', 'Swap Sensor', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
        faildlg = wx.MessageDialog(self, 'The rename operation failed.  Verify the stored password and try again. ',
                                 'Rename Failed', wx.OK | wx.ICON_INFORMATION)
        wngSnsrdlg = wx.MessageDialog(self, 'Put the old sensor back and press OK to resume readings.  Press cancel to close the program',
                                 'Rename Failed', wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
        opStart = self.PauseMeas()
        if chdlg.ShowModal() == wx.ID_OK:
            chdlg.Destroy()
            self.rhText.SetLabel('Working')
            self.SetStatusText('Working')
            location = self.record.location[1:(len(self.record.location) - 1)]
            x = logger.setLocation(LOGGER_PASSWORD, self.record.location)
            print x
            testRecord  = logger.getReading(self.record)
            if self.record.location == testRecord.location:
                self.SetStatusText('Reseting Logger')
                logger.reset()
                self.SetStatusText('Refreshing Memory')
                logger.openRecords()
                self.ResumeMeas(opStart)
            else:
                faildlg.ShowModal()
                self.SetStatusText('Sensor Rename Operation Failed')
                while not (self.record.location == testRecord.location):
                    if wngSnsrdlg.ShowModal() == wx.ID_CANCEL:
                        wngSnsrdlg.Destroy()
                        self.clockTimer.Stop()
                        self._mgr.UnInit()
                        # delete the frame
                        self.Destroy()
                    else:
                        testRecord = logger.getReading(self.record)
                self.ResumeMeas(opStart)

        else:
            self.ResumeMeas(opStart)

    def OnStorageTimer(self, event):  #time to store a record
        if self.missedReadings < 45:
            self.storeRecord()
        if self.record.alarm:
            alert.ootContinues()

    def PauseMeas(self):  #stops automatic communication with the logger
        self.readingTimer.Stop()
        self.storageTimer.Stop()
        self.tempText.SetLabel('Paused:')
        self.rhText.SetLabel('-----')
        return datetime.datetime.now()

    def ResumeMeas(self, stopTime):#resume automatic communication with the logger
        elapsedTime = datetime.datetime.now() - stopTime
        self.TakeReading()
        if elapsedTime.seconds >  (DATA_RECORD_TIME//1000):
            self.storeRecord()
        self.readingTimer.Start(DISPLAY_UPDATE_TIME)
        self.storageTimer.Start(DATA_RECORD_TIME)

    def Restart(self, event):#reset the sytem
        call (["sudo", "reboot"])

    def ShutDown(self, event):#power down the system
        call (["sudo", "poweroff"])

    def setBackgroundColor(self):
        tempDelta = abs(TEMP_NOMINAL - self.record.tempF)
        rhDelta = abs(RH_NOMINAL - self.record.RH)
        if (tempDelta > TEMP_TOLERANCE) or (rhDelta > RH_TOLERANCE):
            self.mainPanel.SetBackgroundColour(ENV_OUT_COLOR)
        elif ((abs(tempDelta - TEMP_TOLERANCE) < TEMPF_BORDERLINE_LEVEL)) or ((abs(rhDelta - RH_TOLERANCE) < RH_BORDERLINE_LEVEL)):
            self.mainPanel.SetBackgroundColour(ENV_BORDERLINE_COLOR)
        else:
            self.mainPanel.SetBackgroundColour(ENV_IN_COLOR)

    def storeInitialReading(self):#stores the initial reading from the device(there is no previous data to be compared)
        storeThis = copy.deepcopy(self.record)
        sql.addRecord(storeThis)
        self.tempArray.append(self.record.tempF)
        self.rhArray.append(self.record.RH)
        self.dateArray.append(self.record.dateTime)

    def storeRecord(self):#store the newest record
        if self.lastStoredRecord == '' or not (self.lastStoredRecord.dateTime == self.record.dateTime):  #record is not identical to the last record stored
            storeThis = copy.deepcopy(self.record)
            thread.start_new_thread(sql.addRecord,(storeThis,))
            self.tempArray.append(self.record.tempF)
            self.rhArray.append(self.record.RH)
            self.dateArray.append(self.record.dateTime)
            self.lastStoredRecord = copy.deepcopy(self.record)
        arraySize = len(self.tempArray)
        if arraySize > 0:
            oldestTime = (datetime.datetime.now() - datetime.timedelta(hours = 8, minutes = 5))
            while self.dateArray[0] < oldestTime:
                del self.tempArray[0]
                del self.rhArray[0]
                del self.dateArray[0]
        arraySize = len(self.tempArray)
        if arraySize > 0:
            self.tMax = max(self.tempArray)
            self.tMin = min(self.tempArray)
            self.rhMax = max(self.rhArray)
            self.rhMin = min(self.rhArray)
            tMaxDelta = abs(self.tMax - TEMP_NOMINAL)
            tMinDelta = abs(TEMP_NOMINAL - self.tMin)
            rhMaxDelta = abs(self.rhMax - RH_NOMINAL)
            rhMinDelta = abs(RH_NOMINAL - self.rhMin)
            timeSpan = self.dateArray[arraySize -1] - self.dateArray[0]
            spanSecs = timeSpan.seconds
            spanHours = str(spanSecs / 3600)
            spanMins =str((spanSecs % 3600) // 60)
            self.timeSpanString = 'Past '+ spanHours + ' Hours and ' + spanMins + ' Minutes: '
            self.tempMaxString = ('Max: ' + str("{0:.1f}".format(self.rhMax)) + '%   ' + str("{0:.2f}".format(self.tMax)) + u"\u00b0" +'F   '
                                  + str("{0:.2f}".format(self.convertFtoC(self.tMax))) + u"\u00b0" +'C  ')
            self.tempMinString =  ('Min:  ' + str("{0:.1f}".format(self.rhMin)) + '%   ' + str("{0:.2f}".format(self.tMin)) + u"\u00b0" +'F   '
                                  + str("{0:.2f}".format(self.convertFtoC(self.tMin))) + u"\u00b0" +'C  ' )

            self.timeSpanText.SetLabel(self.timeSpanString)
            self.tempMaxText.SetLabel(self.tempMaxString)
            self.tempMinText.SetLabel(self.tempMinString)
            if (self.tMax > TEMP_MAX) or (self.rhMax > RH_MAX):
                self.statsPage.SetBackgroundColour(ENV_OUT_COLOR)
            elif (self.tMin < TEMP_MIN) or (self.rhMin < RH_MIN):
                self.statsPage.SetBackgroundColour(ENV_OUT_COLOR)
            else:
                self.statsPage.SetBackgroundColour(ENV_IN_COLOR)
        else:
            self.tMax = 0
            self.tMin = 0
            self.rhMax = 0
            self.rhMin = 0

        self.UpdateLiveGraph()
        self.lastRecordTime = '.              Last record saved at ' + datetime.datetime.now().strftime('%H:%M:%S on %m/%d/%Y')

    def unmountDev(self, event):
        call (["umount", "/dev/sda1"])

    def UpdateStatusText(self):
        self.SetStatusText('Display updated from 1620 in ' + self.record.location + ' at '
                           + self.record.dateTime.strftime('%H:%M:%S on %m/%d/%Y')
                           + self.lastRecordTime)

#--------------------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------------------------#
class StartupSplash(wx.SplashScreen):
    def __init__(self, parent=None):
        image = wx.Image('tempDisplay/media/startUpSplash.png').ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 10000 #miliseconds

        wx.SplashScreen(image,splashStyle, splashDuration, parent)
        #(self, image, splashStyle, splashDuration, parent)
        #self.Bind(wx.EVT_CLOSE, self.OnExit)

        wx.Yield()

    def OnExit(self, evt):
        self.Hide()
        nextFrame = DisplayFrame(None)
        nextFrame.Show()
        nextFrame.ShowFullScreen(True, wx.FULLSCREEN_NOMENUBAR)
        evt.Skip()





app = wx.App()
SplashFrame = StartupSplash()
frame = DisplayFrame(None)
frame.Show()
#SplashFrame.Show(False)
frame.ShowFullScreen(True, wx.FULLSCREEN_NOMENUBAR)
#frame.Maximize(True)

app.MainLoop()

import wx
from datetime import datetime
import numpy 
import matplotlib
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx 
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from networkSqlInterface import getAllRecords as getRecords
from networkSqlInterface import getRecordsByRange as getRange

class ShortToolbar(NavigationToolbar2Wx):
          def __init__(self, plotCanvas):
                NavigationToolbar2Wx.__init__(self, plotCanvas)
                #remove unwanted Buttons
                SUBPLOT_BTN = 6
                self.DeleteToolByPos(SUBPLOT_BTN)
          
      

class GraphFrame(wx.Frame):
    def __init__(self, parent, location, hours, plotWhat, lowTemp, highTemp, lowRH, highRH):
        wx.Frame.__init__(self,parent,title=location.replace('"',''),size=(500,500))       
        menuBar = wx.MenuBar()
        fileButton = wx.Menu()
        viewButton = wx.Menu()
        menuBar.Append(fileButton, 'File')
        exitItem = fileButton.Append(wx.ID_EXIT, 'Quit\tctrl+Q', 'Status Message')
        self.Bind(wx.EVT_MENU, self.onClose, exitItem)
        self.SetMenuBar(menuBar)
        self.panel = MatplotPanel(self, location, hours, plotWhat, lowTemp, highTemp, lowRH, highRH)

    def onClose(self, event):
        self.closeFrame()
        
    def closeFrame(self):
        #self._mgr.UnInit()
        self.Destroy()
        
        

class MatplotPanel(wx.Panel):

    def __init__(self, parent, location, hours, plotWhat, lowTemp, highTemp, lowRH, highRH):     
        wx.Panel.__init__(self, parent,-1,size=(50,50))



        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.figure = Figure()
        
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = ShortToolbar(self.canvas)
        self.ax1 = self.figure.add_subplot(111)
        self.figure.tight_layout()
        self.figure.subplots_adjust(left=.075)
        self.figure.subplots_adjust(right=.935)
        self.figure.subplots_adjust(bottom=.2)
        self.figure.subplots_adjust(top = .93)
        matplotlib.rcParams.update({'font.size': 20})
        
        
        if plotWhat == 'Both':
            self.ax1.yaxis.tick_left()
            self.ax2=self.figure.add_subplot(111,sharex=self.ax1,frameon=False)
            self.ax2.yaxis.tick_right()
            self.ax2.yaxis.set_label_position('right')
            
        self.sizer.Add(self.toolbar, 0, wx.EXPAND)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)

        self.drawGraph(location, hours, plotWhat, lowTemp, highTemp, lowRH, highRH)

    def EndProgram(self):
        self.Destroy()
        
    def OnClose(self, event):
        self.Destroy()


    def drawGraph(self, location, hours, plotWhat, lowTemp, highTemp, lowRH, highRH):
        if type(hours) == int:
            data = getRecords(hours, location)
        elif type(hours) == tuple:
            data = getRange(hours[0], hours[1], location)
        temps = data[0]
        rh = data[1]
        dates = data[2]
        end = len(data[2]) - 1

        if len(data[0]) > 0:
            startTime = dates[0].strftime('%m/%d/%Y %H:%M')
            stopTime = dates[end].strftime('%m/%d/%Y %H:%M')
            titleStr = location.replace('"','') + ' Environmental Data'
            
            if plotWhat == 'Temp' or plotWhat == 'Both':
                self.ax1.set_ylabel('Temp F', color = 'red')
                self.ax1.plot(dates, temps, color = 'red', lw = 2.5)
                for tl in self.ax1.get_yticklabels():
                    tl.set_color('red')
                if max(temps) >highTemp:
                    self.ax1.axhline(highTemp, color = 'red', ls = '--')
                if min(temps) < lowTemp:
                    self.ax1.axhline(lowTemp, color = 'red', ls = '--')

            if plotWhat == 'Both':
                self.ax2.set_ylabel('RH %', color = 'blue')
                self.ax2.plot(dates, rh, color = 'blue', lw = 2.5)
                for tl in self.ax2.get_yticklabels():
                    tl.set_color('blue')
                for tick in self.ax2.get_xticklabels():
                    tick.set_visible(False)
                if max(rh) > highRH:
                    self.ax2.axhline(highRH, color = 'blue', ls = '--')
                if min(rh) < lowRH:
                    self.ax2.axhline(lowRH, color = 'blue', ls = '--')

            if plotWhat == 'Humidity':
                self.ax1.set_ylabel('RH %', color = 'blue')
                self.ax1.plot(dates, rh, color = 'blue', lw = 2.5)
                for tl in self.ax1.get_yticklabels():
                    tl.set_color('blue')
                if max(rh) > highRH:
                    self.ax1.axhline(highRH, color = 'blue', ls = '--')
                if min(rh) < lowRH:
                    self.ax1.axhline(lowRH, color = 'blue', ls = '--')

            for tick in self.ax1.get_xticklabels():
                tick.set_rotation(45)

            self.figure.suptitle(titleStr)

        else:
            messageBox = wx.MessageDialog(self, 'Your parameters returned no records', 'No Data', wx.ICON_WARNING)
            messageBox.ShowModal()
            messageBox.Destroy()
            self.OnClose()
            
        
class MakeGraph():
    def __init__(self, location, hours, plotWhat, lowTemp, highTemp, lowRH, highRH):
        app = wx.App(redirect=False)
        frame = GraphFrame(None, str(location), hours, str(plotWhat), lowTemp, highTemp, lowRH, highRH)
        frame.Show()
        frame.Maximize(True)
        app.MainLoop()

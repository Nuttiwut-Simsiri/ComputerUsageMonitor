import sys 
import psutil
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
from PyQt5.QtGui import QIcon
from PyQt5 import uic
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QAction, 
    QApplication, 
    QMainWindow, 
    QPushButton, 
    QMessageBox, 
    QProgressBar, 
    QStatusBar,
    QLCDNumber,
    QWidget,
)
from time import sleep

from pyqtgraph.functions import Color

class NetworkThread(QThread):
    networkSent = pyqtSignal(int)
    networkRecv = pyqtSignal(int)
    GB_UNIT = 1024*1024*1024

    def __init__(self):
        super().__init__()

    def run(self):
        while 1:
            NetworkData = psutil.net_io_counters()
            self.networkSent.emit(int(NetworkData.packets_sent))
            self.networkRecv.emit(int(NetworkData.packets_recv))
            sleep(0.5)


class DiskThread(QThread):
    diskPercent = pyqtSignal(float)
    diskTotal = pyqtSignal(float)
    diskUsed = pyqtSignal(float)
    GB_UNIT = 1024*1024*1024
    def __init__(self):
        super().__init__()
        

    def run(self):
        while 1:
            diskDetail = psutil.disk_usage('C://')
            self.diskPercent.emit(diskDetail.percent)
            self.diskTotal.emit(diskDetail.total//self.GB_UNIT)
            self.diskUsed.emit(diskDetail.used//self.GB_UNIT)
            sleep(1)

class MemoryThread(QThread):
    memoryPercent = pyqtSignal(float)
    memoryUsed = pyqtSignal(float)
    memoryTotal = pyqtSignal(float)
    GB_UNIT = 1024*1024*1024
    def __init__(self):
        super().__init__()
        

    def run(self):
        while 1:
            memDetail = psutil.virtual_memory()
            self.memoryPercent.emit(memDetail.percent)
            self.memoryUsed.emit(round(memDetail.used/self.GB_UNIT, 1))
            self.memoryTotal.emit(memDetail.total//self.GB_UNIT)
            sleep(1)

class CPUThread(QThread):
    CPUPercent = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.getMean = lambda cpu_percent : sum(cpu_percent)//len(cpu_percent)

    def run(self):
        while 1:
            cpuPercentData = psutil.cpu_percent(interval=0.2, percpu=True)
            nonZeroData = [ d for d in cpuPercentData if d > 0]
            if nonZeroData:
                result = self.getMean(nonZeroData)
                self.CPUPercent.emit(result)
            sleep(0.3)

class Application(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = "My Computer Usage"
        self.top, self.left = 250, 250
        self.width, self.height = 640, 480
        GB_UNIT = 1024*1024*1024
        uic.loadUi('gui.ui', self)

        # List 
        self.memUsedHistory = [] 
        self._cpuPList = []   

        # Graph CSS 
        self.penStyle = pg.mkPen(color=(21, 237, 9), width=2)    

        # Set action for Munu
        self.setExitAction()
        self.setAboutAction()

        # Create Thread for memory data
        self._memP = self.findChild(QProgressBar, 'pBar_PC')
        self._memGpV = self.findChild(QWidget, 'memWidget')
        setMemPercent = lambda v : self._memP.setValue(round(v))
        self.memGWidget = pg.PlotWidget(self._memGpV)
        self.memGWidget.setBackground((237, 237, 237))
        self.memGWidget.resize(621 , 231)
        memTh = MemoryThread()
        memTh.memoryPercent.connect(setMemPercent)
        memTh.memoryUsed.connect(self.setMemGB)
        memTh.start()

        # Create Thread for CPU 
        self._cpuP = self.findChild(QProgressBar, 'pBarCPU')
        self._gpWidget = self.findChild(QWidget, 'graphWidget')
        self.graphWidget = pg.PlotWidget(self._gpWidget)
        self.graphWidget.setBackground((237, 237, 237))
        self.graphWidget.resize(621, 341)
        cpuTh = CPUThread()
        cpuTh.CPUPercent.connect(self.setCPUPercent)
        cpuTh.start()

        # Create Thread for Disk 
        self._diskP = self.findChild(QProgressBar, 'pBar_DPC')
        self._diskU = self.findChild(QProgressBar, 'pBar_DGB')
        setDiskPercent = lambda v : self._diskP.setValue(int(v))
        setDiskUsed = lambda v : self._diskU.setValue(int(v))
        diskTh = DiskThread()
        diskTh.diskPercent.connect(setDiskPercent)
        diskTh.diskUsed.connect(setDiskUsed)
        diskTh.start()

        # Create Thread for net work 
        self._netPktSent = self.findChild(QLCDNumber, 'lcdNumSent')
        self._netPktRecv = self.findChild(QLCDNumber, 'lcdNumRecv')
        setNetPktSent = lambda v : self._netPktSent.display(v)
        setNetPktRecv = lambda v : self._netPktRecv.display(v)
        netTh = NetworkThread()
        netTh.networkSent.connect(setNetPktSent)
        netTh.networkRecv.connect(setNetPktRecv)
        netTh.start()


        self.setInitUI()

    def setCPUPercent(self, v):
        self._cpuP.setValue(round(v))
        self._cpuPList.append(v)

        # filter only lastest 100 data
        if len(self._cpuPList) > 100:
            self._cpuPList.pop(0)
            self.graphWidget.clear()

        self.drawGraph()

    def setMemGB(self, v):
        self.memUsedHistory.append(v)
          # filter only lastest 100 data
        if len(self.memUsedHistory) > 100:
            self.memUsedHistory.pop(0)
            self.memGWidget.clear()

        self.memGWidget.plot(self.memUsedHistory, pen=self.penStyle)

    def drawGraph(self):
        self.graphWidget.plot(self._cpuPList, pen=self.penStyle)

    def setInitUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()

    def setExitAction(self):
        exitQAction = self.findChild(QAction, 'actionExit')
        exitQAction.triggered.connect(self._closeApp)

    def setAboutAction(self):
        aboutAction = self.findChild(QAction, 'actionAbout')
        aboutAction.triggered.connect(self._aboutApp)

    def _aboutApp(self):
        aboutMsg = """Appilcation 0.0.1 beta
Requirements:   
    Python 3.8.2
    PyQt 5.15.0
        """
        helpReply = QMessageBox.information(self, 'Application ', aboutMsg, QMessageBox.Ok)

    def _closeApp(self):
        exitConfirmReply = QMessageBox.question(self, 'Are you sure ?', "Do you want close Application?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if exitConfirmReply == QMessageBox.Yes:
            sys.exit(0)
    

    



if __name__ == "__main__":
    QApp = QApplication(sys.argv)
    app = Application()
    sys.exit(QApp.exec_())
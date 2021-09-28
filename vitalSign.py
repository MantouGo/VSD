import numpy as np
import datetime
import serial
import pyqtgraph as pg
import numpy.matlib
import Jetson.GPIO as GPIO
import time
import struct
import sys

from collections import deque
from pyqtgraph.Qt import QtCore, QtGui
from threading import Thread

from mmWave import vitalsign
from scipy.fftpack import fft
from scipy import signal

from PyQt5.QtGui import QPalette, QFont
from PyQt5.QtWidgets import QLabel, QMainWindow
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        self.setFixedSize(600, 180)
        self.l0 = QLabel(self)
        self.l0.setFixedWidth(300)
        self.l0.setFixedHeight(40)
        self.l0.setAlignment(Qt.AlignCenter)
        self.l0.setText("Breathing(bpm)")
        self.l0.move(0, 0)

        self.l1 = QLabel(self)
        self.l1.setFixedWidth(300)
        self.l1.setFixedHeight(40)
        self.l1.setAlignment(Qt.AlignCenter)
        self.l1.setText("Heart Rate(bpm)")
        self.l1.move(300, 0)

        pe = QPalette()
        pe.setColor(QPalette.WindowText, Qt.red)
        pe.setColor(QPalette.Background, Qt.white)
        self.l0.setAutoFillBackground(True)
        self.l0.setPalette(pe)
        self.l1.setAutoFillBackground(True)
        self.l1.setPalette(pe)

        self.l0.setFont(QFont("Roman times", 22, QFont.Bold))
        self.l1.setFont(QFont("Roman times", 22, QFont.Bold))

        self.lbr = QLabel(self)
        self.lbr.setFixedWidth(300)
        self.lbr.setFixedHeight(60)
        self.lbr.setAlignment(Qt.AlignCenter)
        self.lbr.setFont(QFont("Roman times", 50, QFont.Bold))
        self.lbr.setText("Breathing")
        self.lbr.move(0, 65)

        self.lhr = QLabel(self)
        self.lhr.setFixedWidth(200)
        self.lhr.setFixedHeight(60)
        self.lhr.setAlignment(Qt.AlignCenter)
        self.lhr.setFont(QFont("Roman times", 50, QFont.Bold))
        self.lhr.setText("Heart Rate")

        self.lhr.move(200, 65)

class globalV:
    count = 0
    hr = 0.0
    br = 0.0
    zcAveNum = 20
    zcAveStart = 19  # zcAveNum-1
    def __init__(self, count):
        self.count = count

maxlen = 200
ft0 = np.zeros(maxlen)
ft1 = np.zeros(maxlen)
brw0 = np.zeros(maxlen)
hrw1 = np.zeros(maxlen)
br0 = np.zeros(maxlen)
hr1 = np.zeros(maxlen)
cd6 = np.zeros(maxlen)
rp7 = np.zeros(64)
# -----------------------------------------
win = pg.GraphicsWindow()

pg.setConfigOption('foreground', 'y')
win.setWindowTitle('Vital Sign Demo')
#------------------------------------------
#**********************************************
# fft0: Breathing    fft1: Heart Rate (200points)
#**********************************************
p0 = win.addPlot()
p0.setRange(xRange=[0, 40], yRange=[0, 2])
p0.setLabel('bottom', 'Breathing Rate FFT(ft0)', 'bpm')
p0.setVisible(False) # True/False
br2t = np.linspace(0, 600, 100)
curve_ft0 = p0.plot(ft0)

p1 = win.addPlot()
p1.setRange(xRange=[0, 200], yRange=[0, 2])
p1.setLabel('bottom', 'Heart Rate FFT(ft1)', 'bpm')
p1.setVisible(False) # True/False
hr2t = np.linspace(0, 600, 100)
curve_ft1 = p1.plot(ft1)

## Set up an animated arrow and text that track the curve
# Breathing rate
curvePoint_br_rt = pg.CurvePoint(curve_ft0)
p0.addItem(curvePoint_br_rt)
text_br_rt = pg.TextItem("", anchor=(0.5, 1.7), color = 'b')
text_br_rt.setParentItem(curvePoint_br_rt)
arrow0 = pg.ArrowItem(angle=270)
arrow0.setParentItem(curvePoint_br_rt)
pen = pg.mkPen(color=(0, 0, 255))

# Heart rate
curvePoint_hr_rt = pg.CurvePoint(curve_ft1)
p1.addItem(curvePoint_hr_rt)
text_hr_rt = pg.TextItem("", anchor=(0.5, 1.7), color = 'r')
text_hr_rt.setParentItem(curvePoint_hr_rt)
arrow1 = pg.ArrowItem(angle=270)
arrow1.setParentItem(curvePoint_hr_rt)
pg.mkPen('y')

#===============================================================
# 分隔線
#===============================================================

# ------windowing function---------
tukwd = signal.tukey(200, alpha=0.5)    # M：int輸出窗口中的點數 如果為零或更少 則返回一個空數組 。 alpha：float, 任選參數 窗口的形狀 圖片代表該在餘弦參數範圍內的比例
# ---------------------------------
hrLow = 0.0
hrHigh = 200.0
brLow = 0.0
brHigh = 40.0
# 為甚麼要這樣計算
def jb_br_loc2Val(inp):
    return inp * (brHigh - brLow) / 40 * 600 / 100 + brLow
def jb_hr_loc2Val(inp):
    return inp * (hrHigh - hrLow) / 200 * 600 / 100 + hrLow
def update_fft():
    global ft0, ft1, hr2t, br2t
    curve_ft0.setData(br2t, ft0)
    curve_ft1.setData(hr2t, ft1)

    # Set cursor location(breathing rate)
    br_idx = np.argmax(ft0)
    curvePoint_br_rt.setPos(br_idx / (len(ft0) - 1))
    text_br_rt.setText("{:}".format(jb_br_loc2Val(br_idx)))

    # Set cursor location(heart rate)
    hr_idx = np.argmax(ft1)
    curvePoint_hr_rt.setPos(hr_idx / (len(ft1) - 1))
    text_hr_rt.setText("{:}".format(jb_hr_loc2Val(hr_idx)))


# **************************************
# (windowing) Breathing rate waveform & heart rate waveform after windowing
# **************************************
win.nextRow()
p2 = win.addPlot()
p2.setLabel('bottom', 'Breathing Rate(windowing[brw0])', 'unit:sec')
curve_brw = p2.plot(brw0, pen = pg.mkPen('b'))

p3 = win.addPlot()
p3.setLabel('bottom', 'Heart Rate(windowing[hrw1])', 'unit:sec')
curve_hrw = p3.plot(hrw1, pen = pg.mkPen('y'))
p23t = np.linspace(0, 10, 200)


def update_windowing():
    global p23t, brw0, hrw1
    curve_brw.setData(p23t, brw0)
    curve_hrw.setData(p23t, hrw1)


# **************************************
# (filtering) Breathing rate waveform & heart rate waveform
# **************************************
win.nextRow()
p4 = win.addPlot()
p4.setLabel('bottom', 'Breathing Rate(br0)', 'unit:point')
curve_br = p4.plot(br0, pen = pg.mkPen('b'))

p5 = win.addPlot()
p5.setLabel('bottom', 'Heart Rate(hr1)', 'unit:point')
#curve_hr = p5.plot(hr1)
curve_hr = p5.plot(hr1, pen = pg.mkPen('y'))

# ***************************************
# (original) Chest Displacement: Points= 200 points
# ***************************************
win.nextRow()
p6 = win.addPlot(colspan=1)
p6.setLabel('bottom', 'Chest Displacement(cd6)', 'unit:sec')
p6.setRange(xRange=(0, 10))
p6t = np.linspace(0, 10, 200)  # 用於產生 x1, x2 之間的N點 行線性的矢量
curve_cd = p6.plot(cd6)

def update_indata():
    global p6t, br0, hr1, maxlen, cd6
    curve_cd.setData(p6t,cd6)
    curve_br.setData(br0)
    curve_hr.setData(hr1)

# ------------update all plots--------------------
def update():
    update_indata()
    update_windowing()
    update_fft()
    mainwindow.lbr.setText("{:.2f}".format(gv.br))
    mainwindow.lhr.setText("{:.2f}".format(gv.hr))
# -------------------------------------------------
# need to check again
timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(250) # 80: got(20 Times)   *50ms from uart:

# UART initial# jetson nano ==========================================
try:
    port = serial.Serial("/dev/ttyTHS1", baudrate=921600, timeout=0.5)
except KeyboardInterrupt:
    print("Exiting Program")
except Exception as exception_error:
    print("Error occurred. Exiting Program")
    print("Error" + str(exception_error))
# =====================================================================

# vital sign setup
gv = globalV(0)
vts = vitalsign.VitalSign(port)

fs = 1/0.05     # 50ms 慢時間軸樣本採樣20Hz
nqy = 0.5*fs*60 # 採樣頻率1200 信號本身最大頻率600

b1,a1 = signal.butter(6, [40.0/nqy, 200.0/nqy], 'band') # 0.06-0.3heart rate parameter for fft 過濾器的順序 || 臨界頻率 || 過濾器的類型 Default為'lowpass'
b, a = signal.butter(6, [6.0/nqy, 30.0/nqy], 'band') # 0.01-0.05breath rate parameter for fft 過濾器的順序 || 臨界頻率 || 過濾器的類型 Default為'lowpass'

def vtsExec():
    global ft0, ft1, cd6, b, a, b1, a1, tukwd, br0, brw0, hr1, hrw1
    (dck, vd, rangeBuf) = vts.tlvRead(False)
    vs = vts.getHeader()
    if dck:
        # 處理呼吸 FFT
        gv.br = vd.breathingRateEst_FFT
        gv.br = gv.br if gv.br < 500 else 500  # why br can't over 500

        # 處理 心率 FFT
        gv.hr = vd.heartRateEst_FFT
        gv.hr = gv.hr if gv.hr < 500 else 500

        # 計算幾筆資料
        gv.count = vs.frameNumber
        #
        # # (0)insert chest Displacement
        # #
        # # shift left and insert
        # cd6[:-1] = cd6[1:]
        # cd6[-1] = vd.unwrapPhasePeak_mm
    if True:
        pt = datetime.datetime.now()

        # -----------breathing rate--------------------
        # (3.0)breathing rate bandpass filter
        br0 = signal.filtfilt(b, a, cd6)  # 快速實現信號濾波。 b：濾波器的分子係數向量。 a：濾波器的分母係數向量。如果a[0]不為1，則a和b都通過a[0]。 cd6：要過濾的數據數組。
        # (3.0.1) remove DC level
        br0d = np.diff(br0)  # 沿著指定軸計算第N維的離散差值。 a：輸入矩陣。 n：可選 代表要執行幾次差值。 axis：默認是最後一個
        br0d = np.append(br0d, 0.0)
        # (3.0.2) windowing
        brw0 = br0d * tukwd
        # -----------heart rate ---------
        # (3.1)heart rate bandpass filter
        hr1 = signal.filtfilt(b1, a1, cd6)  # 快速實現信號濾波。 b：濾波器的分子係數向量。 a：濾波器的分母係數向量。如果a[0]不為1，則a和b都通過a[0]。 cd6：要過濾的數據數組。
        # (3.1.1) windowing
        hrw1 = hr1 * tukwd  # 沿著指定軸計算第N維的離散差值。 a：輸入矩陣。 n：可選 代表要執行幾次差值。 axis：默認是最後一個
        # print("vd.conf  br:{:f}   hr:{:f}".format(vd.outputFilterBreathOut ,vd.outputFilterHeartOut ) )

        # ---- fft ---------------
        # you can select better FFT function to get better result
        #
        # (3.0.3)breathing fft
        yf0 = fft(brw0)  # 快速傅立葉轉換 返回brw0中每一列向量的傅立葉轉換。
        ft0 = np.abs(yf0[0:200 // 2])  # 將array各元素取絕對值，然后返回取絕對值的array
        ft0 = ft0 / np.amax(ft0)

        # (3.0.4)heart rate fft
        yf1 = fft(hrw1)  # 快速傅立葉轉換 返回hrw1中每一列向量的傅立葉轉換。
        ft1 = np.abs(yf1[0:200 // 2])
        ft1 = ft1 / np.amax(ft1)

        ct = datetime.datetime.now()
        print("HR:{:.4f} BR:{:.4f} flag:{}".format(gv.hr, gv.br, vd.motionDetectedFlag))


# 執行緒去處理
def uartThread(name):
    pt = datetime.datetime.now()
    ct = datetime.datetime.now()
    port.flushInput()
    while True:
        vtsExec()

thread1 = Thread(target = uartThread, args =("UART",))
thread1.setDaemon(True)
thread1.start()


if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        mainwindow = MainWindow()
        mainwindow.show()
        QtGui.QApplication.instance().exec_()

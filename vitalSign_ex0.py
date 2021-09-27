''' 
Vital Signs : 2019/2/13 15:47
ex0:
Display heart rate & breathing rate data

(1)Download lib:

install:
~#sudo pip intall mmWave
update:
~#sudo pip install mmWave -U


'''
import serial
import struct
import datetime
import csv
import numpy as np
import pandas as pd
from mmWave import vitalsign

# 開啟輸入的csv file
'''
with open('output.csv', 'w', newline='') as csvfile:
	# build csv 寫入器
	vswriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
	# 寫入資料
'''

class globalV:
	count = 0
	hr = 0.0
	br = 0.0
	def __init__(self, count):
		self.count = count
b_list = [] # breath list
h_list = [] # heart list
# UART initial
#jetson nano by chiu-chien-feng
try:
    port = serial.Serial("/dev/ttyTHS1",baudrate = 921600,timeout = 0.5)

except KeyboardInterrupt:
    print("Exiting Program")

except Exception as exception_error:
    print("Error occurred. Exiting Program")
    print("Error"+str(exception_error))
#
#initial global value
#
gv = globalV(0)

vts = vitalsign.VitalSign(port)

 
# UART : 50 ms
def uartGetTLVdata(name):
	print("mmWave: {:} example:".format(name))
	pt = datetime.datetime.now()
	ct = datetime.datetime.now()
	port.flushInput()
	while True:
		#mmWave/VitalSign tlvRead & Vital Sign 
		#print(datetime.datetime.now().time())
		pt = datetime.datetime.now()
		(dck , vd, rangeBuf) = vts.tlvRead(False)
		vs = vts.getHeader()
		#vts.showHeader()

		if dck:
			ct = datetime.datetime.now()
			gv.br = vd.breathingRateEst_FFT
			gv.hr = vd.heartRateEst_FFT
			h_list = gv.br
			b_list = gv.hr
			##vswriter.writerow(['breathingRateEst_FFT','heartRateEst_FFT'])

			dict = {'breathingRateEst_FFT':h_list, 'heartRateEst_FFT':b_list,'FrameNumber':vs.frameNumber}
			df = pd.DataFrame(dict)
			df.to_csv('test.csv')

			print("Heart Rate:{:.4f} Breath Rate:{:.4f} #:{:d}  {}".format(gv.hr,gv.br,vs.frameNumber, ct-pt))
			
			#print("Filter OUT:{0:.4f}".format(vd.outputFilterHeartOut))
			'''
			print("EST FFT:{0:.4f}".format(vd.heartRateEst_FFT))
			print("EST FFT 4Hz:{0:.4f}".format(vd.heartRateEst_FFT_4Hz))
			print("EST FFT xCorr:{0:.4f}".format(vd.heartRateEst_FFT_4Hz))
			print("Confi Heart Out:{0:.4f}".format(vd.confidenceMetricHeartOut))
			print("Confi Heart O 4Hz:{0:.4f}".format(vd.confidenceMetricHeartOut_4Hz))
			print("Confi Heart O xCorr:{0:.4f}".format(vd.confidenceMetricHeartOut_xCorr))
			'''
			print("RangeBuf Length:{:d}".format(len(rangeBuf)))
			print(rangeBuf)


uartGetTLVdata("VitalSign")







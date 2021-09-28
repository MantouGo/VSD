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
#import os
#txtPath = 'Record.txt'


import serial
import struct
import datetime
import csv
import numpy as np
import pandas as pd
from mmWave import vitalsign

b_list = [] # breath list
h_list = [] # heart list
t_list = [] # time list(ms)
class globalV:
	count = 0
	hr = 0.0
	br = 0.0
	def __init__(self, count):
		self.count = count

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

## global df
# UART : 50 ms
def uartGetTLVdata(name):
	print("mmWave: {:} example:".format(name))
	pt = datetime.datetime.now()
	ct = datetime.datetime.now()
	port.flushInput()
	while True:
		# mmWave/VitalSign tlvRead & Vital Sign
		# print(datetime.datetime.now().time())
		pt = datetime.datetime.now()
		(dck , vd, rangeBuf) = vts.tlvRead(False)
		vs = vts.getHeader()

		if dck:
			ct = datetime.datetime.now()
			gv.br = vd.breathingRateEst_FFT
			gv.hr = vd.heartRateEst_FFT
			h_list.append(round(gv.hr, 4))
			b_list.append(round(gv.br, 4))
			t_list.append(ct-pt)
			# 紀錄CSV
			dict = {'Heart Rate:': h_list, 'Breath Rate': b_list, 'Time': t_list}
			df = pd.DataFrame(dict)
			df.to_csv('test.csv')
			#
			print("Heart Rate:{:.4f} Breath Rate:{:.4f} #:{:d}  {}".format(gv.hr,gv.br,vs.frameNumber, ct-pt))
			#print("Filter OUT:{0:.4f}".format(vd.outputFilterHeartOut))
			##print("RangeBuf Length:{:d}".format(len(rangeBuf)))
			#print(rangeBuf)
		vs.frameNumber = 0 # 初始化
uartGetTLVdata("VitalSign")








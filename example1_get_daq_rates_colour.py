#!/usr/bin/env python3
#
# Test script to communicate with the MIDAS DAQ using SOAP protocol
# Gets the status of the DAQ (running or not) and prints rates for certain
# channels
# Joonas Konki - 20180614
#
import requests
import time, datetime
from xml.etree import ElementTree as ET
import base64
from colorama import init, Fore, Back, Style

# Settings
THRESHOLD = 10000 # change font colour when threshold reached
DAQ_URL =  'http://issdaqpc:8015/'
DAQ_WSDL_SERVICE_NAME = 'DataAcquisitionControlServer'
SPECTRUM_WSDL_SERVICE_NAME = 'SpectrumService'
FULL_DAQ_URL = DAQ_URL + DAQ_WSDL_SERVICE_NAME
FULL_SPECTRUM_URL = DAQ_URL + SPECTRUM_WSDL_SERVICE_NAME
HEADER = {'content-type': 'text/xml'}

# Channel mapping to MIDAS HISTOGRAM numbers / CAEN ADC channels
RecoilE_chs = [24,26,33,35]
RecoildE_chs = [25,27,32,34]
Stub_ch_names = ['X1','X2',' E',' G']
Stub1_chs = [5,4,7,6]
Stub2_chs = [9,8,11,10]
Stub3_chs = [14,15,12,13]
Stub4_chs = [18,19,16,17]

# Initialise Colorama
init()

def get_soap_envelope(server,method,params=''):
	body = '<?xml version="1.0" encoding="UTF-8"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" xmlns:xsd="http://www.w3.org/1999/XMLSchema" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body><ns:%s xmlns:ns="urn:%s">%s</ns:%s></SOAP-ENV:Body></SOAP-ENV:Envelope>' % (method,server,params,method)
	return body
	
def print_rates(bytes, name, ch):
	rate_ch = bytes[ (ch)*4 : (ch)*4+4]
	rate_ch_int = int.from_bytes(rate_ch, byteorder='little')
	if rate_ch_int > THRESHOLD:
		print(name + " (ch %3d): " % ch + Fore.RED + str(rate_ch_int) + Style.RESET_ALL)
	else :
		print(name + " (ch %3d): " % ch + Fore.GREEN + str(rate_ch_int) + Style.RESET_ALL)



if __name__ == '__main__':

	#
	# First check if the DAQ is going, because the Rate histogram is not reset to zero !!!!
	#
	soap_env = get_soap_envelope(FULL_DAQ_URL,'GetState','')
	r = requests.post(FULL_DAQ_URL, data=soap_env, headers=HEADER )
	tree = ET.ElementTree(ET.fromstring(r.text))
	root = tree.getroot()

	daq_is_going = False
	for res in root.iter('State'):
		print(Back.BLUE + 'ISS DAQ Rates' + Style.RESET_ALL + '       ' + \
			  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		if 'going' in res.text:
			print('                        ' + Back.GREEN + ' DAQ is GOING! ' + Style.RESET_ALL)
			daq_is_going = True
		
	if not daq_is_going:
		print('                        ' + Back.RED + ' DAQ is STOPPED !? ' + Style.RESET_ALL)
		exit()


	#
	# Get the Rate histogram from SpectrumService WSDL service
	#
	spectrum_name = 'Rate'
	params ='<ns:Name xsi:type="xsd:string">%s</ns:Name><ns:Base xsi:type="xsd:int">0</ns:Base><ns:Range xsi:type="xsd:int">512</ns:Range>' % (spectrum_name)

	soap_env = get_soap_envelope(FULL_SPECTRUM_URL,'SpecRead1D',params)
	r = requests.post(FULL_SPECTRUM_URL, data=soap_env, headers=HEADER )

	tree = ET.ElementTree(ET.fromstring(r.text))
	root = tree.getroot()

	result = ''

	# Decode the result that is given as base64 binary
	for res in root.iter('result'):
		result = base64.b64decode(res.text)

	if result != '' and result != None:
		for i in range(len(RecoilE_chs)):
			print_rates(result, "RecoilE ", RecoilE_chs[i])

		for ch in RecoildE_chs:
			print_rates(result, "RecoildE", ch)

		for i in range(len(Stub1_chs)):
			print_rates(result, "STUBL " + Stub_ch_names[i], Stub1_chs[i])
		for i in range(len(Stub2_chs)):
			print_rates(result, "STUBT " + Stub_ch_names[i], Stub2_chs[i])
		for i in range(len(Stub3_chs)):
			print_rates(result, "STUBB " + Stub_ch_names[i], Stub3_chs[i])
		for i in range(len(Stub4_chs)):
			print_rates(result, "STUBR " + Stub_ch_names[i], Stub4_chs[i])


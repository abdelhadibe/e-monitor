
import minimalmodbus
import threading 
import json  
import paho.mqtt.client as mqtt
import time 
import datetime  
import math
from config import * 

usb_port = '/dev/ttyUSB0' ; 
host = "localhost" ;
port = 1883 ;

energy_meters_topic = "/e-monitor/energy/";
domoticzIn_topic = "domoticz/in"

consumption_meter_id = 3 ; 
production_meter_id = 2; 

def log_time(): 
    dt = datetime.datetime.now() ; 
    log = dt.strftime("%H:%M:%S : ")
    return log ; 


class EnergyMeter(object):
	_mqttc = None ; 
	_tThread = None;
	_consumption_counter = None ; 
	_pv_procduction_counter = None; 
	_voltage_consumption = 0 ; 
	_voltage_production = 0 ; 
	_current_consumption = 0 ; 
	_current_production = 0 ; 
	_active_power_consumption = 0; 
	_active_power_production = 0 ; 
	_total_active_energy_consumption = 0;
	_total_active_energy_production = 0;

 
	def counter_initilisation(self, port, counter_id):
		log = log_time(); 
		counter = minimalmodbus.Instrument(port,counter_id);
		counter.serial.baudrate = 2400
		counter.serial.bytesize = 8
		counter.serial.parity = minimalmodbus.serial.PARITY_NONE
		counter.serial.stopbits = 1
		counter.serial.timeout = 1
		counter.debug = False
		counter.mode = minimalmodbus.MODE_RTU
		print("Waiting for initialisation...\n");
		time.sleep(3);
		print(log+"Counter id = {} initialised \n".format(counter_id));
		return counter ; 

	def publishToDomoticz(self, metering_type, voltage_idx, current_idx, power_idx, energy_idx):

		if(metering_type == "consumption"):
			data_1= json.dumps({ "idx" : voltage_idx, "nvalue" : 0, "svalue" :str(self._voltage_consumption) })
			data_2= json.dumps({ "idx" : current_idx, "nvalue" : 0, "svalue" :str(self._current_consumption )})
			data_3= json.dumps({ "idx" : power_idx, "nvalue" : 0, "svalue" :str(self._active_power_consumption)+str(";5")})
			data_4= json.dumps({ "idx" : energy_idx, "nvalue" : 0, "svalue" :str(self._total_active_energy_consumption*1000)})
		
		elif(metering_type == "production"):
			data_1= json.dumps({ "idx" : voltage_idx, "nvalue" : 0, "svalue" :str(self._voltage_production) })
			data_2= json.dumps({ "idx" : current_idx, "nvalue" : 0, "svalue" :str(self._current_production )})
			data_3= json.dumps({ "idx" : power_idx, "nvalue" : 0, "svalue" :str(self._active_power_consumption)+str(";5")})
			data_4= json.dumps({ "idx" : energy_idx, "nvalue" : 0, "svalue" :str(self._total_active_energy_production*1000)})
			
		self._mqttc.publish(domoticzIn_topic,data_1)
		self._mqttc.publish(domoticzIn_topic,data_2)
		self._mqttc.publish(domoticzIn_topic,data_3)
		self._mqttc.publish(domoticzIn_topic,data_4)


	def publishTo_system(self):

		data = dict();
		consumption = dict();
		production = dict() ; 

		consumption["voltage"] = self._voltage_consumption ; 
		consumption["current"] = self._current_consumption ; 
		consumption["power"] = self._active_power_consumption ; 
		consumption["energy"] = self._total_active_energy_consumption; 
		production["voltage"] = self._voltage_production ; 
		production["current"] = self._current_consumption ; 
		production["power"] = self._active_power_production ; 
		production["energy"] = self._total_active_energy_production ; 
		data["consumption"] = consumption ;
		data["production"] = production ; 

		self._mqttc.publish(energy_meters_topic, json.dumps(data))
		print data ; 






	def __init__(self):
		super(EnergyMeter, self).__init__();

		self._consumption_counter = self.counter_initilisation(usb_port, consumption_meter_id);
		self._pv_procduction_counter = self.counter_initilisation(usb_port, production_meter_id);


		self._mqttc = mqtt.Client();
		self._mqttc.connect(host, port, 60);
		self._mqttc.subscribe(energy_meters_topic);

	def readEnergy_values(self):
		#Values adress from datasheet
		# Consumption Values
		self._voltage_consumption = round(self._consumption_counter.read_float(0, functioncode =4, numberOfRegisters=2), 1);
		self._current_consumption = round(self._consumption_counter.read_float(6, functioncode =4, numberOfRegisters=2), 1);
		self._active_power_consumption = round(self._consumption_counter.read_float(12, functioncode =4, numberOfRegisters=2), 1);
		self._total_active_energy_consumption = round(self._consumption_counter.read_float(342, functioncode =4, numberOfRegisters=2), 4);
		#PV Productionn values
		"""
		self._voltage_production = self._pv_procduction_counter.read_float(0, functioncode =4, numberOfRegisters=2);
		self._consumption_counter = self._pv_procduction_counter.read_float(6, functioncode =4, numberOfRegisters=2);
		self._active_power_production = self._pv_procduction_counter.read_float(12, functioncode =4, numberOfRegisters=2);
		self._total_active_energy_production = self._pv_procduction_counter.read_float(344, functioncode =4, numberOfRegisters=2);
		"""
		
	def runEnergy_meter(self):
		log = log_time();
		print(log+"Energy meter is running\n");
		self._tThread = threading.Thread(target = self.metering_system); 
		self._tThread.daemon = True ; 
		self._tThread.start() ; 
		self._mqttc.loop_start();
	
	def metering_system(self):
		while True :
			self.readEnergy_values();
			self.publishTo_system();
			self.publishToDomoticz("consumption",voltage_consumption_idx,current_consumption_idx,power_consumption_idx,energy_consumption_idx);

			print ("Voltage = {} \n".format(self._voltage_consumption) );
			print ("Current = {} \n".format(self._current_consumption) );
			print ("Power = {} \n".format(self._active_power_consumption )); 
			print ("Energy = {} \n".format(self._total_active_energy_consumption));
			print("------------------------------------------------\n")
			time.sleep(4);

def main():
	totalEnergy_meter = EnergyMeter();
	totalEnergy_meter.runEnergy_meter();

	while True: 
		pass ;

if __name__ == '__main__':
	main();



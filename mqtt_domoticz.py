import time 
import threading
import paho.mqtt.client as mqtt 
import json 
from config import * 

domoticzIn  = "domoticz/in"
domoticzOut = "domoticz/out"

mode_topic  = "/e-monitor/mode/" ; 
plug_topic = "/e-monitor/plug/";
planning_topic = "/e-monitor/planning/";



prise_on  = {"command": "switchlight", "idx": 44, "switchcmd": "On" }
prise_off = {"command": "switchlight", "idx": 44, "switchcmd": "Off" }




jsPrise_1_on  = json.dumps(prise_on)
jsPrise_1_off = json.dumps(prise_off)


class mqtt_domoticz(object):
	_mqttc = None ; 
	_tThread = None;
	_jsframe_planning = None ; 

	def publishToDomotiz(self,topic,data):
		client.publish(topic,data)

	def sendSwitch_cmd(self, idx, cmd):
		try: 
			data = dict();
			data['command'] = "switchlight"; 
			data['idx'] = idx ; 
			if( cmd==1):
				data['switchcmd'] = "On"; 
			elif(cmd==0):
				data['switchcmd'] = "Off"; 
			json_data = json.dumps(data);
			#print json_data ;
		except Exception as ex : 
			print("error to switch cmd "); 
		else :
			self._mqttc.publish(domoticzIn, json_data);
			print(data['switchcmd']+"-cmd sended to switch idx:"+str(idx)); 
	"""
	def OnMsg_mode(self, client, userdata, msg):
		try:
			payload = json.loads(msg.payload.decode('utf-8'))
		except Exception as ex:
			print("exception decoding json payload : "+ str(ex))
		else:
			if (payload['cmd'] == "on"): 
				self._mqttc.publish(domoticzIn,jsPrise_1_on);
			elif (payload['cmd'] == "off"):
				self._mqttc.publish(domoticzIn,jsPrise_1_off);
	"""

	def on_message(self,client, userdata, msg):
		try :
			jsframe = dict() ; 
			print("Message recieved "); 
			print("New message on " + msg.topic + " : " + str(msg.payload) + "\n");
			payload = json.loads(msg.payload.decode('utf-8'));
		except Exception as ex: 
			print ("Error decoding json data"+str(ex));

		else :
			# Mode  
			if(payload['idx']== auto_mode_idx) : 
				
				if(payload['nvalue'] == 1):
					jsframe['mode'] = "auto" ; 
					self._mqttc.publish(mode_topic,json.dumps(jsframe,ensure_ascii=False)); 
					print ("On cmd") ; 
				else :
					jsframe['mode'] = "manual" ; 
					self._mqttc.publish(mode_topic,json.dumps(jsframe,ensure_ascii=False)); 
					print ("Off cmd") ;
			# Waching machin Plannig
			elif(payload['idx'] == waching_machin_idx) : 
				if(payload['nvalue']== 1):
					self._jsframe_planning['waching_machin'] = "True" ; 
				else:
					self._jsframe_planning['waching_machin'] = "False" ; 
				#Send Planning
				self._mqttc.publish(planning_topic,json.dumps(self._jsframe_planning,ensure_ascii=False)); 
			
			elif(payload['idx'] == water_heating_idx) : 
				if(payload['nvalue']== 1):
					self._jsframe_planning['water_heating'] = "True" ; 
				else:
					self._jsframe_planning['water_heating'] = "False" ; 
				#Send Planning
				self._mqttc.publish(planning_topic,json.dumps(self._jsframe_planning,ensure_ascii=False)); 
			
			elif(payload['idx'] == home_heating_idx) : 
				if(payload['nvalue']== 1):
					self._jsframe_planning['home_heating'] = "True" ; 
				else:
					self._jsframe_planning['home_heating'] = "False" ; 
				#Send Planning
				self._mqttc.publish(planning_topic,json.dumps(self._jsframe_planning,ensure_ascii=False)); 
			
			elif(payload['idx'] == pool_heating_idx) : 
				if(payload['nvalue']== 1):
					self._jsframe_planning['pool_heating'] = "True" ; 
				else:
					self._jsframe_planning['pool_heating'] = "False" ; 
				#Send Planning
				self._mqttc.publish(planning_topic,json.dumps(self._jsframe_planning,ensure_ascii=False)); 					 
			
			elif(payload['idx'] == pool_filtration_idx) : 
				if(payload['nvalue']== 1):
					self._jsframe_planning['pool_filtration'] = "True" ; 
				else:
					self._jsframe_planning['pool_filtration'] = "False" ; 
				#Send Planning
				self._mqttc.publish(planning_topic,json.dumps(self._jsframe_planning,ensure_ascii=False)); 			

			elif(payload['idx'] == dryer_idx) : 
				if(payload['nvalue']== 1):
					self._jsframe_planning['dryer'] = "True" ; 
				else:
					self._jsframe_planning['dryer'] = "False" ; 
				#Send Planning
				self._mqttc.publish(planning_topic,json.dumps(self._jsframe_planning,ensure_ascii=False)); 		

			elif(payload['idx'] == dish_washer_idx) : 
				if(payload['nvalue']== 1):
					self._jsframe_planning['dish_washer'] = "True" ; 
				else:
					self._jsframe_planning['dish_washer'] = "False" ; 
				#Send Planning
				self._mqttc.publish(planning_topic,json.dumps(self._jsframe_planning,ensure_ascii=False)); 							





	def __init__(self):
	
		self._mqttc= mqtt.Client() ; 
		self._mqttc.on_message = self.on_message ; 
		#self._mqttc.message_callback_add(plug_topic, self.OnMsg_mode);
		self._mqttc.connect("localhost",1883,60); 
		#self._mqttc.subscribe("/e-monitor/#");
		self._mqttc.subscribe(domoticzOut) ; 
		
		# Plannig initialisation ; 
		self._jsframe_planning = dict() ; 
		self._jsframe_planning['waching_machin'] = "False" ; 
		self._jsframe_planning['water_heating'] = "False" ;
		self._jsframe_planning['pool_heating'] = "False" ; 
		self._jsframe_planning['home_heating'] = "False" ;
		self._jsframe_planning['pool_filtration'] = "False" ;
		self._jsframe_planning['dryer'] = "False" ;
		self._jsframe_planning['dish_washer'] = "False" ;		
		

	def runMqqt_domoritcz(self):
		self._tThread = threading.Thread(target = self.transfering) ; 
		self._tThread.daemon= True ; 
		self._tThread.start() ; 
		self._mqttc.loop_start() ; 

	def transfering(self): 
		print("message Transfering....") ; 
		
		


def main(): 

	mqtt_transfert = mqtt_domoticz() ; 
	mqtt_transfert.runMqqt_domoritcz() ; 

	while True : 
		pass ;
     

if __name__ == '__main__':
    main(); 
 



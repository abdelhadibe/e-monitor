
import json 
import urllib
import paho.mqtt.client as mqtt 
import time 
import threading
#myAPPID = da4129fd505da7e78ad1da77ef375160

#url = 'api.openweathermap.org/data/2.5/forecast?id=524901&APPID=da4129fd505da7e78ad1da77ef375160'
url = 'http://api.openweathermap.org/data/2.5/forecast?q=toulouse,fr&APPID=da4129fd505da7e78ad1da77ef375160&units=metric&lang=fr'
#url = 'api.penweathermap.org/data/2.5/forecast?zip=31400,fr'

Wheath_ext_today = "/e-monitor/ext/today/" # max min actual , dt , 
Wheath_ext_tomor = "/e-monitor/ext/tomor/" 

#create Mqtt client 
tmp_today_idx = 17 ; 
humidity_today_idx = 82; 
clouds_now_idx = 28 ; 
tmp_tomorrow_idx = 20 ; 
humidity_tomorrow_idx = 83; 
clouds_tomorrow_idx = 27 ;


client = mqtt.Client()
client.connect("localhost",1883,60)
domoticz_topic = "domoticz/in"

def humidityStatus(value):
	if value <= 25 :
		return "0"
	elif value > 25 and value <=50 : 
		return "1"
	elif value > 50 and value <= 75:
		return "2"
	else: 
		return "3"

def publishToDomotiz(topic,data):
	client = mqtt.Client()
	client.connect("localhost",1883,60)
	client.publish(topic,data)
	client.disconnect()


def getForcast(url):
	
	while True : 
		# request server 
		try:
			responce = urllib.urlopen(url)
			data = json.loads(responce.read());
		except Exception as ex : 
			print("Error to get forecast data: " +str(ex));
		else:
		#Date recupration
	    #actul weather 
			city = data['city']['name']
			tmp = data['list'][0]['main']['temp'] 
			tmp_max = data['list'][0]['main']['temp_max'] 
			tmp_min = data['list'][0]['main']['temp_min'] 
			humidity = data['list'][0]['main']['humidity'] 
			weather = data['list'][0]['weather'][0]['description']
			clouds = data['list'][0]['clouds']['all']
			date = data['list'][0]['dt_txt']
			dt = data['list'][0]['dt']
			dt= time.ctime(dt)

			## Day +1 forecast	
		 
			tmp_1 = data['list'][1]['main']['temp'] 
			tmp_max_1 = data['list'][1]['main']['temp_max'] 
			tmp_min_1 = data['list'][1]['main']['temp_min'] 
			humidity_1 = data['list'][1]['main']['humidity'] 
			weather_1 = data['list'][1]['weather'][0]['description']
			clouds_1 = data['list'][1]['clouds']['all']
			date_1 = data['list'][1]['dt_txt']
			dt_1 = data['list'][1]['dt']
			dt_1= time.ctime(dt_1)

			#publish Data To Broker 

			todaysForcast = {"today":{"date":dt, "tmp":tmp, "hum":humidity, "tmp_max": tmp_max, "tmp_min":tmp_min,"weather":weather ,"cloud":clouds},
			"tomorr":{"date":dt_1, "tmp":tmp_1, "hum":humidity_1, "tmp_max": tmp_max_1, "tmp_min":tmp_min_1,"weather":weather_1 ,"cloud":clouds_1}}

			jsToday =json.dumps(todaysForcast);
			#jsTomor =json.dumps(tomorrForcast);
			#client.publish(Wheath_ext_today,jsToday);
			#client.publish(Wheath_ext_tomor,jsTomor);


			tmp_today        	= { "idx" : tmp_today_idx, "nvalue" : 0, "svalue" :str(tmp) }
			tmp_tomorrow        = { "idx" : tmp_tomorrow_idx, "nvalue" : 0, "svalue" :str(tmp_1) }
			#tmp_max_today    	= { "idx" : 18, "nvalue" : 0, "svalue" :str(tmp_max)}
			#tmp_min_today    	= { "idx" : 21, "nvalue" : 0, "svalue" :str(tmp_min) }
			#tmp_max_tomorrow    = { "idx" : 14, "nvalue" : 0, "svalue" :str(tmp_max_1) }
			#tmp_min_tomorrow    = { "idx" : 20, "nvalue" : 0, "svalue" :str(tmp_min_1) }
			humidity_today      = { "idx" : humidity_today_idx, "nvalue" : humidity,   "svalue" : humidityStatus(humidity) }
			humidity_tomorrow   = { "idx" : humidity_tomorrow_idx, "nvalue" : humidity_1, "svalue" : humidityStatus(humidity_1) }
			DHT				 	= { "idx" : 16, "nvalue" : 100, "svalue" : "3"}
			tmp_hum_today       = { "idx" : 26, "nvalue" : 0, "svalue" :str(tmp)+";"+str(humidity)+";"+humidityStatus(humidity)}
			#cloudsDz			= { "idx" : 28, "nvalue" : 0, "svalue" :weather + " : " +str(clouds)+"%" }
			clouds_now			= { "idx" : clouds_now_idx, "nvalue" : 0, "svalue" :str(clouds) }
			clouds_tomorrow		= { "idx" : clouds_tomorrow_idx, "nvalue" : 0, "svalue" :str(clouds_1) }


			data_out_0 = json.dumps(tmp_today)
			data_out_1 = json.dumps(tmp_tomorrow)
			data_out_2 = json.dumps(humidity_today)
			data_out_3 = json.dumps(humidity_tomorrow)
			data_out_4 = json.dumps(clouds_now)
			data_out_5 = json.dumps(clouds_tomorrow)



			publishToDomotiz(domoticz_topic,data_out_0)
			publishToDomotiz(domoticz_topic,data_out_1)
			publishToDomotiz(domoticz_topic,data_out_2)
			publishToDomotiz(domoticz_topic,data_out_3)
			publishToDomotiz(domoticz_topic,data_out_4)
			publishToDomotiz(domoticz_topic,data_out_5)
			



			print ("Ville :"+city)
			print("Tmp actuele : {} degre".format(tmp))
			print("Tmp Max : {} degre".format(tmp_max))
			print("Tmp Min : {} degre".format(tmp_min))
			print("humidite: {} %".format(humidity))
			print("Heure de previstion : {} ".format(date))
			print("Type de journee : "+weather)
			print("Clouds : {} %".format(clouds))
			print("Heure fin de previstion : {} ".format(dt))

			print "\n ----- day +1 ------- \n"

			 
			print("Tmp : {} degre".format(tmp_1))
			print("Tmp Max : {} degre".format(tmp_max_1))
			print("Tmp Min : {} degre".format(tmp_min_1))
			print("humidite: {} %".format(humidity_1))
			print("Heure de previstion : {} ".format(date_1))
			print("Type de journee : "+weather_1)
			print("Clouds : {} %".format(clouds_1))
			print("Heure fin de previstion : {} \n".format(dt_1))
			time.sleep(600) ; 


def startForcast(url): 
	th= threading.Thread(target=getForcast(url))
	th.daemon=True;
	th.start() ; 
	client.loop_start() ;

def main():
	
	startForcast(url);
	while True:
		pass;
if __name__ == '__main__':
	main()
	exit(0);



"""

"""

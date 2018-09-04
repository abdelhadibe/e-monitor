import threading
import json
import time
import signal
import random ;
import sys
import datetime
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
from config import *


host = "localhost"
port =  1883

domoticzIn_topic = "domoticz/in";
weather_topic = "/e-monitor/ext/today/" ;
forecast_scenari_topic = "/e-monitor/scenario/forecast/" ;
autoConsommation_scenari_topic = "/e-monitor/scenario/autoconsommation/";
planning_topic = "/e-monitor/planning/";
mode_topic  = "/e-monitor/mode/" ;
energy_topic = "/e-monitor/energy/";
swimPool_topic= "/e-monitor/swimpool/tmp/"

def write_to_db(value):
    dt = datetime.datetime.utcnow().isoformat();
    json_body = [
        {
            "measurement": "test3",
            "tags": {},
            "time": dt,
            "fields": {
                "power_consumption" : value
            }
        }
    ]
    #print("Saved Data : {}".format(json_body));
    self._influxdb_client.write_points(json_body)


right_margin = "\n--------------------------"

def log_time():
    dt = datetime.datetime.now() ;
    log = dt.strftime("%H:%M:%S : ")
    return log ;


class Monitoring(object):
    """docstring for monitoring"""
    _shutdown = None ;
    _mqttClient = None ;
    _influxdb_client = None ;
    _auto_mode = False ;
    _manu_mode = False ;
    _tThread  = None ;
    _scheduler = None ;
    _current_tmp = 0 ;
    _todayTmp_max = 0;
    _todayTmp_min =0 ;
    _current_hum = 0 ;
    _current_cloud = 0;
    _current_weather = "" ;
    _tomorrowTmp = 50 ;
    _tomorrowTmp_max = 0 ;
    _tomorrowTmp_min = 0 ;
    _tomorrow_hum = 0 ;
    _tomorrow_weather = "" ;
    _tomorrow_cloud = 0 ;
    _swimPool_tmp = 0 ;
    _general_consum = 0 ;
    _photoVol_prodution = 0;
    _stopCond = None  ;
    ## Scenarios
    _autoConsommation_scenari = False ;
    _weatherForcast_scenari = False ;
    _waching_machin = 0 ;
    _dryer = 0 ;
    _home_heating = 0;
    _pool_heating = 0 ;
    _water_heating = 0;
    _pool_filtration = 0;
    _dish_washer = 0;
    ## Planning
    _waching_machine_planning = False;
    _dryer_planning = False ;
    _home_heating_planning = False ;
    _water_heating_plannig = False ;
    _pool_heating_planning = False ;
    _pool_filtration_planning = False ;
    _dish_washer_planning = False;
    _devices_planner = 0;
    _consumed_power = 0 ;
    _remaining_power = 0 ;
    _device_list = 0;
    _timer = 0;



    def write_to_db(self, last_time):
        time_now = datetime.datetime.now() ;
        delta_t = time_now - last_time ;
        if(delta_t.seconds >= 5):
            power_running = self.calculate_consumed_power(self._devices_planner);
            power_running = float(power_running )
            power = random.uniform(400.0, 600.0) + power_running ;
            dt = datetime.datetime.utcnow().isoformat();
            json_body = [
            {
            "measurement": "test6",
            "tags": {},
            "time": dt,
            "fields": {
            "power_consumption" : power
                      }
            }
            ]
            self._influxdb_client.write_points(json_body)
            self._timer = datetime.datetime.now();

    def check_time(self):
        log = log_time() ;
        dt = datetime.datetime.now() ;
        if (dt.hour == 0 and dt.minute == 0 and dt.second == 0 ):
            for k,device in self._devices_planner.items()  :
                device['number_times_pass'] = 0 ;
            print(log+"Number times passed device updated to 0");

    def select_device(self, lst):
        #print "in select device function list" ;
        if (len(lst) != 0) :
            minimum = lst[0];
            for x in lst :
                if x['number_times_pass'] <= minimum['number_times_pass'] :
                    minimum = x;
            return minimum ;

    def update_remaining_time(self, planner):
        for k,d in planner.items():
            #if(d['in_planning'] == "True"):
            if(d['is_running'] == "True"):
                d['stop_time'] = datetime.datetime.now() ;
                d['elapsed_time'] = self.get_elapsed_time(d['start_time'], d['stop_time']) ;




    def device_control(self, planner):
    	log = log_time();
    	device = dict() ;
        for k,d in  planner.items():
            if (d['is_running'] == "True" ):
                device_name = d['name'] ;
                if(d['elapsed_time'] >= d['time_to_run']):
	                d['is_running'] = "False"
	                d['stop_time'] = datetime.datetime.now() ;
	                self.sendSwitch_cmd(switch_device_idx[device_name], "Off") ;
	                self._consumed_power = self.calculate_consumed_power(self._devices_planner);
	                self._remaining_power = self._photoVol_prodution - self._consumed_power ;
	                print(log+"Consumed Power : {} | remaining Power : {} \n".format(self._consumed_power,self._remaining_power));




    def home_device_initialization(self, device_name, in_planning, time_to_run, power_demande):
    	my_device = dict();
    	my_device['name'] = device_name ;
    	my_device['in_planning'] = in_planning;
    	my_device['is_running'] = "False";
    	my_device['stop_time'] = datetime.datetime.now();
    	my_device['elapsed_time'] = "" ;
    	my_device['number_times_pass'] = 0 ;
    	my_device['time_to_run'] = time_to_run ;
    	my_device['priority'] = 0;
    	my_device['power_consumption'] = "" ;
    	my_device['energy_consumption'] = 0;
    	my_device['energy_consumption_threshold'] = 15 ;
    	my_device['power_demande'] = power_demande  ;


    	return my_device ;

    def device_search(self, planner) :
    	d = dict () ;
    	for k,device in planner.items() :
    		if(device['in_planning'] == "True") :
    			if(device['is_running'] == "False") :
	    			if( device['power_demande'] <= self._remaining_power) :
	    				device['start_time'] = datetime.datetime.now() ;
	    				d = device ;
	    				return d;
    		else:
    			d = {}  ;
    			return d ;

    def calculate_consumed_power(self, planner):
    	power = 0 ;
    	log = log_time() ;
    	for k,device in planner.items():
    		if (device['is_running'] == "True"):
    			power = power + device['power_demande'] ;
    	return power ;

    def print_running_devices(self, planner):
    	log = log_time();
    	ch = "" ;
    	for k,device in planner.items():
    		if (device['is_running'] == "True"):
    			ch = ch+device['name']+" ";
    	print(log+"running devices : {}".format(ch)) ;

    """
    def write_log(self, name, power):
    	log_file = "device_log_"+name+".txt" ;
    	my_log = open(log_file,"w");
    	ch = name+","+log_time()+","+str(power);
    	my_log.write(ch);
    """

    def get_elapsed_time(self,start, stop):

    	elapsed = stop - start ;
        elapsed_in_min = (elapsed.seconds)/60.0 ;

    	return elapsed_in_min;

    def OnMsg_devicePlanning(self, client, userdata, msg):
    	try:
    		log = log_time();
    		payload = json.loads(msg.payload.decode('utf-8'));
    	except Exception as ex:
    		print(log+"Error decoding json payload on OnMsg_devicePlanning: "+ str(ex)+right_margin);
    	else:
            self._waching_machine_planning = payload['waching_machin'] ;
            self._home_heating_planning = payload['home_heating'];
            self._water_heating_plannig = payload['water_heating'];
            self._pool_heating_planning = payload['pool_heating'];
            self._pool_filtration_planning = payload['pool_filtration'];
            self._dryer_planning = payload['dryer'];
            self._dish_washer_planning = payload['dish_washer'];


            self._waching_machin['in_planning'] = self._waching_machine_planning;
            self._home_heating['in_planning'] = self._home_heating_planning;
            self._water_heating['in_planning'] = self._water_heating_plannig ;
            self._pool_heating['in_planning'] = self._pool_heating_planning  ;
            self._pool_filtration['in_planning'] = self._pool_filtration_planning;
            self._dryer['in_planning'] = self._dryer_planning ;
            self._dish_washer['in_planning'] =self._dish_washer_planning;


            print "Waching_machin : {} \n".format(self._waching_machin['in_planning'])
            print "Home_heating : {} \n".format(self._home_heating['in_planning'])
            print "Water_heating : {} \n".format(self._water_heating['in_planning'])
            print "Pool_heating : {} \n".format(self._pool_heating['in_planning'])
            print "Pool_filtration : {} \n".format(self._pool_filtration['in_planning'])
            print "dryer : {} \n".format(self._dryer['in_planning'])
            print "dish_washer : {} \n".format(self._dish_washer['in_planning'])

            self._devices_planner['waching_machin'] = self._waching_machin ;
            self._devices_planner['home_heating'] = self._home_heating ;
            self._devices_planner['water_heating'] = self._water_heating ;
            self._devices_planner['pool_heating'] = self._pool_heating ;
            self._devices_planner['dryer'] = self._dryer ;
            self._devices_planner['pool_filtration'] = self._pool_filtration ;
            self._devices_planner['dish_washer'] = self._dish_washer ;

            print("-----------------------\n")


    def OnMsg_autoconsommation(self, client, userdata, msg):
    	try:
    		log = log_time();
    		payload = json.loads(msg.payload.decode('utf-8'));
    	except Exception as ex:
    		print(log+"Error decoding json payload on OnMsg_autoconsommation: "+ str(ex)+right_margin);
    	else:
    		if(payload['autoconsommation'] == "On"):
    			self._autoConsommation_scenari = True;
    			print(log+"OnMsg autoconsommation : autoconsommation scenari enabled \n");
    		elif(payload['autoconsommation'] == "Off"):
    			self._autoConsommation_scenari = False ;
    			print(log+"OnMsg autoconsommation : autoconsommation scenari disabled \n");

    def OnMsg_weatherforecast(self, client, userdata, msg):
    	try:
    		log = log_time();
    		payload = json.loads(msg.payload.decode('utf-8'));
    	except Exception as ex:
    		print(log+"exception decoding json payload on OnMsg_autoconsommation: "+ str(ex)+right_margin);
    	else:
    		if(payload['autoconsommation'] == "On"):
    			self._autoConsommation_scenari = True;
    			print(log+"OnMsg autoconsommation : autoconsommation scenari enabled \n");
    		elif(payload['autoconsommation'] == "Off"):
    			self._autoConsommation_scenari = False ;
    			print(log+"OnMsg autoconsommation : autoconsommation scenari disabled \n");

    def sendSwitch_cmd(self, idx, cmd):
		try:
			log = log_time();
			data = dict();
			data['command'] = "switchlight";
			data['idx'] = idx;
			data['switchcmd'] = cmd;
			json_data = json.dumps(data);
		except Exception as ex :
			print("error to switch cmd ");
		else :
			device_name = "" ;
			for k,v in switch_device_idx.items():
				if v == idx :
					device_name = k ;

			self._mqttClient.publish(domoticzIn_topic, json_data);
			print(log+data['switchcmd']+"-cmd sended to switch: "+device_name+str(idx));


    def OnMsg_mode(self, client, userdata, msg):
        try:
            log = log_time() ;
            payload = json.loads(msg.payload.decode('utf-8'))
        except Exception as ex:
            print(log+"exception decoding json payload : "+ str(ex)+right_margin)
        else:
            if (payload['mode'] == "auto"):
                self._auto_mode = True ;
                self._manu_mode = False ;
                print(log+"On message - mode : Automatic mode activated = " + str(self._auto_mode)+right_margin) ;
            elif (payload['mode'] == "manual"):
                self._manu_mode = True ;
                self._auto_mode = False ;
                print(log+"On message - mode : Manual mode activated = "+ str(self._manu_mode)+right_margin) ;


    def OnMsg_scheduling(self, client, userdata, msg):
    	try :
    		log = log_time() ;
    	except Exception as ex :
    		print(log+"Error loading json payload : "+ str(ex)+right_margin );
    	else:
    		pass ;


    def on_message(self, client, userdata, msg):
        print("New message on " + msg.topic + " : " + str(msg.payload) + "\n");

    def on_connect(self, client,userdata ,flags, rc):
		if rc==0:
			log = log_time();
			print(log+"Connected to broker"+right_margin);

    def on_disconnect(self ,client,userdata , rc):
        log = log_time() ;
        if rc != 0 :
            print(log+"Error : unexpected disconnection from Mqtt broker");
            self._mqttClient.reconnect();
        else :
            print(log+"Disconnection from MQTT broker ");


    def OnMsg_consumption(self, client, userdata, msg):
        try:
            log = log_time()
            payload = json.loads(msg.payload.decode('utf-8')) ;
        except Exception as ex :
            print(log+"error loading json frame in OnMsg_comsumption\n");
        else:
            self._general_consum = payload['consumption'] ;
            self._photoVol_prodution = payload['production'] ;

            print (log+"OnMsg consumption {} \n".format(self._photoVol_prodution));


    def OnMsg_swimPool(self, client, userdata, msg):
        try :
            log = log_time();
            payload =json.loads(msg.payload.decode('utf-8'))

        except Exception as ex :
            print(log+"error loading json frame On swimPool msg");
        else :
            self._swimPool_tmp = payload['tmp'];
            print(log+"On message - swimPool : Temperature = "+str(self._swimPool_tmp)+right_margin) ;




    def onMsg_weather(self, client, userdata, msg):
        log = log_time();
        try:

            payload =json.loads(msg.payload.decode('utf-8'))
        except Exception as ex :
            print(log+"exception decoding json payload : "+ str(ex)+right_margin)
        else:
            print (log+"On Message weather .....")
            self._current_tmp    = payload['today']['tmp'];
            self._todayTmp_max   = payload['today']['tmp_max']
            self._todayTmp_min   = payload['today']['tmp_min']
            self._current_cloud  = payload['today']['cloud'];
            self._current_weather= payload['today']['weather']
            self._tomorrowTmp    = payload['tomorr']['tmp'];
            self._tomorrTmp_max  = payload['tomorr']['tmp_max']
            self._tomorrTmp_min  = payload['tomorr']['tmp_min']
            self._tomorr_hum     = payload['tomorr']['hum'];
            self._tomorr_cloud   = payload['tomorr']['cloud'];
            self._current_weather= payload['tomorr']['weather'];
            #print self._tomorrowTmp ;
            #print (log+"In On Weather function"+right_margin) ;



    def __init__(self):

        super(Monitoring, self).__init__()
        self._shutdown = False ;
        self._manu_mode = False ;
        self._auto_mode = False ;
        self._devices_planner = dict() ;
        self._device_state = dict() ;
        self._consumed_power = 0 ;
        self._remaining_power =  0;
        self._timer = datetime.datetime.now();

        log = log_time();
        # influxDB client
        self._influxdb_client = InfluxDBClient('localhost', 8086, 'root', 'root', 'first_example')
        # Mqtt Client
        self._mqttClient = mqtt.Client()
        self._mqttClient.on_connect = self.on_connect ;
        self._mqttClient.on_disconnect = self.on_disconnect

        self._mqttClient.message_callback_add(weather_topic, self.onMsg_weather);
        self._mqttClient.message_callback_add(mode_topic, self.OnMsg_mode) ;
        self._mqttClient.message_callback_add(swimPool_topic,self.OnMsg_swimPool) ;
        self._mqttClient.message_callback_add(energy_topic, self.OnMsg_consumption);
        self._mqttClient.message_callback_add(autoConsommation_scenari_topic,self.OnMsg_autoconsommation) ;
        self._mqttClient.message_callback_add(planning_topic,self.OnMsg_devicePlanning) ;

        self._mqttClient.connect("localhost", 1883, 60)
        self._mqttClient.subscribe("/e-monitor/#");

        # Home device initialisation
        self._waching_machin  = self.home_device_initialization("waching_machin","False", waching_machin_time_to_run, waching_machin_consump_profile);
        self._home_heating    = self.home_device_initialization("home_heating","False", home_heating_time_to_run, home_heating_consump_profile);
        self._water_heating   = self.home_device_initialization("water_heating","False", water_heating_time_to_run, water_heating_consump_profile);
        self._pool_heating 	  = self.home_device_initialization("pool_heating","False", pool_heating_time_to_run, pool_heating_consump_profile);
        self._dryer 		  = self.home_device_initialization("dryer","False", dryer_time_to_run, dryer_consump_profile);
        self._pool_filtration = self.home_device_initialization("pool_filtration","False", pool_filtration_time_to_run, pool_filtration_consump_profile);
        self._dish_washer     = self.home_device_initialization("dish_washer","False", dish_washer_time_to_run, dish_washer_consump_profile);

        # Planner Initialisation ;
        self._devices_planner['waching_machin'] = self._waching_machin ;
        self._devices_planner['home_heating'] = self._home_heating ;
        self._devices_planner['water_heating'] = self._water_heating;
        self._devices_planner['pool_heating'] = self._pool_heating ;
        self._devices_planner['dryer'] = self._dryer ;
        self._devices_planner['pool_filtration'] = self._pool_filtration ;
        self._devices_planner['dish_washer'] = self._dish_washer ;

        #Domoticz Initilisation
        self.sendSwitch_cmd(auto_mode_idx,"Off");
        self.sendSwitch_cmd(waching_machin_idx,"Off");
        self.sendSwitch_cmd(water_heating_idx,"Off");
        self.sendSwitch_cmd(home_heating_idx,"Off");
        self.sendSwitch_cmd(pool_heating_idx,"Off");
        self.sendSwitch_cmd(pool_filtration_idx,"Off");
        self.sendSwitch_cmd(dryer_idx,"Off");
        self.sendSwitch_cmd(dish_washer_idx,"Off");

        #Device State ;
        self._device_state['waching_machin'] = "Off";
        self._device_state['water_heating'] = "Off";
        self._device_state['home_heating'] = "Off";
        self._device_state['pool_heating'] = "Off";


    def runMonitoring(self):
    	log = log_time() ;
        print(log+"Energy Monitor starting"+right_margin) ;
        self._tThread = threading.Thread(target = self.global_monitoring) ;
        self._tThread.daemon = True ;
        self._tThread.start() ;
        self._mqttClient.loop_start();

    def stopMonitoring(self):
    	self._shutdown = True ;

    def disconnect_Monitoring(self):
    	self._mqttClient.loop_stop();
    	self._mqttClient.disconnect();


    def global_monitoring(self):
        log = log_time();
        print(log+"Monitoring..."+right_margin);
        while not self._shutdown:
            if(self._auto_mode == True ):
                if(self._photoVol_prodution > pv_production_threshold ):
                    self._consumed_power = self.calculate_consumed_power(self._devices_planner)
                    self._remaining_power = self._photoVol_prodution - self._consumed_power ;
                    if(self._remaining_power >= -200 ):
                        time_now = datetime.datetime.now() ;
                        self.device_list = [] ;
                        for k,device in self._devices_planner.items() :
                            if(device['in_planning'] == "True") :
                                if(device['is_running'] == "False") :
                                    if( device['power_demande'] <= self._remaining_power + power_threshold) :
                                        if( self.get_elapsed_time(device['stop_time'], time_now) >= 1.0):
                                            self.device_list.append(device);
                                            #print("In list append \n");
                        #print "in loop",self.device_list ;

                        if ( len(self.device_list) != 0 ):
                            #print "in not list"
                            for x in self.device_list:
                                print x['name']
                            device = self.select_device(self.device_list) ;
                            selected_device_name = device['name'] ;
                            for k,d in self._devices_planner.items() :
                                if (d['name'] == selected_device_name ):
                                    print log_time(),"Selected device is  : ",device['name'] ;
                                    device['start_time'] = datetime.datetime.now() ;
                                    device['is_running'] = "True" ;
                                    device_name = device['name'] ;
                                    device['number_times_pass'] = device['number_times_pass'] + 1 ;
                                    self.sendSwitch_cmd(switch_device_idx[device_name], "On") ;
                                    self._consumed_power = self.calculate_consumed_power(self._devices_planner);
                                    self._remaining_power = self._photoVol_prodution - self._consumed_power ;
                                    log = log_time();
                                    print(log+"Consumed Power : {} | remaining Power : {} \n".format(self._consumed_power,self._remaining_power));
                                    self.print_running_devices(self._devices_planner) ;
                                    print "{} - Number times passed :{} ".format(device_name, device['number_times_pass']) ;

            self.write_to_db(self._timer);
            self.update_remaining_time(self._devices_planner);
            self.device_control(self._devices_planner) ;
            self.check_time();


def cntrl_handler(signum, frame):
	global shutdown ;
	global energy_monitoring ;
	log = log_time() ;

	print(log+"<CTRL+C> cmd detected");
	print(log+"energy monitoring [Shutdown]---------");
	energy_monitoring.stopMonitoring();
	energy_monitoring.disconnect_Monitoring();

	shutdown = True ;

def main():
	global shutdown;
	global energy_monitoring ;

	log = log_time() ;
	print(log+"In main"+right_margin);

	shutdown = False ;
	signal.signal(signal.SIGINT, cntrl_handler);
	energy_monitoring = Monitoring();
	energy_monitoring.runMonitoring();

	while not shutdown:
		pass ;
	sys.exit(0);

if __name__ == '__main__':
    main() ;
    sys.exit(0) ;

import time
import argparse
import random
from influxdb import InfluxDBClient
import datetime
from math import sqrt,exp,pi
import json

import paho.mqtt.client as mqtt
from config import *
consumption_topic = "/e-monitor/energy/";

host = "localhost"
port =  1883

def on_connect(self, client,userdata ,flags, rc):
    if rc==0:
        log = log_time();
        print(log+"Connected to broker"+right_margin);

mqttClient = mqtt.Client()
mqttClient.on_connect = on_connect ;
mqttClient.connect("localhost", 1883, 60)


def publishTo_system(active_power_production):

    data = dict();

    data['consumption']  = active_power_production ;
    data['production']  = active_power_production ;
    data = json.dumps(data)
    mqttClient.publish(consumption_topic, data)
    print data ;



def write_to_db(value1, value2,value3):
    dt = datetime.datetime.utcnow().isoformat();
    json_body = [
        {
            "measurement": "test6",
            "tags": {},
            "time": dt,
            "fields": {
                "value1": value1,
                "value2": value2,
                "power_pv" : value3
            }
        }
    ]
    print("Saved Data : {}".format(json_body));
    client.write_points(json_body)

def calu_w(x):
    sigma = 0.5 ;
    a = 1/(sigma*sqrt(2*pi));
    b = exp(-pow(x,2)/(2*pow(sigma,2)));
    f = a*b ;
    return f ;


client = InfluxDBClient('localhost', 8086, 'root', 'root', 'first_example')
client.create_database('first_example')


#print calu_w(500)

x = 2;
sigma = 0.5
a = 1/(sigma*sqrt(2*pi));

b = exp(-pow(x,2)/(2*pow(sigma,2)));
f = a*b ;

print "a: "+str(a )
print "b: "+str(b)
print "f: "+str(f) ;
print sigma
i= -900 ;
a = -0.004320988 ;
print a

while (i<=900):

    f1= random.randint(1, 80)
    f2= random.randint(1, 80)
    w= a*i*i+3500
    #w = random.uniform(0,w)
    write_to_db(f1, f2, w);
    publishTo_system(w)
    i = i + 1 ;
    time.sleep(1.0)

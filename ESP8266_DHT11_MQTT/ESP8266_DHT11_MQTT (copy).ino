
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "DHT.h"          // Librairie des capteurs DHT
#include <string.h>

#define wifi_ssid "Pi"
#define wifi_password "abdelhadi"

#define mqtt_server "192.168.43.213"
 #define mqtt_user "guest"  //s'il a été configuré sur Mosquitto
 #define mqtt_password "guest" //idem

#define temperature_topic "domoticz/in"  //Topic température
#define humidity_topic "domoticz/in"        //Topic humidité

//Buffer qui permet de décoder les messages MQTT reçus
char message_buff[100];

long lastMsg = 0;   //Horodatage du dernier message publié sur MQTT
long lastRecu = 0;
bool debug = false;  //Affiche sur la console si True

#define DHTPIN D2    // Pin sur lequel est branché le DHT

// Dé-commentez la ligne qui correspond à votre capteur 
//#define DHTTYPE DHT11       // DHT 11 
#define DHTTYPE DHT22         // DHT 22  (AM2302)
char tmp[50] ; 
char hum[50] ; 
//Création des objets
DHT dht(DHTPIN, DHTTYPE);  
WiFiClient espClient;
PubSubClient client(espClient);


void setup() {
  Serial.begin(9600);     //Facultatif pour le debug
     //Pin 2 
  setup_wifi();           //On se connecte au réseau wifi
  client.setServer(mqtt_server, 1883);    //Configuration de la connexion au serveur MQTT
  client.setCallback(callback);  //La fonction de callback qui est executée à chaque réception de message   
  dht.begin();
}

//Connexion au réseau WiFi
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connexion a ");
  Serial.println(wifi_ssid);

  WiFi.begin(wifi_ssid, wifi_password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Connexion WiFi etablie ");
  Serial.print("=> Addresse IP : ");
  Serial.print(WiFi.localIP());
}

//Reconnexion
void reconnect() {
  //Boucle jusqu'à obtenur une reconnexion
  while (!client.connected()) {
    Serial.print("Connexion au serveur MQTT...");
    if (client.connect("ESP8266Client", mqtt_user, mqtt_password)) {
      Serial.println("OK");
    } else {
      Serial.print("KO, erreur : ");
      Serial.print(client.state());
      Serial.println(" On attend 5 secondes avant de recommencer");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  long now = millis();
  //Envoi d'un message par minute
   
    //Lecture de l'humidité ambiante
    float h = dht.readHumidity();
    // Lecture de la température en Celcius
    float t = dht.readTemperature();

    //Inutile d'aller plus loin si le capteur ne renvoi rien
    if ( isnan(t) || isnan(h)) {
      Serial.println("Echec de lecture ! Verifiez votre capteur DHT");
      return;
    }
  
   
    
    StaticJsonBuffer<300> JSONbuffer_t;
    StaticJsonBuffer<300> JSONbuffer_h;
    JsonObject& JSONencoder_t = JSONbuffer_t.createObject();
    JsonObject& JSONencoder_h = JSONbuffer_h.createObject();

    float ft = 51 ;
    //t = (int)t ;
    sprintf(tmp,"%.0f", t);   
    sprintf(hum,"%.0f", h); 
    //dtostrf(ft, 6, 2,tmp);
    
    JSONencoder_t["idx"] = 16;
    JSONencoder_h["idx"] = 17;
    JSONencoder_t["nvalue"] = 0;
    JSONencoder_h["nvalue"] = h;
 
    JSONencoder_t["svalue"] = tmp;
    JSONencoder_h["svalue"] = 2;
    
    
    char JSONmessageBuffer_t[100];
    char JSONmessageBuffer_h[100];
    JSONencoder_t.printTo(JSONmessageBuffer_t, sizeof(JSONmessageBuffer_t));
    JSONencoder_h.printTo(JSONmessageBuffer_h, sizeof(JSONmessageBuffer_h));
    Serial.print(ft);
    Serial.println("Sending message to MQTT topic..");
    Serial.println(JSONmessageBuffer_t);
    Serial.println(JSONmessageBuffer_h);

    
    client.publish(temperature_topic,JSONmessageBuffer_t);   //Publie la température sur le topic temperature_topic
    client.publish(temperature_topic,JSONmessageBuffer_h);
    //client.publish(humidity_topic, String(h).c_str(), true);      //Et l'humidité
 
    delay(2000);
}

// Déclenche les actions à la réception d'un message
// D'après http://m2mio.tumblr.com/post/30048662088/a-simple-example-arduino-mqtt-m2mio
void callback(char* topic, byte* payload, unsigned int length) {

  int i = 0;
  if ( debug ) {
    Serial.println("Message recu =>  topic: " + String(topic));
    Serial.print(" | longueur: " + String(length,DEC));
  }
  // create character buffer with ending null terminator (string)
  for(i=0; i<length; i++) {
    message_buff[i] = payload[i];
  }
  message_buff[i] = '\0';
  
  String msgString = String(message_buff);
  if ( debug ) {
    Serial.println("Payload: " + msgString);
  }
  
  if ( msgString == "ON" ) {
    digitalWrite(D2,HIGH);  
  } else {
    digitalWrite(D2,LOW);  
  }
}

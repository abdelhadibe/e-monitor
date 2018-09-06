
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <string.h>

#define wifi_ssid "pi"
#define wifi_password "abdelhadi"

#define mqtt_server "192.168.43.180"

#define temperature_topic "domoticz/in"  //Topic température


//Buffer qui permet de décoder les messages MQTT reçus
char message_buff[100];

long lastMsg = 0;   //Horodatage du dernier message publié sur MQTT
long lastRecu = 0;
bool debug = false;  //Affiche sur la console si True
int tmp_piscine_idx = 87 ; 

/* Broche du bus 1-Wire */
const byte BROCHE_ONEWIRE = D7;

/* Code de retour de la fonction getTemperature() */
enum DS18B20_RCODES {
  READ_OK,  // Lecture ok
  NO_SENSOR_FOUND,  // Pas de capteur
  INVALID_ADDRESS,  // Adresse reçue invalide
  INVALID_SENSOR  // Capteur invalide (pas un DS18B20)
};


char tmp[50] ; 
 
/* Création de l'objet OneWire pour manipuler le bus 1-Wire */
OneWire ds(BROCHE_ONEWIRE);
WiFiClient espClient;
PubSubClient client(espClient);

/**
 * Fonction de lecture de la température via un capteur DS18B20.
 */
byte getTemperature(float *temperature, byte reset_search) {
  byte data[9], addr[8];
  // data[] : Données lues depuis le scratchpad
  // addr[] : Adresse du module 1-Wire détecté
  
  /* Reset le bus 1-Wire ci nécessaire (requis pour la lecture du premier capteur) */
  if (reset_search) {
    ds.reset_search();
  }
 
  /* Recherche le prochain capteur 1-Wire disponible */
  if (!ds.search(addr)) {
    // Pas de capteur
    return NO_SENSOR_FOUND;
  }
  
  /* Vérifie que l'adresse a été correctement reçue */
  if (OneWire::crc8(addr, 7) != addr[7]) {
    // Adresse invalide
    return INVALID_ADDRESS;
  }
 
  /* Vérifie qu'il s'agit bien d'un DS18B20 */
  if (addr[0] != 0x28) {
    // Mauvais type de capteur
    return INVALID_SENSOR;
  }
 
  /* Reset le bus 1-Wire et sélectionne le capteur */
  ds.reset();
  ds.select(addr);
  
  /* Lance une prise de mesure de température et attend la fin de la mesure */
  ds.write(0x44, 1);
  delay(800);
  
  /* Reset le bus 1-Wire, sélectionne le capteur et envoie une demande de lecture du scratchpad */
  ds.reset();
  ds.select(addr);
  ds.write(0xBE);
 
 /* Lecture du scratchpad */
  for (byte i = 0; i < 9; i++) {
    data[i] = ds.read();
  }
   
  /* Calcul de la température en degré Celsius */
  *temperature = (int16_t) ((data[1] << 8) | data[0]) * 0.0625; 
  
  // Pas d'erreur
  return READ_OK;
}
void setup() {
  Serial.begin(9600);     //Facultatif pour le debug
     //Pin 2 
  setup_wifi();           //On se connecte au réseau wifi
  client.setServer(mqtt_server, 1883);    //Configuration de la connexion au serveur MQTT
 

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
    if (client.connect("ESP8266Client")) {
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
   
   float temperature;
   
  /* Lit la température ambiante à ~1Hz */
  if (getTemperature(&temperature, true) != READ_OK) {
    Serial.println(F("Erreur de lecture du capteur"));
    return;
  }

    /* Affiche la température */
    Serial.print(F("Temperature : "));
    Serial.print(temperature, 2);
    Serial.write(176); // Caractère degré
    Serial.write('C');
    Serial.println();
     
    
    StaticJsonBuffer<300> JSONbuffer_t;
    JsonObject& JSONencoder_t = JSONbuffer_t.createObject();
 
    sprintf(tmp,"%.0f", temperature);   
    //dtostrf(ft, 6, 2,tmp);
 
    JSONencoder_t["idx"] = tmp_piscine_idx;
    JSONencoder_t["nvalue"] = 0;
    JSONencoder_t["svalue"] = tmp;
    
    char JSONmessageBuffer_t[100];
    JSONencoder_t.printTo(JSONmessageBuffer_t, sizeof(JSONmessageBuffer_t));

    Serial.println("Sending message to MQTT topic..");
    Serial.println(JSONmessageBuffer_t);

    client.publish(temperature_topic,JSONmessageBuffer_t);   //Publie la température sur le topic temperature_topic
    delay(2000);
}



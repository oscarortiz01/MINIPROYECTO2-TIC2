// Include the required Wire library for I2C
#include <Wire.h>

void setup() {
  Serial.begin(9600);
  // Start the I2C Bus as Host (Tu código decía address 8, pero el Host no necesita dirección para preguntar)
  Wire.begin(9); 
  Wire.onReceive(receiveEvent);
}

void loop() {
  // 1. Leer de PC 1 y transmitir al device #9 (Tu código adaptado)
  if (Serial.available() > 0) {
    String msg = Serial.readStringUntil('\n');
    msg.trim();
    
    Wire.beginTransmission(8); // transmit to device #8
    Wire.print(msg);           // sends el PING
    Wire.endTransmission();    // stop transmitting
  }
   
}
  // 2. POLLING
void receiveEvent(){ 
  String response = "";
  
  while (Wire.available()) {
    char c = Wire.read(); 
      response += c;
  }

  if (response.length() > 0) {
    Serial.println(response); // Enviar respuesta al PC 1
  }
  
  delay(50);
}

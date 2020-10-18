// Digital read and write with a push button to test things

// digital pin 2 has a pushbutton attached to it. Give it a name:
const int pushButton = 1;

// the setup routine runs once when you press reset:
void setup() {
  Serial.begin(9600); // initialize serial communication at 9600 bits per second, 960 characters per second:
  
  pinMode(pushButton, INPUT); // make the pushbutton's pin an input:
}

void loop() {
  // read the input pin:
  int buttonState = digitalRead(pushButton); //read the input pin
  
  Serial.println(buttonState);// print out the state of the button:
  delay(1);        // delay in between reads for stability
}

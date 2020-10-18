// digital pin 2 has a pushbutton attached to it. Give it a name:
const int pushButton = 1;

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second, 960 characters per second:
  Serial.begin(9600);
  // make the pushbutton's pin an input:
  pinMode(pushButton, INPUT);
}

void loop() {
  // read the input pin:
  int buttonState = digitalRead(pushButton);
  
  // print out the state of the button:
  Serial.println(buttonState);
  delay(2);        // delay in between reads for stability
}

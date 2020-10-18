int inPin = 6;
int inPinval = 0;

int outPin = 2;
int outPinval = 0;

int eventInput = 0;

void setup() {
  // put your setup code here, to run once:

Serial.begin(9600);

pinMode(LED_BUILTIN, OUTPUT);

pinMode(inPin, INPUT);
digitalWrite(inPin, HIGH);

pinMode(outPin, OUTPUT);
digitalWrite(outPin, LOW);

}

void loop() {
  // put your main code here, to run repeatedly:

inPinval = digitalRead(inPin);
digitalWrite(LED_BUILTIN, inPinval);

outPinval = Serial.read();

  // to use switch as task response key
if (inPinval == LOW) Serial.write(45);

  // to trigger ds7a with switch:
//if (inPinval == LOW) {
//digitalWrite(outPin, HIGH);
//delay(50);
//digitalWrite (outPin, LOW);
//delay(200);
//}

  //to trigger ds7a with serial input from task:
if (outPinval > 0) {
digitalWrite(outPin, HIGH);
delay(50); 
digitalWrite (outPin, LOW);
delay(200);
}

}

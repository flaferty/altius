#include <Arduino_BMI270_BMM150.h>
#include <ArduinoBLE.h>

BLEService imuService("12345678-1234-5678-1234-56789abcdef0");  // custom
BLECharacteristic imuChar("abcdef01-1234-5678-1234-56789abcdef0",
                          BLERead | BLENotify, 36);  // 9 floats * 4 bytes, all values are sent as one

void setup() {
  Serial.begin(115200); // initialize USB for debugging
  while (!Serial);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE!");
    while (1);
  }

  BLE.setLocalName("IMU_RightLeg");
  BLE.setAdvertisedService(imuService);

  imuService.addCharacteristic(imuChar);
  BLE.addService(imuService);
  BLE.advertise();

  Serial.println("Arduino is ready");
}

void loop() {
  BLEDevice central = BLE.central(); //device that arduino connects to

  if (central) {
    while (central.connected()) {
      float accX, accY, accZ;
      float gyroX, gyroY, gyroZ;
      float magX, magY, magZ;

      if (IMU.accelerationAvailable()) {
        IMU.readAcceleration(accX, accY, accZ);
      }

      if (IMU.gyroscopeAvailable()) {
        IMU.readGyroscope(gyroX, gyroY, gyroZ);
      }

      if (IMU.magneticFieldAvailable()) {
        IMU.readMagneticField(magX, magY, magZ);
      }

      float values[9] = {
        accX, accY, accZ,
        gyroX, gyroY, gyroZ,
        magX, magY, magZ
      };

      // this automatically sends a notification if subscribed
      imuChar.setValue((uint8_t*)values, sizeof(values)); //casts array to bytes

      delay(10);  // 100 Hz
    }

    Serial.println("Disconnected");
  }
}

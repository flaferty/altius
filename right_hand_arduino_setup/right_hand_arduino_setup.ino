#include <Arduino_BMI270_BMM150.h>
#include <ArduinoBLE.h>

BLEService imuService("12345678-1234-5678-1234-56789abc0000"); //service UUID

//characteristic UUIDs
// Accelerometer
BLEFloatCharacteristic accX("00000001-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);
BLEFloatCharacteristic accY("00000002-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);
BLEFloatCharacteristic accZ("00000003-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);

// Gyroscope
BLEFloatCharacteristic gyroX("00000004-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);
BLEFloatCharacteristic gyroY("00000005-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);
BLEFloatCharacteristic gyroZ("00000006-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);

// Magnetometer
BLEFloatCharacteristic magX("00000007-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);
BLEFloatCharacteristic magY("00000008-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);
BLEFloatCharacteristic magZ("00000009-0000-1000-8000-00805f9b34fb", BLERead | BLENotify);

void setup() {
  Serial.begin(115200);
  delay(1000);

  //keep trying until IMU initializes
  while (!IMU.begin()) {
    Serial.println("IMU not found. Retrying...");
    delay(1000);
  }
  Serial.println("IMU initialized.");

  //keep trying until BLE initializes
  while (!BLE.begin()) {
    Serial.println("BLE init failed. Retrying...");
    delay(1000);
  }
  Serial.println("BLE initialized.");
  Serial.println("Arduino is alive");

  BLE.setLocalName("IMU_RightHand"); //different for each arduino
  BLE.setAdvertisedService(imuService);

  imuService.addCharacteristic(accX);
  imuService.addCharacteristic(accY);
  imuService.addCharacteristic(accZ);
  imuService.addCharacteristic(gyroX);
  imuService.addCharacteristic(gyroY);
  imuService.addCharacteristic(gyroZ);
  imuService.addCharacteristic(magX);
  imuService.addCharacteristic(magY);
  imuService.addCharacteristic(magZ);

  BLE.addService(imuService);
  BLE.advertise();
}

void loop() {
  BLEDevice central = BLE.central(); //device that arduino connects to

  if (central && central.connected()) //if device has connected and is still connected
  {
    while (central.connected()) {
      float ax, ay, az, gx, gy, gz, mx, my, mz;

      if (IMU.accelerationAvailable()) IMU.readAcceleration(ax, ay, az);
      if (IMU.gyroscopeAvailable()) IMU.readGyroscope(gx, gy, gz);
      if (IMU.magneticFieldAvailable()) IMU.readMagneticField(mx, my, mz);

      accX.writeValue(ax);
      accY.writeValue(ay);
      accZ.writeValue(az);

      gyroX.writeValue(gx);
      gyroY.writeValue(gy);
      gyroZ.writeValue(gz);

      magX.writeValue(mx);
      magY.writeValue(my);
      magZ.writeValue(mz);

      delay(100);  // Send data every 100 ms
    }
  }
}


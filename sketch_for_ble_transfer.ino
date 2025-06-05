#include <Arduino_BMI270_BMM150.h>
#include <ArduinoBLE.h>

BLEService imuService("180D");

// Accelerometer
BLEFloatCharacteristic accX("2a57", BLERead | BLENotify);
BLEFloatCharacteristic accY("2a58", BLERead | BLENotify);
BLEFloatCharacteristic accZ("2a59", BLERead | BLENotify);

// Gyroscope
BLEFloatCharacteristic gyroX("2a5a", BLERead | BLENotify);
BLEFloatCharacteristic gyroY("2a5b", BLERead | BLENotify);
BLEFloatCharacteristic gyroZ("2a5c", BLERead | BLENotify);

// Magnetometer
BLEFloatCharacteristic magX("2a5d", BLERead | BLENotify);
BLEFloatCharacteristic magY("2a5e", BLERead | BLENotify);
BLEFloatCharacteristic magZ("2a5f", BLERead | BLENotify);

void setup() {
  Serial.begin(115200);
  delay(1000);

  if (!IMU.begin()) {
    while (1);  // IMU not found
  }

  if (!BLE.begin()) {
    while (1);  // BLE failed
  }

  BLE.setLocalName("NanoBLE-IMU");
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
  BLEDevice central = BLE.central();

  if (central && central.connected()) {
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

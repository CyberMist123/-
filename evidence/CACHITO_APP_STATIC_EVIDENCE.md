# Cachito app static evidence

This file records the relevant facts recovered from the previously uploaded `info-plist.txt` and `objc-metadata.txt`. It is evidence for review, not a complete decompilation.

## Info.plist facts

Observed app metadata:

```text
CFBundleDisplayName = Cachito
CFBundleExecutable = CachitoiOS
CFBundleIdentifier = com.Cachito.CachitoiOS
CFBundleShortVersionString = 1.7.8
MinimumOSVersion = 13.0
ITSAppUsesNonExemptEncryption = false
NSAppTransportSecurity.NSAllowsArbitraryLoads = true
```

Bluetooth and background declarations:

```text
NSBluetoothAlwaysUsageDescription = 开启蓝牙权限，才能连接产品
NSBluetoothPeripheralUsageDescription = "Cachito"想要使用蓝牙权限
UIBackgroundModes = [
  bluetooth-central,
  bluetooth-peripheral,
  fetch,
  processing
]
```

Other notable permissions include microphone access for voice control, camera/photo access, and URL schemes for WeChat and Alipay.

### Interpretation

- `bluetooth-central` supports the ordinary model where the app connects to a BLE accessory.
- `bluetooth-peripheral` supports the possibility that the app also advertises BLE data.
- Both modes being declared is consistent with the current uncertainty: Cachito may use GATT writes, app-originated advertising, or both.
- `NSAllowsArbitraryLoads = true` may make ordinary network observation easier, but does not prove the absence of certificate pinning or application-layer encryption.

## Objective-C metadata facts

Recovered class/property names include:

```text
BleManager
AdvertisHelper
ToyCommondModel
CustomModePlayManager
BTModeData
UserRemoteCommandModel
```

Relevant property and ivar names include:

```text
serviceUUID
linkHelper: AdvertisHelper
helper: AdvertisHelper
paojiHelper: AdvertisHelper
shunxiArray
paojiArray
sxlevels
levels
sxTmodel: ToyCommondModel
pjTmodel: ToyCommondModel
beginShunxiStr
beginPaojiStr
beginBLEStr
shunxiTimer
paojiTimer
BLETimer
stopTopAdvertisingFlag
deviceId
remoteId
codeString
```

Recovered Bluetooth-related symbols/strings from prior inspection include:

```text
CBPeripheralManager
startAdvertisingWithServiceUUID:
ZJQserviceUUID:
writeValue:forCharacteristic:type:
dataOutCharacteristic
peripheral:didUpdateValueForCharacteristic:error:
```

### Interpretation

Strong evidence:

- the app has a central-side BLE manager;
- the app contains advertising helpers and timers;
- suction (`shunxi`) and piston (`paoji`) are represented separately;
- remote IDs/codes exist in the app model;
- characteristic write and update paths exist.

Still unproven:

- whether `710002..` is emitted by the phone or accessory;
- whether the accessory is controlled exclusively by advertisements, exclusively by GATT, or by both in different modes;
- the exact method that constructs the changing UUID/checksum bytes;
- the server endpoint and message schema used by the six-character remote session.

## Minimum discriminating tests suggested by this evidence

1. Scan with the Cachito app force-quit while the accessory remains powered.
2. Scan with the app open while the accessory is powered off/disconnected.
3. Scan with both active.
4. Compare whether `710002..` appears and whether its RSSI follows the phone or accessory.
5. Separately enumerate any connectable accessory GATT services read-only.

Do not send a nonzero command until the advertiser identity and transport are established.

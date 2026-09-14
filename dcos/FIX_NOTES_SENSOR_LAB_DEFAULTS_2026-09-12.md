# Sensor / Powerboard Lab Defaults Fix

This build keeps the requested **zero-camera** behavior while restoring the confirmed physical Lab defaults from the working MVP for Sensors and Powerboard.

- Camera: still has **no default IP/RTSP URL** and will not connect until a Camera is added through Plant Vision.
- Water-quality sensor default: `http://192.168.1.100/readings`
- Ambient sensor default: `http://192.168.1.111:8080/readings`
- Powerboard 1 default: `192.168.1.102`
- Powerboard 2 default: `192.168.1.101`
- All hardware defaults can be overridden through `.env`.

This restores the behavior of the working MVP for physical sensors/powerboards without reintroducing the MVP's automatic camera configuration.

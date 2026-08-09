# LeafyCV1.0 with Current Django Backend

```text
Farm Camera
    |
    v
Shared latest JPEG
    |
    v
LeafyCV1.0
    |
    +-- image validity
    +-- basil tissue segmentation
    +-- fixed integer slot IDs
    +-- canopy / size / colour
    +-- crowding
    +-- growth change
    |
    +-- local CSV/raw/annotated/mask
    |
    v
Django HTTP POST
 metadata + raw_image
    |
    v
computer_vision/views.py
    |
    +--> telemetry.CameraImage
    |
    +--> ImageAnalysis
    |
    +--> PlantVisionMeasurement (one per slot)
```

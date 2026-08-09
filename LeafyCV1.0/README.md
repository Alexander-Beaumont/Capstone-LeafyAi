# LeafyCV1.0

LeafyCV1.0 is the Leafy AI camera and computer-vision component.

It is intentionally separate from the Django backend `computer_vision` app and
from the team's frontend.

## Responsibilities

LeafyCV1.0:
- captures/consumes farm camera images;
- keeps fixed plant-slot identities;
- measures whole-zone and per-slot canopy coverage;
- measures projected canopy width/height;
- measures green/yellow visible tissue;
- measures visual neighbour-contact crowding;
- calculates `growth_change`;
- records measurement validity and processing time;
- saves local raw/annotated/mask/CSV results;
- can POST CV results + a raw JPEG to the Django backend.

It does not own:
- the frontend;
- the database;
- sensor logic;
- the LLM;
- farm actuation.

## Repository-safe contents

These files belong in GitHub:

```text
leafy_cv/
  camera/
  cv/
  scripts/
  tests/
  .env.example
  .gitignore
  API_CONTRACT.md
  BACKEND_TEAM_MESSAGE.md
  CV_ARCHITECTURE.md
  GITHUB_SAFETY_CHECK.md
  README.md
  VERSION
  check_setup.py
  example_cv_payload.json
  requirements.txt
```

## Keep these local/private

Do not commit:
- `.venv/`;
- `.env`;
- real camera usernames/passwords;
- real API tokens;
- `shared_camera/`;
- `outputs/`;
- training videos/datasets;
- model weights unless the team explicitly uses Git LFS.

## Local setup

From inside `leafy_cv`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The `.venv` is local and ignored by Git.

## Local camera configuration

Set values only in your current PowerShell session:

```powershell
$env:FARM_CAMERA_USER='YOUR_REAL_USERNAME'
$env:FARM_CAMERA_PASSWORD='YOUR_REAL_PASSWORD'
$env:FARM_CAMERA_RTSP_PATH=''
$env:FARM_CAMERA1_IP='YOUR_CAMERA_1_IP'
$env:FARM_CAMERA2_IP='YOUR_CAMERA_2_IP'
```

Do not put real values in `.env.example`.

## One-sample CV test

After a latest camera JPEG exists:

```powershell
python .\cv\leafycv_1_0.py level1_camera2 --latest-image .\shared_camera\level1_camera2_latest.jpg --output .\outputs\camera2_test --count 1
```

`--count 1` means analyse one sample and stop.

## Backend API

The measurement payload is aligned to the Django
`ImageAnalysis` and `PlantVisionMeasurement` fields supplied by the team.

The exact HTTP endpoint still comes from the backend route/view. Set it locally:

```powershell
$env:LEAFY_CV_API_URL='http://BACKEND_HOST:PORT/EXACT_ROUTE'
$env:LEAFY_CV_API_SEND_IMAGES='raw'
```

If the backend requires a token:

```powershell
$env:LEAFY_CV_API_KEY='TOKEN_FROM_BACKEND_TEAM'
```

Test one sample before starting the 10-minute schedule.

## PowerShell backticks

A PowerShell backtick at the end of a line only means that the same command
continues on the next line. It is not a secret and it is not uploaded runtime data.

## Camera architecture note

The normal direct-camera workflow should open/capture/release. A continuous
shared RTSP connection should only be used when this process is the
project-owner-approved/trusted shared collector for that physical camera.

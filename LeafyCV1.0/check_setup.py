#!/usr/bin/env python3
import os
import platform
import socket
import sys
from pathlib import Path

print("Leafy AI - setup check")
print("=" * 32)
print("Python:", sys.version.split()[0])
print("Executable:", sys.executable)
print("Platform:", platform.platform())

try:
    import cv2
    print("OpenCV:", cv2.__version__)
    build = cv2.getBuildInformation()
    ffmpeg_lines = [line.strip() for line in build.splitlines() if "FFMPEG:" in line]
    print("FFmpeg:", ffmpeg_lines[0] if ffmpeg_lines else "Could not find FFMPEG line")
except Exception as exc:
    print("OpenCV ERROR:", exc)

try:
    import numpy as np
    print("NumPy:", np.__version__)
except Exception as exc:
    print("NumPy ERROR:", exc)

user = os.getenv("FARM_CAMERA_USER", "")
password = os.getenv("FARM_CAMERA_PASSWORD", "")
path = os.getenv("FARM_CAMERA_RTSP_PATH")
print("Camera username set:", bool(user))
print("Camera password set:", bool(password), f"(length {len(password)})" if password else "")
print("RTSP path:", repr(path) if path is not None else "<not set>")

for name, ip in [
    ("level1_camera1", os.getenv("FARM_CAMERA1_IP", "")),
    ("level1_camera2", os.getenv("FARM_CAMERA2_IP", "")),
]:
    if not ip:
        print(f"{name}: IP not set")
        continue
    try:
        with socket.create_connection((ip, 554), timeout=2):
            print(f"{name} {ip}:554 -> reachable")
    except Exception as exc:
        print(f"{name} {ip}:554 -> NOT reachable ({exc})")

for path in [
    Path("shared_camera/level1_camera1_latest.jpg"),
    Path("shared_camera/level1_camera2_latest.jpg"),
]:
    print(f"{path}:", "exists" if path.exists() else "not created yet")

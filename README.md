# capaoi

The **Capsule Automatic Optical Inspection** project (Nov 2024 – Feb 2025) is designed to detect defects in manufactured capsules within a factory environment. It utilizes a `Basler` camera to ensure high-precision quality control.

## Drivers on Windows

To set up the camera on a Windows machine, download the latest `pylon` software from the [Basler website](https://www.baslerweb.com/en-us/downloads/software/). The `pylon` package includes all necessary drivers for connecting the camera.

## Quick Start

To ensure a clean and isolated environment for running the project, follow these steps to create and activate a virtual environment named `capaoi` and install the required dependencies.

### Prerequisites
- Python (version 3.6+ recommended)
- `pip` (Python package manager)
- `venv` module (comes with standard Python installations)

### Steps to Create and Activate the Virtual Environment

#### 1. Navigate to the Project Directory
Open a terminal or command prompt and navigate to the root directory of your project:
```sh
cd /path/to/capaoi/project
```

#### 2. Create the Virtual Environment
Run the following command to create a virtual environment named `capaoi`:
```sh
python -m venv capaoi
```
This will create a directory named `capaoi` containing the virtual environment.

#### 3. Activate the Virtual Environment
- **On Windows (Command Prompt):**
  ```sh
  capaoi\Scripts\activate
  ```
- **On Windows (PowerShell):**
  ```sh
  capaoi\Scripts\Activate.ps1
  ```
- **On macOS/Linux:**
  ```sh
  source capaoi/bin/activate
  ```

Once activated, you should see `(capaoi)` appear at the beginning of your terminal prompt, indicating that the virtual environment is active.

#### 4. Install Dependencies
With the virtual environment activated, install the required packages from `requirements.txt`:
```sh
pip install -r requirements.txt
```

#### 5. Verify Installation
To check if all dependencies were installed correctly, you can list the installed packages:
```sh
pip list
```

#### 6. Update existing packages
To update install `pip` packages, run the following command inside a `PowerShell` terminal:
```sh
pip list --outdated --format=freeze | ForEach-Object { ($_ -split '==')[0] } | ForEach-Object { pip install --upgrade $_ }
```

#### 6. Deactivating the Virtual Environment
After you're done working, deactivate the virtual environment by running:
```sh
deactivate
```

To get started with the project, run the following commands:

```bash
pip install -r requirements.txt  # Install required dependencies
pip install -e .  # Install the capaoi project as an editable package
pip show capaoi  # View details about the installed project
```

Launch the project directly from the terminal using:

```bash
capaoi  # Windows, Linux
```

## Build Windows Executable

```bash
pyinstaller --onefile --windowed --exclude-module PyQt5 --exclude-module PySide2 --exclude-module PySide6 main.py

pyinstaller --onefile --windowed --exclude-module PyQt5 --exclude-module PySide2 --exclude-module PySide6 --add-data="data/Figs_14/000_mask_raw.png:data/Figs_14" --add-data="images/logo.svg:images" --add-data="backup/AAA/Figs/Fig1.png:backup/AAA/Figs" --add-data="backup/AAA/Figs/Fig2.png:backup/AAA/Figs" main.py
```

## Execute Unit Tests

```bash
cd tests
python -m unittest test_belt.py test_relay_controller.py
```

## Code Snippets

To retreive the name of the camera:

```python
camera.GetDeviceInfo().GetFriendlyName()
```

To retreive the sensor width and height:

```python
# Retreive sensor width and height, and convert µm to mm
sensor_width_mm: float = camera.SensorWidth.GetValue() / 1000.0
sensor_height_mm: float = camera.SensorHeight.GetValue() / 1000.0

logging.debug(
    "Sensor Size: %.2f mm x %.2f mm", sensor_width_mm, sensor_height_mm)
```

Work with an I/O line and monitor the status:

```python
# Select a line
camera.LineSelector.Value = "Line1"
# Get the status of the line
status = camera.LineStatus.Value
logging.debug("Line status: %s", status)
# Get the line status of all I/O lines. Because the GenICam interface does not
# support 32-bit words, the line status is reported as a 64-bit value.
line_state_all = camera.LineStatusAll.Value
logging.debug("Line status all: %s", line_state_all)
```

Verify the resulting (actual) frame-rate of the camera:

```python
camera.BslResultingAcquisitionFrameRate.GetValue()
```

Calculate the relative distance to the right edge of field-of-view

```python
real_world_dist_to_right_edge_mm: list[float] = [
    (INIT_WIDTH - center[0]) * MM_PER_PIXEL
    for center in capsule_centers_abnormal
]
```

Calculate relative actuation delays in milliseconds

```python
rel_actuation_delay_ms: list[int] = [
    int(((dist + BELT_LENGTH_MM) / BELT_SPEED_MM_S) * 1000)
    for dist in real_world_dist_to_right_edge_mm
]
```

Use camera emulation feature with built-in test image:

```python
camera.TestImageSelector.Value = "Testimage1"
```

## Reference

- https://opencv24-python-tutorials.readthedocs.io/en/latest/index.html
- https://www.geeksforgeeks.org/python-opencv-morphological-operations/
- https://github.com/pavel-a/usb-relay-hid
- https://github.com/mcuee/libusb-win32

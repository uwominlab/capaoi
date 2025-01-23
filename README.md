# capaoi

The **Capsule Automatic Optical Inspection** project (Nov 2024 – Feb 2025) is designed to detect defects in manufactured capsules within a factory environment. It utilizes a `Basler` camera to ensure high-precision quality control.

## Drivers on Windows

To set up the camera on a Windows machine, download the latest `pylon` software from the [Basler website](https://www.baslerweb.com/en-us/downloads/software/). The `pylon` package includes all necessary drivers for connecting the camera.

## Quick Start

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

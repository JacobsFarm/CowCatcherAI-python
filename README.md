# 🐄 CowCatcher AI

### This is a fork of the official CowcatcherAI repository

This fork is based on the very first version of the CowcatcherAI code, originally developed by Jacob's Farm. The code is written entirely in Python and serves as a solid foundation for a variety of AI projects.
This project is easier to modify due to its Python-based structure and its standalone interface. It is ideal for developers who prefer a flexible and easily editable version — or for pioneers who appreciate the original CowcatcherAI code over the modern implementations.

#### official cowcatcherai software https://github.com/CowCatcherAI/CowCatcherAI

**CowCatcher AI** is an open-source computer vision system designed to monitor your herd 24/7. By analyzing live footage from your barn cameras, it automatically detects "mounting" behavior—the primary sign of estrus (heat)—and instantly sends a photo notification to your smartphone via Telegram or combine it with your Home assistant setup.

![CowCatcher Overview](https://github.com/user-attachments/assets/cee1e5f5-f9ae-4241-b8ad-8a9313b4a70c)

---

📷 barn camera footage ──→ 🤖 AI Computer Vision ──→ ⚡ *mounting* detection ──→ 💽 save image ──→ 📲 Telegram notification with image

### Key Features
- **24/7 monitoring** of live camera footage
- **Automatic detection** of in heat behavior with AI
- **Direct notifications** via Telegram with photos
- **Local and secure** – your data stays on your farm
- **Open source** - fully customizable and transparent
- **completely free software** one-time setup and lifetime usage
- **affordable and scalable** for 1 calf pen or complete barn

## 🛠️ Requirements

### Bare minimum (for getting started)
- **Standard computer**
- **any IP camera** with RTSP support
- **Internet connection**

### Hardware (for best performance)
- **Computer** with NVIDIA graphics card (€600-1000 for 1-4 cameras)
- **any IP camera** with RTSP support (€80-170)
- **PoE switch** for cameras (€80 for 4 ports)
- **LAN cables** (€1 per meter)
- **Internet connection**
- **Scalable** more cameras require more powerful computer

### Software
- Our Cowcatcher AI software
- Anaconda Prompt
- Sublime Text or Visual Studio Code 
- WinRAR/7-Zip for extracting files

## 📥 Installation

### First of All

You can install this yourself by following the guide below, or contact me for assistance, i can also do the installation for free
- **Email:** jacobsfarmsocial@gmail.com
- **Telegram:** @Jacob5456

For additional guidance, I've created video tutorials for the installation process. While they aren't completely up-to-date, they're quite helpful as the process is largely the same.

**Video Playlist:**  
https://www.youtube.com/playlist?list=PLAa1RFX0i2uCmmDactfR1bR208mwl6KY0

### Step 1: Download Software
1. Download and install [Anaconda](https://www.anaconda.com/products/distribution)
2. Download and install [Sublime Text](https://www.sublimetext.com/) (optional)
3. Download and install [WinRAR](https://www.win-rar.com/) or 7-Zip
4. Download the latest release of [CowCatcherAI](https://github.com/JacobsFarm/CowCatcherAI-python/releases)  
   or with command: `git clone -b https://github.com/JacobsFarm/CowCatcherAI-python.git`

### Step 2: Prepare Project
1. Extract the zip file to a folder of your choice (e.g., `C:\Users\username\Documents\Cowcatcher`)
2. Remember the path to this folder, you'll need to reference it constantly

### Step 3: Set Up Python Environment

Open **Anaconda Prompt** and execute the following commands:

```bash
# Navigate to your project drive (replace C: with your drive)
C:

# Go to your project folder
cd \Users\username\Documents\Cowcatcherai

# Create a new conda environment
conda create -n cowcatcher python=3.11

# Confirm with 'y' when prompted
y

# Activate the environment
conda activate cowcatcherai
```

### Step 4: Install Required Packages

```bash
# Install Ultralytics YOLO
pip install ultralytics
```

### Step 5: (Only for Nvidia graphic Cards) Check GPU Support

```bash
# Install PyTorch with CUDA support for NVIDIA 16-series or newer GPUs, such as the GTX 1660, RTX 2060, RTX 3060...
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

# Install PyTorch with CUDA support for Nvidia GTX 10-series, such as the gtx 1050 / 1060 /1070 ...
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Start Python
python

# Test CUDA availability
import torch
torch.cuda.is_available()

# Should return 'True' for GPU support
# Exit Python
exit()
```

### Step 6: Configure Batch File (Optional)
Create or modify the provided batch file for easy startup. Update the variables according to your setup:

```batch
@echo off
REM Configuration - modify these variables as needed
REM To see version conda in anaconda prompt = echo %CONDA_PREFIX%
set CONDA_PATH="C:\ProgramData\anaconda3\Scripts\activate.bat"
set PROJECT_DRIVE=C:
set PROJECT_FOLDER=CowCatcherAI
set SCRIPT_NAME=main_gui.py

REM Execute the script
call %CONDA_PATH%
%PROJECT_DRIVE%
cd %PROJECT_FOLDER%
python %SCRIPT_NAME%
pause
```

**Customizable Variables:**
- `CONDA_PATH`: Path to your Anaconda installation
- `PROJECT_DRIVE`: Drive letter where your project is located
- `PROJECT_FOLDER`: Name of your project folder
- `SCRIPT_NAME`: Name of the main Python script

## 🤖 Setting Up Telegram Bot

### Step 1: Create Bot
1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Give your bot a name: "e.g.:" `Estrus Detection`
4. Give your bot a username: `EstrusDetectionBot`
5. **Save the API token** you receive, NEVER share this token

### Step 2: Get Your User ID
1. Search for `@userinfobot` in Telegram
2. Start a chat and send `/start`
3. **Note your personal Telegram ID**

## 🚀 Starting the System
Use the configured .bat file, or follow these steps:

```bash
# Navigate to your project folder
C:
cd CowCatcherAI

# Start the detection program
python main_gui.py
```

Upon successful startup, you'll now see an interface

From now fill in the settings and start 

## 📁 Project Structure

```
[Map]CowCatcherAI/
[Map] cowcatcherai/
    app.py
    requirements.txt
    [Map] data/
        [Map] mounting_detections_camera1/
   [Map] gui/
        gui_manager.py
        __init__.py
    [Map] handlers/
        cowcatcher_template.py
        __init__.py
    [Map] logic/
        config_manager.py
        process_manager.py
        __init__.py
    [Map] settings/
        config.json
    [Map] weights/
        cowcatcherV15.pt
```
## Other Repo's from the Cowcatcher AI family
**Main repo
https://github.com/CowCatcherAI/CowCatcherAI

** AI detector (main software base)
https://github.com/ESchouten/ai-detector

**cowcatcher repo for in 100% python code 
https://github.com/JacobsFarm/CowCatcherAI-python

**Annotation Helper
https://github.com/JacobsFarm/annotation_helper_cowcatcherai

## 📄 License

This project uses the GNU Affero General Public License v3.0 (AGPL-3.0). It is based on Ultralytics YOLO and is fully open source.
IMPORTANT NOTICE: This software/model is NOT authorized for commercial use or distribution.

## 🙏 Acknowledgments

This project is made possible by the amazing [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) library. Their state-of-the-art computer vision technology forms the foundation for our AI detection of estrus behavior in cows.

**Thank you Ultralytics team!** 🚀 For making cutting-edge AI technology available that now also helps Dutch farmers.

## 🤝 Contributing

This is an open source project. You may modify and improve it as you see fit. Contributions are welcome via pull requests.

## 📞 Support

For questions or support, please contact via the project repository or community channels, we have a page on facebook https://www.facebook.com/groups/1765616710830233 and Telegram https://t.me/+SphG4deaWVNkYTQ8
For more direct contact: cowcatcherai@gmail.com

---
⚠️ Disclaimer

Use at your own risk.
This software is intended as a tool and does not replace professional knowledge and experience. The AI may give false notifications; the user remains responsible for the final assessment and decision. Physical inspection and identification of the animal remain essential.

Although this solution is designed to be user-friendly and efficient, the underlying technology is not new. The computer vision used is based on YOLO, a proven technique that has been applied for years for object and motion detection. The Telegram notifications also use an existing API. Despite appearing innovative, it involves a smart combination of existing technologies.se positives or negatives; the user remains responsible for all final breeding decisions.

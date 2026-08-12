# Science Adventure series All in One universal extractor

This project aims to unify and simplify the process of extracting science adventure visual novels for non-technical people.
Simply select a profile, point it to your install, select an output folder, and press go!
Windows and Linux systems are supported. Linux requires mono or wine to use some features.

You can download the latest release from the [releases](https://github.com/UNF0RM4TT3D/SciAdvAIOExtract/releases) section.

## Supported games
Full Steam Sci;Adv Library

- Chaos;Head Noah
- Steins;Gate
- Robotics;Notes Elite
- Chaos;Child
- Steins;Gate 0
- Robotics;Notes DaSH
- Steins;Gate Linear Bounded Phenogram
- Steins;Gate My Darling's Embrace
- Steins;Gate Elite

Non-Steam

- Occultic;Nine Fan Port
- Occultic;Nine Xwine port

Occultic;Nine profiles written by [itsrigs](https://github.com/rigatoni)

## Running or Building

You can download the current release from the [releases section](https://github.com/UNF0RM4TT3D/SciAdvAIOExtract/releases)

Then extract the zip and find the SciAdvAIOExtract executable and execute it.

On Windows a terminal window will pop up behind the main window, debugging output will be output there.

Linux requires Wine to be installed in $PATH (sorry SteamOS) and ideally also Mono, which speeds up execution of dotnet based dependencies greatly.

## Building or running on unsupported platforms.

Clone this repository or download a tagged source zip file and extract it.

```
# Create a new venv
python -m venv venv

# enter the venv

source ./venv/bin/activate

#on Windows use instead

.\winvenv\Scripts\Activate.ps1

# Install python dependencies
pip install -r requirements.txt

# Run

pyside6-project run

# Or build

pyside6-project deploy

# Building on windows requires MSVC installed and any components you may get prompted to install.

```

---

## Windows SmartScreen/Defender warnings/false positives.

The application isn't signed, and may trigger SmartScreen and Defender. I do not have access to a signing certificate and nuitka/pyside-deploy is know to trigger some AV solutions. [Link](https://www.reddit.com/r/learnpython/comments/13igjrl/nuitka_hello_world_binary_detected_as_malware_why/) [Link](https://forum.qt.io/topic/161256/pyside6-deploy-triggers-windows-deffender-wacatac-b-ml)

The source is available for inspection and modification, feel free to do analysis and run it from source. 

## Contributing

Pull requests and bug reports are very welcome. AI may be used, but needs to be disclosed.

## Other details

Other 5pb or MAGES. Visual Novels may also work, the profiles just need to be written. Feel free to open issues or pull requests for those too.

To extract CPK files (Chaos;Head Noah, Robotics;Notes Elite and DaSH) the project uses [CriPakTools.exe](https://github.com/esperknight/CriPakTools)

MPV is generally able to recognise the format on even unknown video and audio files (if run from terminal). So if you want to extract A/V MPV or other software capable of detecting media formats is strongly recommended.

This project is mostly licensed under the GNU GPL-v3 License, apart from files contained in the libs folder (MIT) and [FreeMote By UlyssesWu](https://github.com/UlyssesWu/FreeMote) (CC-BY-NC-SA 4.0), this means that you cannot use the extractor commercially for extracting Anonymous;Code or other psb.m

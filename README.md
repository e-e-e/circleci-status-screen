# circleci-status-screen

A script to show circle ci build status on a 32 x 64 LED matrix.

Look at this [Adafruit Tutorial](https://learn.adafruit.com/adafruit-rgb-matrix-plus-real-time-clock-hat-for-raspberry-pi/driving-matrices) for instructions on setting up the required hardware.

# Installation

Requires Python v2.7+

Clone this repo.

```
git clone https://github.com/e-e-e/circleci-status-screen
```

## Configure

This script loads environment variables from a .env file.
Create a `.env` file with the circleci-status-screen director.

**.env example**
```
PI=true # Include this variable only on the Raspberry Pi
CIRCLE_API_TOKEN=your_circle_api_token
USER_NAME=your_circleci_user
REPO_NAME=the_repository
```

## On a Raspberry Pi

### Install required dependencies

```sh
sudo apt-get update
sudo apt-get install python-dev python-imaging
sudo pip install circleclient python-dotenv
```

### Install and make [rpi-rgb-led-matrix](https://github.com/adafruit/rpi-rgb-led-matrix) driver

```sh
wget https://github.com/adafruit/rpi-rgb-led-matrix/archive/master.zip
unzip master.zip
cd rpi-rgb-led-matrix
make
# copy compiled code to your circleci-status-screen directory
cp ./rgbmatric.so ../circleci-status-screen
```

### Run

#### To run quick and easily:

```sh
cd cicleci-status-screen
sudo python status.py # sudo is required to access the GPIO pins on the pi
```

### Or automatically start on start up:

Make new file `circleci.service` within `/lib/systemd/system/`
```sh
sudo vim /lib/systemd/system/circleci.service
```
**circleci.service**
```systemd
[Unit]
Description=Circle ci status board
After=multi-user.target network-online.target time-sync.target timers.target

[Service]
Type=idle
ExecStartPre=/bin/sleep 60
ExecStart=/usr/bin/python -u /home/pi/circleci-status-screen/status.py
StandardOutput=inherit
StandardError=inherit
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Set permissions correctly for the service file.
```sh
sudo chmod 644 /lib/systemd/system/myscript.service
```

Then enable the service

```sh
sudo systemctl daemon-reload
sudo systemctl enable circleci.service
```

### Raspberry PI Nightmares

We found that a number of raspberry pi instabilities caused us issues.

If using WiFi:

1. Turn off power management for wlan0.
2. Ensure that wifi is set to your countries region.

If using systemd, also ensure `ExecStartPre=/bin/sleep 60` is added to your service. We found that if the python script started before the pi synced time, the process would hang.

## Without the RPI or LED matrix

You can run this code without the display simply by

```sh
virtualenv -p python2 env
source ./env/bin.activate
pip install pipenv
pipenv install
python status.py
```


# Naboris
This is the code repo for my tiny robot "Naboris." <br />
Learn how to build your own version here: https://www.instructables.com/id/Do-it-yourself-Autonomous-Tiny-Robot/

![Alt text](/naboris/static/naboris-small.jpeg)

# Project Goal
The objective is to create a small cheap (under $500) robotics platform that could autonomously navigate indoor environments with only a camera. This project is meant to demonstrate you don't need big fancy lab equipment and million dollar grants to do something cool in the field of robotics. The linked instructable explains how to get setup hardware-wise.

# Software setup
All installation commands will specifically be for Raspberry Pi's running Raspbian (the "host" computer). The expectation for this robot is you'll be developing headless (without a display) and thus remotely via SSH (the "remote" computer). The only thing you'll need on the remote is python 3.5 or higher installation. Any of the below packages are valid for the remote as well.

## Dependencies
Before you get started, you'll need these dependencies:
* Python 3.5 or higher: <br />
    ```wget https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tgz
    tar xzvf Python-3.6.0.tgz
    cd Python-3.6.0/
    ./configure
    make
    sudo make install
    ```
    source: https://raspberrypi.stackexchange.com/questions/59381/how-do-i-update-my-rpi3-to-python-3-6
* pip for Python 3.6:
    ```wget https://bootstrap.pypa.io/get-pip.py
    python3 get-pip.py
    ```
* PySerial: ```sudo pip3 install pyserial```
* PiCamera: http://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/
    * Make sure you replace "pip" with pip3

#### Optional packages:

* Matplotlib: ```sudo pip3 install matplotlib```
* Scipy: ```sudo pip3 install scipy```
* Numpy: ```sudo pip3 install scipy```
* Pygame: ```sudo pip3 install pygame```
* OpenCV: http://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/

## Installation
Install git if haven't done so: ```sudo apt-get install git```<br />
Download the repo:
```
cd ~
git clone https://github.com/Woz4tetra/Naboris
```
The package isn't on the python package index, so you'll need to symlink it:<br />
```sudo ln -s $PWD/Naboris/Atlasbuggy/atlasbuggy /usr/local/lib/python3.6/site-packages```<br /><br />
Test if worked:
```
python3
>>> import atlasbuggy
```

## My development environment
I'm using a mac to develop by SSH'ing into the raspberry pi via a DIY access point (see the instructable for details). I'm using Transmit by Panic to access the raspberry pi's files remotely.

# Try some code out
If you're the impatience type like me, you want a code library to impress you on the first date. So here's something you can run out of the box (with the dependencies). So assuming you have matplotlib and numpy installed, try the following out for size:
```bash
cd Naboris/naboris
python3 tryme.py
```
```python

```

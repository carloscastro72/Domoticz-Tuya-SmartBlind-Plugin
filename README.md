# Domoticz-Tuya-SmartBlind-Plugin

A Domoticz plugin to manage Tuya Smart Blind (Venetian Blinds EU)

## ONLY TESTED FOR Windows and Synology

With Python version 3.5 & Domoticz version 4.9700 (stable)
## Prerequisites

This plugin is based on the pull request of [`dominikandreas`](https://github.com/dominikandreas) on pytuya Python library by [`clach04`](https://github.com/clach04).
For the installation of this library, follow the Installation guide below.
See [`https://github.com/clach04/python-tuya/`](https://github.com/clach04/python-tuya/) and [`https://github.com/dominikandreas/python-tuya`](https://github.com/dominikandreas/python-tuya) for more information.

For the pytuya Python library, you need pycrypto. pycrypto can be installed with pip:
```
pip3 install pycrypto
```
See [`https://pypi.org/project/pycrypto/`](https://pypi.org/project/pycrypto/) for more information.

## Installation


```bash
#For Windows (create if not exists): 
cd C:\Program Files (x86)\Domoticz\plugins 
#For Synology:
cd /usr/local/domoticz/var/plugins/
```

Clone repository or download from [`https://github.com/carloscastro72/Domoticz-Tuya-SmartBlind-Plugin`](https://github.com/carloscastro72/Domoticz-Tuya-SmartBlind-Plugin) and unzip on plugins folder
```bash
git clone https://github.com/carloscastro72/Domoticz-Tuya-SmartBlind-Plugin
```
Navigate to plugin folder and create symlink to pytuya path
```bash
cd Domoticz-Tuya-SmartBlind-Plugin
#For Windows
mklink /D pytuya python-tuya\pytuya
#For Synology
ln -s python-tuya\pytuya pytuya
```

In the web UI, navigate to the Hardware page. In the hardware dropdown there will be an entry called "Tuya SmartBlind".

## Known issues

1/ python environment

Domoticz may not have the path to the pycrypto library in its python environment.
In this case you will observe something starting like that in the log:
* failed to load 'plugin.py', Python Path used was 
* Module Import failed, exception: 'ImportError'

To find where pycrypto is installed, in a shell:
```bash
pip3 show pycrypto
```
The Crypto directory should be present in the directory indicated with Location.

when you have it, just add a symbolic link to it in Domoticz-Tuya-SmartPlug-Plugin directory with ```ln -s```.
Example:
```bash
cd ~/domoticz/plugins/Domoticz-Tuya-SmartPlug-Plugin
ln -s /home/pi/.local/lib/python3.5/site-packages/Crypto Crypto
```

2/ Tuya app

The tuya app must be close. This limitation is due to the tuya device itself that support only one connection.

3/ Alternative crypto libraries

PyCryptodome or pyaes can be used instead of pycrypto. 


## Parameters

| Parameter | Value |
| :--- | :--- |
| **IP address** | IP of the Smart Plug eg. 192.168.1.231 |
| **DevID** | devID of the Smart Plug |
| **Local Key** | Local Key of the Smart Plug |
| **Debug** | default is 0 |

## DevID & Local Key Extraction

Recommanded method:
[`https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md`](https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md)

All the information can be found here:
[`https://github.com/clach04/python-tuya/`](https://github.com/clach04/python-tuya/)

## Acknowledgements

* Special thanks for all the hard work of [clach04](https://github.com/clach04), [`dominikandreas`](https://github.com/dominikandreas), [codetheweb](https://github.com/codetheweb/) and all the other contributers on [python-tuya](https://github.com/clach04/python-tuya) and [tuyapi](https://github.com/codetheweb/tuyapi) who have made communicating to Tuya devices possible with open source code. And thanks to  [`tixi`](https://github.com/tixi) or giving me a starting point in the creation of a Domoticz plugin 
* Domoticz team

# Domoticz Tuya Smart Blind Python Plugin
# MIT License
# Copyright (c) 2019 carloscastro72
# Permission is hereby granted, free of charge, to any person obtaining a copy       
# of this software and associated documentation files (the "Software"), to deal      
# in the Software without restriction, including without limitation the rights       
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell          
# copies of the Software, and to permit persons to whom the Software is              
# furnished to do so, subject to the following conditions:                           
#                                                                                      
# The above copyright notice and this permission notice shall be included in all     
# copies or substantial portions of the Software.                                    
#                                                                                      
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR         
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,           
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE        
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER             
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,      
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE      
# SOFTWARE.                                                                          


"""
<plugin key="hornet_tuya_smartblind_plugin" name="Tuya SmartBlind" author="hornet" version="3.0.0" externallink="https://github.com/carloscastro72/Domoticz-Tuya-SmartBlind-Plugin">
    <params>
        <param field="Address" label="IP address" width="200px" required="true"/>
        <param field="Mode1" label="DevID" width="200px" required="true"/>
        <param field="Mode2" label="Local Key" width="200px" required="true"/>
        <param field="Mode3" label="Time to open (seconds)" width="200px" required="true"/>
        <param field="Mode4" label="Time to close (seconds)" width="200px" required="true"/>
        <param field="Mode5" label="DPS always ON" width="200px" required="true" default="None"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="0"   value="0" default="true"/>
                <option label="1"   value="1"/>
                <option label="2"   value="2"/>
                <option label="4"   value="4"/>
                <option label="8"   value="8"/>
                <option label="16"  value="16"/>
                <option label="32"  value="32"/>
                <option label="64"  value="64"/>
                <option label="128" value="128"/>
            </options>
        </param>
    </params>
</plugin>
"""

# https://wiki.domoticz.com/wiki/Developing_a_Python_plugin
# Debugging
# Value     Meaning
# 0         None. All Python and framework debugging is disabled.
# 1         All. Very verbose log from plugin framework and plugin debug messages.
# 2         Mask value. Shows messages from Plugin Domoticz.Debug() calls only.
# 4         Mask Value. Shows high level framework messages only about major the plugin.
# 8         Mask Value. Shows plugin framework debug messages related to Devices objects.
# 16         Mask Value. Shows plugin framework debug messages related to Connections objects.
# 32         Mask Value. Shows plugin framework debug messages related to Images objects.
# 64         Mask Value. Dumps contents of inbound and outbound data from Connection objects.
# 128         Mask Value. Shows plugin framework debug messages related to the message queue.

import Domoticz
import pytuya
import time
import threading


########################################################################################
#
# plugin object
#
########################################################################################
class Blind:
    def __init__(self):
        self.__address = None  # IP address of the smartblind
        self.__devID = None  # devID of the smartblind
        self.__localKey = None  # localKey of the smartblind
        self.__device = None  # pytuya object of the smartblind
        self.__runAgain = self.__HB_BASE_FREQ  # heartbeat smartblind
        self.__connection = None  # connection to the tuya plug
        self.__plugs = None  # mapping between dps id and a plug object
        self.__state_machine = 0
        # state_machine: 0 -> no waiting msg ; 1 -> set command sent ; 2 -> status command sent
        return


class BasePlugin:
    #######################################################################
    #
    # constant definition
    #
    #######################################################################
    __HB_BASE_FREQ = 2  # heartbeat frequency (val x 10 seconds)
    __VALID_CMD = ('Open', 'Close', 'Stop')  # list of valid command

    #######################################################################
    #
    # constructor
    #
    #######################################################################
    def __init__(self):
        self.__address = None  # IP address of the smartblind
        self.__devID = None  # devID of the smartblind
        self.__localKey = None  # localKey of the smartblind
        self.__device = None  # pytuya object of the smartblind
        self.__runAgain = self.__HB_BASE_FREQ  # heartbeat smartblind
        self.__connection = None  # connection to the tuya plug
        self.__plugs = None  # mapping between dps id and a plug object
        self.__state_machine = 0  # state_machine: 0 -> no waiting msg ; 1 -> set command sent ; 2 -> status command sent
        self.__start_moving = None
        self.__start_level = None
        self.__level = 0
        self.__nValue = 0
        self.__running = 0
        self.__direction = None
        self.__on_running_timer = None
        return

    #######################################################################
    #
    # onStart Domoticz function
    #
    #######################################################################
    def onStart(self):

        # Debug mode
        if int(Parameters["Mode6"]) > 0:
            Domoticz.Debugging(int(Parameters["Mode6"]))
            Domoticz.Debug("Debugger started with level" + Parameters["Mode6"])

        Domoticz.Debug("onStart called")
        # get parameters
        self.__address = Parameters["Address"]
        self.__devID = Parameters["Mode1"]
        self.__localKey = Parameters["Mode2"]
        self.__timeToOpen = Parameters["Mode3"]
        self.__timeToClose = Parameters["Mode4"]
        self.__start_moving = None
        self.__on_running_timer = None

        # set the next heartbeat
        self.__runAgain = self.__HB_BASE_FREQ
        if (len(Devices) == 0):
            # create domoticz devices
            Options = {"LevelActions": "||",
                       "LevelNames": "Off|On|Stop",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="Tuya SmartBlind", Unit=1, Type=244, Switchtype=13, Options=Options).Create()
            Domoticz.Debug("Tuya SmartBlind Device created.")
        else:
            Domoticz.Debug("El dispositivo ya existe. " + str(Devices))

        self.__dom_devices = Devices

        # create the pytuya object
        self.__device = pytuya.CoverDevice(self.__devID, self.__address, self.__localKey)
        Domoticz.Debug(str(self.__device))

    def starting_movement(self, direction):
        self.__start_moving = time.time()
        self.__start_level = self.__level
        self.__direction = direction

    def stopping_movement(self):
        self.__start_moving = None
        self.__start_level = None
        self.__direction = None

    def update_levels(self):
        if self.__start_moving is None:
            return
        working_time = time.time() - self.__start_moving
        Domoticz.Debug("update_levels - working_time: " + str(working_time))
        if self.__direction == "off":  # open
            max_time = float(self.__timeToOpen)
            percent = int(round(float(working_time) * 100.0 / float(max_time)))
            new_level = int(self.__start_level) - int(percent)
            if new_level < 0:
                new_level = 0

            if new_level == 0:
                self.__nValue = 0
            elif new_level < 100:
                self.__nValue = 2
            self.__level = new_level
        elif self.__direction == "on":  # close
            max_time = float(self.__timeToClose)
            percent = int(round(float(working_time) * 100.0 / float(max_time)))
            new_level = int(self.__start_level) + int(percent)
            if new_level > 100:
                new_level = 100

            if new_level == 100:
                self.__nValue = 1
            elif new_level > 0:
                self.__nValue = 2
            self.__level = new_level
        Domoticz.Debug("update_levels - percent moved: " + str(working_time) + " new level: " + str(new_level))
        self.update_device()
        if working_time > max_time:
            self.stopping_movement()
            self.__device.stop()
            return

    #######################################################################
    #
    # onCommand Domoticz function
    #
    #######################################################################
    def onCommand(self, unit, command, level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(unit) + ": Command '" + str(command) + "' Level: " + str(level))
        if command == "Off":  # open blind
            if self.__direction == "on":
                command = "Stop"
            else:
                self.starting_movement("off")
                self.onRunning()
                self.__device.open()
        if command == "On":  # close blind
            if self.__direction == "off":
                command = "Stop"
            else:
                self.starting_movement("on")
                self.onRunning()
                self.__device.close()
        if command == "Stop":
            # self.__device.stop()
            self.__on_running_timer.cancel()
            self.stopping_movement()

    #######################################################################
    #
    # onHeartbeat Domoticz function
    #
    #######################################################################
    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.__runAgain -= 1
        if self.__runAgain == 0:
            self.__runAgain = self.__HB_BASE_FREQ
            state = self.__device.state()
            Domoticz.Log("State is: " + str(state))

    def onRunning(self):
        Domoticz.Debug("onRunning called")
        self.update_levels()
        if self.__direction is not None:
            self.__on_running_timer = threading.Timer(1, self.onRunning)
            self.__on_running_timer.start()

    def update_device(self):
        self.__dom_devices[1].Update(nValue=self.__nValue, sValue=str(self.__level), Switchtype=13, TimedOut=0)
        self.__dom_devices[1].Refresh()


########################################################################################
#
# Domoticz plugin management
#
########################################################################################
global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

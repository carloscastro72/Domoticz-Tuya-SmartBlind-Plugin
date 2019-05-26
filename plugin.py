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

########################################################################################
#
# plugin object
#
########################################################################################


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

        # set the next heartbeat
        self.__runAgain = self.__HB_BASE_FREQ
        if (len(Devices) == 0):
            # create domoticz devices
            Options = {"LevelActions": "||",
                       "LevelNames": "Off|On|Stop",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="Tuya SmartBlind", Unit=1, Type=244, Switchtype=15, Options=Options).Create()
            Domoticz.Debug("Tuya SmartBlind Device created.")
        else:
            Domoticz.Debug("El dispositivo ya existe. "+str(Devices))

        # create the pytuya object
        self.__device = pytuya.CoverDevice(self.__devID, self.__address, self.__localKey)

        Domoticz.Debug(str(self.__device))

        # state machine
        self.__state_machine = 1

        state = self.__device.state()
        Domoticz.Log("State is: " + str(state))

    #######################################################################
    #
    # onCommand Domoticz function
    #
    #######################################################################
    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Command '" + str(Command) + "' Level: " + str(Level))
        if Command == "Off":
            self.__device.open()
        if Command == "On":
            self.__device.close()
        if Command == "Stop":
            self.__device.stop()

    #######################################################################
    #
    # onHeartbeat Domoticz function
    #
    #######################################################################
    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.__runAgain -= 1
        if (self.__runAgain == 0):
            self.__runAgain = self.__HB_BASE_FREQ
            state = self.__device.state()
            Domoticz.Debug("State is:" + str(state))

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


################################################################################
# Generic helper functions
################################################################################

def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or Devices[Unit].TimedOut != TimedOut or AlwaysUpdate:
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Debug("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")

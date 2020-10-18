# -*- coding: utf-8 -*-
"""
Created on Tue Oct  6 12:30:22 2020

@author: useradmin-port970
"""

import psychopy as psy
from psychopy import sound, gui, visual, core, data, event
import numpy as np  # whole numpy lib is available, prepend 'np.'
import os  # handy system and path functions
import sys  # to get file system encoding
import serial  #connecting to the serial port (Arduino)

import copy
import random


#Dir
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

#OPEN THE SERIAL PORT TO COMMUNICATE WITH ARDUINO

# ser = serial.Serial('COM3', 9600, timeout=0)
# line = ser.readline()


#Participant information
expInfo={'Participant code':0000, 'Age (Years)':00, 'Gender':['M', 'F', 'Other'], 'Would you like to run this task using its default parameters?':True}
expName='Penalty'
dlg=gui.DlgFromDict(dictionary=expInfo, title='Participant Information', tip={'Would you like to run this task using its default parameters?': 'Default Penalty shoot'})
if dlg.OK ==False: 
    print('Closing port and exit')
    ser.close()
    core.quit()
expInfo['date'] = data.getDateStr()


# Experiment parameters

taskInfo_brief={'Count down':True,'Trial by trial feedback':True, 'Step size (ms)':33, 'Stop limit (ms)':150,'Lower limit (ms)':500,
                'n_go_trials (per block)':2, 'n_stop_trials (per block)':4,'n blocks':4, 'practice trials':False, 'n practice go trials':1,
                'n practice stop trials':1, 'Full Screen':True, 'Total bar height':15, 'Threat Mode':True}


# Display the goal an goakeeper
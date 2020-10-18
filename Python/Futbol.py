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
import math
import copy
import random


#Dir
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

#OPEN THE SERIAL PORT TO COMMUNICATE WITH ARDUINO

ser = serial.Serial('COM3', 9600, timeout=0)
line = ser.readline()


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

taskInfo_brief={'n_go_trials (per block)':2, 'n_stop_trials (per block)':4,'n blocks':4, 'practice trials':False, 'n practice go trials':1,
                'n practice stop trials':1, 'Full Screen':True, 'Pressure Mode':True}


if not expInfo['Would you like to run this task using its default parameters?']:
    dlg=gui.DlgFromDict(dictionary=taskInfo_brief, title='Experiment Parameters',
        tip={
        '% StopS':'# of trials that are Stops',
        'n trials':'Total number of main trials',
        'Step size (ms)':'If participant fails to stop the next Stop will be this much earlier in ms (i.e. staircase step size)', 
        'Stop limit (ms)':'What is the closest to the target the StopS trial can be?'
        # 'N Blocks':'How many blocks to perfom'
        })
    if dlg.OK ==False: 
        ser.close()
        core.quit()

# Block and trial types
trials=[0]*taskInfo_brief['n_stop_trials (per block)']+[1]*taskInfo_brief['n_go_trials (per block)']
print('Type of trials (0 = Stop):', trials)

if taskInfo_brief['Pressure Mode']:
    if taskInfo_brief['n blocks']% 2 == 0:
        blocks = [0]*int(taskInfo_brief['n blocks']/2) + [1]*int(taskInfo_brief['n blocks']/2)
    else:
        blocks = [1]*int(math.ceil(taskInfo_brief['n blocks']/2)) + [0]*int(math.floor(taskInfo_brief['n blocks']/2))
else:
    blocks = [0]*int(taskInfo_brief['n blocks'])
print ('Block type (0 is non-pressure): ')
#Could be a good idea to have a goal with public behind for under pressure
np.random.shuffle(trials)
block_trials = trials
    
# Random blocks
np.random.shuffle(blocks)
print (blocks)



# Display the goal an goalkeeper



while True :
    print (line)





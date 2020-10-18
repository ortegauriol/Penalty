
"""
Open-Source Anticipated Response Inhibition (OSARI) 
Created in PsychoPy v3.1.2

Written by: Rebecca J Hirst [1] and Rohan Puri [2]
Edited by: Jason L He [3]

[1] Trinity College Institute of Neuroscience, Trinity College Dublin
[2] University of Tasmania
[3] John Hopkins School of Medicine 

Mail to Author:  HirstR@tcd.ie or rj.hirst@hotmail.co.uk
Version 1.0;
Create Date 04062019;
Last edited 011019

References:
    
Guthrie, M. D., Gilbert, D. L., Huddleston, D. A., Pedapati, E. V., Horn, P. S., Mostofsky, S. H., & Wu, S. W. (2018). 
Online Transcranial Magnetic Stimulation Protocol for Measuring Cortical Physiology Associated with Response Inhibition.
Journal of Visualized Experiments, (132), 1-7. http://doi.org/10.3791/56789

He, J. L., Fuelscher, I., Coxon, J., Barhoun, P., Parmar, D., Enticott, P. G., & Hyde, C. (2018). 
Impaired motor inhibition in developmental coordination disorder. Brain and Cognition, 127(August),
23-33. http://doi.org/10.1016/j.bandc.2018.09.002

To Do:
    Add triggers for EEG/TMS (from final column of input file)
    Currently we check if the button has been lifted at the start of each frame, if it has been lifted we then get the RT through checking the clock. 
        *however* if the button has been lifted say 1ms after the win refreshed, this may lead to a RT that is over estimated by the duration of 1 frame - 1ms. 
         For this reason, we need to work on using the hardware.keyboard module to see if we can get more accurate timing for key lifts (note this is easier for key presses). 
    Consider making it so that a "stop" trial always finishes Xms following stop, currently the trial finishes at the time that the bar would have completely filled.
    Add "out of" to the correct count feedback at end
    Ensure "stop-limit_adjusted" calculation is consistent with other calculations (i.e. in relation to the adjusted target line) 
    Check that it is not possible to fall below the stop limit (i.e. an error should be thrown if this happens)
Input (optional):
    
    txt file contianing 3 columns:
        Col 1: Trial n
        Col 2: Trial type (0 = StopS, 1 = go)
        Col 3: Stop time
        Col 4: Trigger time (time relative to start of trial) 
        
Output:
    
    Block: block number 
    
    TrialType: Practice or real trial 
    
    Trial: Trial number_text
    
    Signal: 1 = Go
            0 = Stop
    
    Response: What the participants response was ( 0 = no lift, 1 = lift)
    
    RT: Lift time of participants relative to the starting line (to 2 decimal places)
    
    SSD: Stop Signal Distance (relative to starting line) if the trial was a stop trial.
    Note: 
        Make sure the resolution of "testMonitor" in monitor centre matches actual screen resolution 

Updated by ortegauriol@gmail.com, September 2020

	1. Bug (Solved):  when cancel on participant information window serial port communication kept open, blocking the port communication for a second instance without unplug - plug cycle.
	2. Inclusion of 'Threat mode' on task configuration
	3. If threat mode is not checked all blocks are non-threat (0)
	4. Blocks and trials are flexible and defined from GUI
	5. Blocks if odd number =  50/50;  if even number threats blocks are 1 more.
	6. Random blocks
	7. The trials of each block are randomized independently.
	8. Threat visual cue incorporated on top right corner of the window
	9. Threat removed if block is non-threat
	10. Block type included in Output
    11. Updated instructions declaring Trigger instead of space key.

"""

#Import relevant modules
from __future__ import absolute_import, division
from psychopy import sound, gui, visual, core, data, event
import numpy as np  # whole numpy lib is available, prepend 'np.'
import os  # handy system and path functions
import sys  # to get file system encoding
import pyglet
import math
import serial  #connecting to the serial port (Arduino)

import copy
import random
#import csv

_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

#--------------------------set up exp info gui------------

#GUI input

#setting up serial port
ser = serial.Serial('COM3', 9600, timeout=0)
line = ser.readline()

#About participant
expInfo={'Participant code':0000, 'Age (Years)':00, 'Sex':['M', 'F', 'Other'], 'Would you like to run this task using its default parameters?':True, 'Spaceship':False}
expName='StopSignal'
dlg=gui.DlgFromDict(dictionary=expInfo, title='Participant Informationa', tip={'Would you like to run this task using its default parameters?': 'This will run a behavioural task with no triggers for use with TMS ect. No further options will be presented'})
if dlg.OK ==False: 
    print('Closing port and exit')
    ser.close()
    core.quit()
expInfo['date'] = data.getDateStr()

#About the task
taskInfo_brief={'Count down':True,'Trial by trial feedback':True, 'Step size (ms)':33, 'Stop limit (ms)':150,'Lower limit (ms)':500,
                'n_go_trials (per block)':2, 'n_stop_trials (per block)':4,'n blocks':4, 'practice trials':False, 'n practice go trials':1,
                'n practice stop trials':1, 'Full Screen':True, 'Total bar height':15, 'Threat Mode':True}

#original taskInfo dict
#taskInfo_brief={'Count down':True,'Trial by trial feedback':True, 'Step size (ms)':25, 'Stop limit (ms)':150, 'n_go_trials (per block)':10, 'n_stop_trials (per block)':2
#        ,'n trials':260, 'n blocks':1, 'practice trials':True, 'n practice go trials':1, 'n practice stop trials':1, '% StopS':25, 'Full Screen':True, 'Total bar height':15}

Bar_top=taskInfo_brief['Total bar height']/2
Target_pos=(.8*taskInfo_brief['Total bar height'])-Bar_top


taskInfo={'Bar base below fixation (cm)':Bar_top, 'Bar width (cm)':3, 'Bar top above fixation (cm)':Bar_top, 'Target line width (cm)':5, 
        'Target line above fixation (cm)':Target_pos, 'rise velocity (cm/sec)':15
        , 'StopS start pos. (ms)':300}

if not expInfo['Would you like to run this task using its default parameters?']:
    dlg=gui.DlgFromDict(dictionary=taskInfo_brief, title='Experiment Parameters',
        tip={
        'Count down':'Do you want a countdown before the bar starts filling?',
        '% StopS':'Percentage of trials that are StopS, remember to ensure percentage is compatible with n trials',
        'n trials':'Total number of main trials', 
        'Step size (ms)':'If participant fails to stop the next Stop will be this much earlier in ms (i.e. staircase step size)', 
        'Stop limit (ms)':'What is the closest to the target the StopS trial can be?'
        # 'N Blocks':'How many blocks to perfom'
        })
    if dlg.OK ==False: 
        ser.close()
        core.quit()

#About the hardware (i.e. triggers ect)

hardwareInfo={'Parallel port triggers':False, 'Import trial info file':False, 'Trigger file path':'example_input.txt'}
if not expInfo['Would you like to run this task using its default parameters?']:
    dlg=gui.DlgFromDict(dictionary=hardwareInfo, title='Hardware requirements')
    if dlg.OK ==False: 
        ser.close()
        core.quit()

#get the trigger file 
if hardwareInfo['Import trial info file']:
    b = open(hardwareInfo['Trigger file path'], "r").readlines()
    line = b[0].split()#work through each row by doing this 
    line[0]#get each col value for each trial by doing this 

#check if the number of trials is governed by external txt file or gui
if hardwareInfo['Import trial info file']:
    n_trials=len(b)
    trials=[]
    stoptimes=[]
    for trial in range(0, len(b)):
        line = b[trial].split()
        trials.append(int(line[1]))#the info regarding the trial type is in the second column
        stoptimes.append(float(line[2]))#the info regarding the stoptime is in the third column
else:
   # n_trials=taskInfo_brief['n trials']
   # trials=[1]*n_trials
    trials=[0]*taskInfo_brief['n_stop_trials (per block)']+[1]*taskInfo_brief['n_go_trials (per block)']
    print(trials)
    
#Check if proportion of specified trials is compatible with trials 
#create array of 0s (StopStrials) and 1s (go trials) based on user input.

#originally the number of trials was set based on percentages - now allow user to state exactly how many trials of each they want 
#if not hardwareInfo['Import trial info file']:#if we are not using an external file to set the number of trials and the type of each trial...
#    if not ((taskInfo_brief['% StopS']/100)*len(trials)).is_integer():#if the requested %StopS trials does not create an integer...
#        #throw error to reset number of trials
#        print('Percentage StopS trials does not make a whole number, reset %StopS or n trials')#quit and tell the user to re-enter compatible info
#        print('-----------ending task-----------')
#        core.quit()
#    else: #else set this perceptage of trials to be StopS trials (i.e. "0") 
#        #trials[:int(((taskInfo_brief['% StopS']/100)*int(len(trials)))-1)]=[0]*int(((taskInfo_brief['% StopS']/100)*len(trials))-1)
#        trials[:int(((taskInfo_brief['% StopS']/100)*int(len(trials))))]=[0]*int(((taskInfo_brief['% StopS']/100)*len(trials)))

    
# Blocks will be divided in a 50/50 way and shuffled to be random. if n_blocks is Pair; if Not pair more threads than non-threat blcks.
# Threat blocks == 1 && Non-Threat block == 0
if taskInfo_brief['Threat Mode']:
    if taskInfo_brief['n blocks']% 2 == 0:
        blocks = [0]*int(taskInfo_brief['n blocks']/2) + [1]*int(taskInfo_brief['n blocks']/2)
    else:
        blocks = [1]*int(math.ceil(taskInfo_brief['n blocks']/2)) + [0]*int(math.floor(taskInfo_brief['n blocks']/2))
else:
    blocks = [0]*int(taskInfo_brief['n blocks'])
# Random blocks
np.random.shuffle(blocks)
print (blocks)


#randomly shuffle the trials - note, this will not randomise the trials if an imported file is used. Trials must be entered into the .txt file in the desired order.
if not hardwareInfo['Import trial info file']:#only randomly shuffle the trials if they have not been manually imported
    if len(blocks) > 1:
        block_trials = []
        for sublist in blocks:
            block_trials.append(copy.deepcopy(trials))
        for sublist in block_trials:
            np.random.shuffle(sublist)
    else:    
        np.random.shuffle(trials)
        block_trials = trials
# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
#Check if a "data" output folder exists in this directory, and make one if not.
if not os.path.exists(_thisDir + os.sep +'data/'):
    print('Data folder did not exist, making one in current directory')
    os.makedirs(_thisDir + os.sep +'data/')
    

#Output file updated as requested
Output = _thisDir + os.sep + u'data/OSARI_%s_%s_%s' % (expInfo['Participant code'], expName, expInfo['date'])
with open(Output+'.txt', 'a') as b:
    b.write('Threat Block#	TrialType	Trial	Signal	Response success 	RT	SSD\n')
    

if not os.path.exists(_thisDir + os.sep +'logfiles/'):
    print('Logfile folder did not exist, making one in current directory')
    os.makedirs(_thisDir + os.sep +'logfiles/')
    
#Set up the window in which we will present stimuli
win = visual.Window(
    fullscr=taskInfo_brief['Full Screen'],
    winType='pyglet',
    monitor='testMonitor', color=[-1,-1,-1], colorSpace='rgb',
    blendMode='avg', mouseVisible = False, allowGUI=False)

#Add in the practice trials if we need them
if taskInfo_brief['practice trials']:
    #Add on the practice trials to the list of trials 
    practice_trials =[1]*taskInfo_brief['n practice go trials']+[0]*taskInfo_brief['n practice stop trials']
    trials_no_prac=trials
    trials=practice_trials+trials
    practice_go_inst=visual.TextStim(win, pos=[0, 0], height=1, color= [1,1,1],
        text="Ready for %s practice Go trials?"%(taskInfo_brief['n practice go trials']), units='cm' )
    practice_stop_inst=visual.TextStim(win, pos=[0, 0], height=1, color= [1,1,1],
        text="Ready for %s practice Stop trials?"%(taskInfo_brief['n practice stop trials']), units='cm' )
    understand=visual.TextStim(win, pos=[0, 0], height=1, color= [1,1,1],
        text="Do you understand the task?", units='cm' )

# store frame rate of monitor if we can measure it, most of times is 60
expInfo['frameRate'] = win.getActualFrameRate()

frame_dur=1000/expInfo['frameRate']
cm_per_frame=((taskInfo['rise velocity (cm/sec)']/expInfo['frameRate']))
increase=cm_per_frame

print('Monitor frame rate is %s' %(expInfo['frameRate']))
print('Bar will rise %s cm per frame, thats %s cm per second'%(increase, taskInfo['rise velocity (cm/sec)']))
cm_to_move=(taskInfo['Bar base below fixation (cm)']+taskInfo['Bar top above fixation (cm)'])

Time_from_base_to_top=(taskInfo_brief['Total bar height']/taskInfo['rise velocity (cm/sec)'])*1000
frames_from_base_to_top = Time_from_base_to_top/frame_dur

#recalculating overshoot/udershoot
backbar_overshoot = (math.ceil(frames_from_base_to_top)-frames_from_base_to_top)*cm_per_frame
backbar_undershoot = (math.floor(frames_from_base_to_top)-frames_from_base_to_top)*cm_per_frame

#the overshoot or undershoot may be closer to the actual desired bar height, lets check which is closer and use this.
if backbar_overshoot< abs(backbar_undershoot):#if the overshoot is smaller than the undershoot, use the overshoot
    optimal_difference=backbar_overshoot
else:#if the undershoot is smaller than the overshoot, use the undershoot
    optimal_difference=backbar_undershoot
#tell the user which one we are using to make logic clear
print('Overshoot: %.10f, Undershoot: %.10f, Optimal difference: %.10f'%(backbar_overshoot, backbar_undershoot, optimal_difference))

if optimal_difference !=0:
    print('Distance to move from base to top of background bar is not divisible by distance traveled per frame. Bar will be adjusted by %.10f'%(optimal_difference))


#non adjusted time from base to targetline (i.e. before correcting fro over/undershoot)
cm_to_move_to_targetline_non_adj = Bar_top+Target_pos
Time_from_base_to_targetline_non_adj=(cm_to_move_to_targetline_non_adj/taskInfo['rise velocity (cm/sec)'])*1000#this is the calculation for the print out 
frames_from_base_to_target=Time_from_base_to_targetline_non_adj/frame_dur

#need to make sure the distance from the base to the target line is divisible by cm per frame (i.e. it would be possible for the participant to actually hit the target line)
target_overshoot = (math.ceil(frames_from_base_to_target)-frames_from_base_to_target)*cm_per_frame
target_undershoot = (math.floor(frames_from_base_to_target)-frames_from_base_to_target)*cm_per_frame

#the overshoot or undershoot may be closer to the actual desired bar height, lets check which is closer and use this.
if target_overshoot< abs(target_undershoot):#if the overshoot is smaller than the undershoot, use the overshoot
    target_optimal_difference=target_overshoot
else:#if the undershoot is smaller than the overshoot, use the undershoot
    target_optimal_difference=target_undershoot
#tell the user which one we are using to make logic clear
print('target_Overshoot: %.10f, target_Undershoot: %.10f, target_Optimal difference: %.10f'%(target_overshoot, target_undershoot, target_optimal_difference))

if target_optimal_difference !=0:
    print('Distance to move to target is not divisible by distance traveled per frame. Bar will be adjusted by %.10f'%(target_optimal_difference))
    #Adjust the distance to move by taking into account the overshoot
cm_to_move_to_targetline=(taskInfo['Bar base below fixation (cm)']+taskInfo['Target line above fixation (cm)'])+target_optimal_difference
Target_pos_adjusted=taskInfo['Target line above fixation (cm)']+target_optimal_difference
Time_from_base_to_targetline=(cm_to_move_to_targetline/taskInfo['rise velocity (cm/sec)'])*1000#this is the time from base to taget taking into account over/undershoot
print('bar has %s cm to travel and will take %s ms to rise to targetline'%(cm_to_move_to_targetline, Time_from_base_to_targetline))

stoptime=taskInfo['StopS start pos. (ms)']#next step is to make this number change depending on if response was correct or incorrect
StopSpos=(Time_from_base_to_targetline-stoptime)*(taskInfo['rise velocity (cm/sec)']/1000)
print('Bar will stop at %s cm'%(StopSpos))

#take into acount the refresh rate of the monitor to ensure that the Stop position is divisible by the distance traveled per frame (i.e. the constraints of the monitor allow this stop position).

#recalculating SSD over/undershoot
#time_from_base_to_SSD=((cm_to_move_to_targetline-StopSpos)/taskInfo['rise velocity (cm/sec)'])*1000
time_from_base_to_SSD=Time_from_base_to_targetline-stoptime#(StopSpos/taskInfo['rise velocity (cm/sec)'])*1000
frames_from_base_to_SSD = time_from_base_to_SSD/frame_dur
SSD_overshoot = (math.ceil(frames_from_base_to_SSD)-frames_from_base_to_SSD)*cm_per_frame
SSD_undershoot = (math.floor(frames_from_base_to_SSD)-frames_from_base_to_SSD)*cm_per_frame

#the overshoot or undershoot may be closer to the actual desired bar height, lets check which is closer and use this.
if SSD_overshoot< abs(SSD_undershoot):#if the overshoot is smaller than the undershoot, use the overshoot
    SSD_optimal_difference=SSD_overshoot
else:#if the undershoot is smaller than the overshoot, use the undershoot
    SSD_optimal_difference=SSD_undershoot
print('SSD Overshoot: %.10f, SSD Undershoot: %.10f, SSD Optimal difference: %.10f'%(SSD_overshoot, SSD_undershoot, SSD_optimal_difference))

StopSpos_adjusted=StopSpos+SSD_optimal_difference
#StopSpos_adjusted_time=((cm_to_move_to_targetline-StopSpos_adjusted)/taskInfo['rise velocity (cm/sec)'])*1000#for the log file
StopSpos_adjusted_time=(StopSpos_adjusted/taskInfo['rise velocity (cm/sec)'])*1000#for the log file
print('Initial StopSpos %s . This is not divisible by the distance traveled per frame. Adjusted to %s'%(StopSpos, StopSpos_adjusted))


#Method to detect if a button is currently being pressed.
#Known issues with using iohub on Mac with security settings 
#Bypass method noted on discourse page at: https://discourse.psychopy.org/t/tracking-key-release/1099

#key=pyglet.window.key
#keyboard = key.KeyStateHandler()
#win.winHandle.push_handlers(keyboard)

feedback_dist=-8#where on the x axis (in cm) do you want the feedback to appear

#Instructions
Main_instructions = visual.TextStim(win, pos=[0, 0], height=1, color=[1,1,1],
    text="Press and hold the Trigger untill the bar reaches the target\n\nIf the bar stops rising keep holding the Trigger", units='cm')
if expInfo['Spaceship']:
    Main_instructions = visual.TextStim(win, pos=[0, 0], height=1, color=[1,1,1],
        text="Help the alien land his ship!\n\nPress and hold the Trigger untill the yellow on the UFO line reaches the yellow target line\n\nIf the UFO stops rising keep holding the Trigger!", units='cm')
practice_prepare = visual.TextStim(win, pos=[0, 0], height=1, color=[1,1,1],
    text="First lets practice!", units='cm')
PressKey_instructions = visual.TextStim(win, pos=[0, 0], height=1, color=[1,1,1],
    text="Press and hold the Trigger when ready!", units='cm')
TooSoon_text = visual.TextStim(win, pos=[feedback_dist, 0], height=1, color=[1,1,1],
    text="Press and hold the Trigger when ready!" , units='cm')
incorrectstop = visual.TextStim(win, pos=[feedback_dist, 0], height=1, color=[1,1,1],
    text="Oops! Bar full! Trigger held too long" , units='cm')
incorrectgo = visual.TextStim(win, pos=[feedback_dist, 0], height=1, color=[1,1,1],
    text="Oops! That was a Stop trial" , units='cm')
correctstop=visual.TextStim(win, pos=[feedback_dist, 0], height=1, color=[1,1,1],
    text="Correct stop!" , units='cm')
wrongKey=visual.TextStim(win, pos=[feedback_dist, 0], height=1, color=[1,1,1],
    text="WrongKey - Please press the Trigger", units='cm' )
countdown_clock=core.Clock()
number_text = visual.TextStim(win, pos=[0, 0],height=.1, color=[-1,-1,-1], text="1")



def waitSwitch():
    line = ser.readline()
    print('waiti line',line)
    while len(line)==0:
        line = ser.readline()
        core.wait(0.1)
        # print('wait line2',line)


def countdown():#give countdown and if finger is lifted say this is too soon and restart 
    if taskInfo_brief['Count down']:
        print ('coundown TRUE')
        countdown_clock.reset()
        line = ser.readline()
        while countdown_clock.getTime()<4:#whilst less than 4 seconds
            while int(countdown_clock.getTime())<4:
                line = ser.readline()
                if len(line)>0: #keyboard[key.SPACE]:
                    number_text.text="%s"%(3-int(countdown_clock.getTime()))
                else:
                    TooSoon_text.draw()
                    win.flip()
                    waitSwitch()
                    #k = event.waitKeys()
                    #if k[0]=='escape':#make sure the user can still quit in this loop
                        #print('User pressed escape, quiting now')
                        #win.close()
                        #core.quit()
                    countdown_clock.reset()
                Bar.draw()
                if expInfo['Spaceship']:
                    Spaceship.draw()
                targetLine.draw()
                if int(countdown_clock.getTime())<3:
                    number_text.draw()
                fillBar.draw()
                win.flip()
    else:
        print ('coundown False')
        ser.reset_input_buffer()
        line = ser.readline()
        if len(line)>0: #keyboard[key.SPACE]:
            core.wait(0.5)
        else:
            #TooSoon_text.draw()
            win.flip()
            waitSwitch()
        Bar.draw()
        fillBar.draw()
        win.flip()
        # core.wait(1)
        # while len(line)==0:
        #     line = ser.readline()
        #     core.wait(0.05)
        #     print ("countdown Line", line)

#Stimuli
bar_width_vert1=0-(taskInfo['Bar width (cm)']/2)
bar_width_vert2=(taskInfo['Bar width (cm)']/2)


#use vertices to have more control over the position and size of the stimulus
vert = [(bar_width_vert1,0-taskInfo['Bar base below fixation (cm)']), (bar_width_vert1,0-taskInfo['Bar base below fixation (cm)']+.01), 
        (bar_width_vert2,0-taskInfo['Bar base below fixation (cm)']+.01), (bar_width_vert2,0-taskInfo['Bar base below fixation (cm)'])]

#position and size of the background bar (based on user input)
fullvert_orig = [(bar_width_vert1,0-taskInfo['Bar base below fixation (cm)']),(bar_width_vert1,taskInfo['Bar top above fixation (cm)']),
        (bar_width_vert2,taskInfo['Bar top above fixation (cm)']),(bar_width_vert2,0-taskInfo['Bar base below fixation (cm)'])]

#vertices of the full white bar in the background - acounting for overshoot by adding the overshoot to the top 2 vertices (i.e. we increase the size of the background bar). 
fullvert = [(bar_width_vert1,0-taskInfo['Bar base below fixation (cm)']),(bar_width_vert1,taskInfo['Bar top above fixation (cm)']+optimal_difference),
        (bar_width_vert2,taskInfo['Bar top above fixation (cm)']+optimal_difference),(bar_width_vert2,0-taskInfo['Bar base below fixation (cm)'])]

TL_width_vert1=0-(taskInfo['Target line width (cm)']/2)
TL_width_vert2=(taskInfo['Target line width (cm)']/2)

#The 'Target line above fixation (cm)' input from the GUI specifies the location of the middle of the target line. The actual lower and upper vertices will 
#be this position +/-.1
Target_pos_adjusted
targetLinevert = [(TL_width_vert1,Target_pos_adjusted-.1),(TL_width_vert1,Target_pos_adjusted+.1),
        (TL_width_vert2,Target_pos_adjusted+.1),(TL_width_vert2,Target_pos_adjusted-.1)]

fillBar= visual.ShapeStim(win, fillColor='skyblue', lineWidth=0, opacity=1, units='cm', vertices=vert)
Bar = visual.ShapeStim(win, vertices=fullvert, fillColor='white', lineWidth=0, opacity=1, units='cm')
targetLine = visual.ShapeStim(win, vertices=targetLinevert, fillColor='yellow', lineWidth=0, opacity=1, units='cm')

print(0-taskInfo['Bar base below fixation (cm)'])

Spaceship_height_cm=2
Spaceship=visual.ImageStim(win, image='Stimuli'+os.sep+'Spaceship.png', pos=(0, vert[2][1]-(Spaceship_height_cm/2)), units='cm')
Spaceship_practice_im=visual.ImageStim(win, image='Stimuli'+os.sep+'Practice_Image.png', pos=(10, 0), units='cm')

# Define the threat visual cue
Threatfeed = visual.ImageStim(win, image='Stimuli'+os.sep+'Hazard.png', pos=(0.8, 0.7), units='norm')


#Trial loop
inc=0
correct=[]

stepsize_ms=taskInfo_brief['Step size (ms)']
stoplimit_ms=taskInfo_brief['Stop limit (ms)']

#Need to take into acount the monitor refresh rate when calculating the stepsize. Take the overshoot into account and save in log file for user. 
frames_to_cover_stepsize=stepsize_ms/frame_dur
stepsize_overshoot = (math.ceil(frames_to_cover_stepsize)-frames_to_cover_stepsize)*cm_per_frame
stepsize_undershoot = (math.floor(frames_to_cover_stepsize)-frames_to_cover_stepsize)*cm_per_frame

#the overshoot or undershoot may be closer to the actual desired bar height, lets check which is closer and use this.
if stepsize_overshoot< abs(stepsize_undershoot):#if the overshoot is smaller than the undershoot, use the overshoot
    stepsize_optimal_difference=stepsize_overshoot
else:#if the undershoot is smaller than the overshoot, use the undershoot
    stepsize_optimal_difference=stepsize_undershoot
print('stepsize overshoot: %.10f, stepsize undershoot: %.10f, stepsize optimal difference: %.10f'%(stepsize_overshoot, stepsize_undershoot, stepsize_optimal_difference))
stepsize_optimal_difference_time=stepsize_optimal_difference*1000/taskInfo['rise velocity (cm/sec)']
#stepsize_optimal_difference_time=frames_to_cover_stepsize*frame_dur
#stepsize_adjusted=stepsize_ms+stepsize_optimal_difference
stepsize_adjusted=stepsize_ms+stepsize_optimal_difference_time
print('Initial stepsize %s ms. The distance travelled in this time is not divisible by the distance traveled per frame. Adjusting stepsize to %s'%(stepsize_ms, stepsize_adjusted))
cm_moved_in_stoplimit=(stoplimit_ms*taskInfo['rise velocity (cm/sec)']/1000)
#cm_moved_in_stoplimit=(stoplimit_ms/expInfo['frameRate'])*cm_per_frame

#recalculating stoplimit_overshoot/undershoot
frames_to_cover_stoplimit=stoplimit_ms/frame_dur
stoplimit_overshoot= (math.ceil(frames_to_cover_stoplimit)-frames_to_cover_stoplimit)*cm_per_frame
stoplimit_undershoot= (math.floor(frames_to_cover_stoplimit)-frames_to_cover_stoplimit)*cm_per_frame


#the overshoot or undershoot may be closer to the actual desired bar height, lets check which is closer and use this.
if stoplimit_overshoot< abs(stoplimit_undershoot):#if the overshoot is smaller than the undershoot, use the overshoot
    stoplimit_optimal_difference=stoplimit_overshoot
else:#if the undershoot is smaller than the overshoot, use the undershoot
    stoplimit_optimal_difference=stoplimit_undershoot
print('stoplimit Overshoot: %.10f, stoplimit Undershoot: %.10f, stoplimit Optimal difference: %.10f'%(stoplimit_overshoot, stoplimit_undershoot, stoplimit_optimal_difference))
#stoplimit_adjusted=stoplimit_ms+ (stoplimit_optimal_difference*1000/taskInfo['rise velocity (cm/sec)']
stoplimit_adjusted=stoplimit_ms+stoplimit_optimal_difference
print('Initial stoplimit %s ms. The distance travelled in this this time %s is not divisible by the distance traveled per frame. stoplimit overshoot %s adjusting stoplimit to %s'%(stoplimit_ms, cm_moved_in_stoplimit, stoplimit_optimal_difference, stoplimit_adjusted))

#A clock to keep track of the trial time 
trialClock=core.Clock()

#keep track of feedback to give individual feedback at the end
correct_go_distances=[]
correct_go_distances_ms=[]
correct_gos=0
correct_StopSs=0

count=0

#Save the parameters to a log file 
log_filename = _thisDir + os.sep + u'logfiles/Log_file%s_%s_%s' % (expInfo['Participant code'], expName, expInfo['date'])
with open(log_filename+'.txt', 'a') as b:
   # b.write('Participant code: %s\nCountdown: %s\nTrial by Trial feedback : %s\nStepsize (ms) : %s\nStepsize (ms - Adjusted for frame rate) : %s\nStop limit (ms) : %s\nStop limit (ms - adjusted for frame rate) : %s\nn trials : %s\nPercentage Stop trials : %s\nStopS start pos. (ms) : %s\n StopS start pos. (ms adjusted for frame rate; note this will change dynamically on each trial) : %s\nTotal bar height (cm): %s'%(expInfo['Participant code'], taskInfo_brief['Count down'], taskInfo_brief['Trial by trial feedback'], taskInfo_brief['Step size (ms)'],stepsize_adjusted, taskInfo_brief['Stop limit (ms)'],stoplimit_adjusted,  taskInfo_brief['n trials'], taskInfo_brief['% StopS'], taskInfo['StopS start pos. (ms)'], StopSpos_adjusted_time, taskInfo_brief['Total bar height']))
    b.write('Participant code: %s\nCountdown: %s\nTrial by Trial feedback : %s\nStepsize (ms) : %s\nStepsize (ms - Adjusted for frame rate) : %s\nStop limit (ms) : %s\nStop limit (ms - adjusted for frame rate) : %s\nStopS start pos. (ms) : %s\n StopS start pos. (ms adjusted for frame rate; note this will change dynamically on each trial) : %s\nTotal bar height (cm): %s'%(expInfo['Participant code'], taskInfo_brief['Count down'], taskInfo_brief['Trial by trial feedback'], taskInfo_brief['Step size (ms)'],stepsize_adjusted, taskInfo_brief['Stop limit (ms)'],stoplimit_adjusted,  taskInfo['StopS start pos. (ms)'], StopSpos_adjusted_time, taskInfo_brief['Total bar height']))

with open(log_filename+'.txt', 'a') as b:
    b.write('\n\n Now logging actual trial velocity of each trial (based on recorded frame durations)...')


block_count=0
trial_count=0
practice=True

#draw the main instructions
Main_instructions.draw()
if expInfo['Spaceship']:
    Spaceship_practice_im.draw()
win.flip()
core.wait(1)
T_stop = []#Stop trials stop position variables for threat and non
NT_stop= []
waitSwitch()
#event.waitKeys()
practice_prepare.draw()
win.flip()
waitSwitch()
#event.waitKeys()
original_time = stoptime
for block in range(taskInfo_brief['n blocks']):
    block_type = blocks[block]
    print('block type: ', block_type)
    trials = block_trials[block]
    print('Trials: ', trials)
    
    print('Threat Track', T_stop)
    print('NT Track', NT_stop)
    
    # continue from the previous block stop location
    if block_type == 0 and not NT_stop:
        print('original stop')
        stoptime = original_time
    elif block_type == 0 and NT_stop:
        stoptime = NT_stop
    
    if block_type == 1 and not T_stop:
        print('original stop')
        stoptime = original_time
    elif block_type == 1 and T_stop:
        stoptime = T_stop

    if block_count>0:#if more than 1 block has been completed
        Threatfeed.setAutoDraw(False)
        Blocks_completed = visual.TextStim(win, pos=[0, 0], height=1, color=[1,1,1],
            text="Block %s of %s complete!!\n\nPress the trigger when ready to continue!"%(block_count, taskInfo_brief['n blocks']), units='cm')
        Blocks_completed.draw()
        win.flip()
        core.wait(1)#this is so that they don't accidentally press a button and move past the break screen
        waitSwitch()
        #event.waitKeys()
    block_count=block_count+1
    for trial in trials:
        targetLine.fillColor='yellow'
        trial_count=trial_count+1
        if taskInfo_brief['practice trials'] and block_count==1:#if this trial is one of the practice trials
            if trial_count <=len(practice_trials):
                if trial_count==1 and practice:#if this is one of the practice go trials 
                    practice_go_inst.draw()
                    trial_label='practice'
                    win.flip()
                    waitSwitch()
                    #event.waitKeys()
                elif taskInfo_brief['n practice go trials']+1==trial_count and practice:#if this is a practice stop trialClock
                    practice_stop_inst.draw()
                    trial_label='practice'
                    win.flip()
                    waitSwitch()
                    #event.waitKeys()
            elif trial_count==taskInfo_brief['n practice go trials']+taskInfo_brief['n practice stop trials']+1 and practice:#if this is the start of the main trials, ask them if they understand before commencing 
                understand.draw()
                trials=trials_no_prac
                trial_count=1
                win.flip()
                waitSwitch()
                #event.waitKeys()
                practice=False #this variable tells us we don't want a practice any more
                trial_label='main'
                
                #reset the stop pos to be what it should be at the start
                stoppos=fullvert[1][1]
        else:
            trial_label='main'
        #staircase the position of the StopS based on if they were correct on the last StopS
        if not hardwareInfo['Import trial info file']:
            if correct == -1 and (stoptime>stoplimit_adjusted-frame_dur and stoptime<=stoplimit_adjusted):
                stoptime=stoplimit_adjusted 
            elif correct==-1 and stoptime>stoplimit_adjusted:#if they incorrectly lifted on a StopS trial (checking success count allows us to check if the trial restarted)
                if stoptime+stepsize_adjusted > taskInfo_brief['Lower limit (ms)']:
                    print('lower limit reached')
                else:
                    # print('stoptime',stoptime)
                    print('LOWER LIMIT', stoptime+stepsize_adjusted)
                    stoptime=stoptime+stepsize_adjusted
                    if block_type == 0:
                        NT_stop = stoptime
                    else:
                        T_stop  = stoptime  
            elif correct ==2:#if they correctly stopped on the StopS trial
                # IF stop was correct it decreases the target - stop trial stop position, evaluate a threshold. 
                if stoptime-stepsize_adjusted < taskInfo_brief['Stop limit (ms)']:
                    print ('Threshold reached :D')
                else:
                    # print('stoptime',stoptime)
                    print('UPPER LIMIT', stoptime-stepsize_adjusted)
                    stoptime=stoptime-stepsize_adjusted
                    if block_type == 0:
                        NT_stop = stoptime
                    else:
                        T_stop  = stoptime

        else:
            stoptime=stoptimes[count]#index the stop time from the preset file 
            #count=count+1
#        StopSpos=(Time_from_base_to_targetline-stoptime)*(taskInfo['rise velocity (cm/sec)']/1000)
#        StopSpos_adjusted=StopSpos-SSD_overshoot
#        StopSpos=StopSpos_adjusted
#        
#        #calculate where the SSD is in time relative to the base for the output file
#        StopSpos_time=(StopSpos/cm_per_frame)*frame_dur
#        
        
        
        #recalculating SSD over/undershoot - dynamically on each trial
        #time_from_base_to_SSD=((cm_to_move_to_targetline-StopSpos)/taskInfo['rise velocity (cm/sec)'])*1000
        StopSpos=(Time_from_base_to_targetline-stoptime)*(taskInfo['rise velocity (cm/sec)']/1000)
        time_from_base_to_SSD=(StopSpos/taskInfo['rise velocity (cm/sec)'])*1000
        frames_from_base_to_SSD = time_from_base_to_SSD/frame_dur
        SSD_overshoot = (math.ceil(frames_from_base_to_SSD)-frames_from_base_to_SSD)*cm_per_frame
        SSD_undershoot = (math.floor(frames_from_base_to_SSD)-frames_from_base_to_SSD)*cm_per_frame
        
        # print('StopSpos',StopSpos)
        # print('SSD_overshoot',SSD_overshoot)
        # print('SSD_undershoot', SSD_undershoot)
        
        
        #the overshoot or undershoot may be closer to the actual desired bar height, lets check which is closer and use this.
        if SSD_overshoot< abs(SSD_undershoot):#if the overshoot is smaller than the undershoot, use the overshoot
            SSD_optimal_difference=SSD_overshoot
        else:#if the undershoot is smaller than the overshoot, use the undershoot
            SSD_optimal_difference=SSD_undershoot
        #StopSpos_adjusted=StopSpos-SSD_optimal_difference
        StopSpos_adjusted=StopSpos+SSD_optimal_difference
        StopSpos=StopSpos_adjusted
#        
#        #calculate where the SSD is in time relative to the base for the output file
        StopSpos_time=(StopSpos/cm_per_frame)*frame_dur
        
        #reset correct 
        correct=[]
        
        #set the stop position based on if this is a go or StopS trial
        if trial==1:
            stoppos=fullvert[1][1]
        else:
            # stoppos= (0-taskInfo['Bar base below fixation (cm)'])+int(StopSpos)
            stoppos= (0-taskInfo['Bar base below fixation (cm)'])+StopSpos
        print('Position in CM for stop trial',stoppos)
        
        #present the instructions to press and hold the key to start the trial
        PressKey_instructions.draw()
        win.flip()
        waitSwitch()
        #k = event.waitKeys()
        #if k[0]=='escape':
            #print('User pressed escape, quiting now')
            #win.close()
            #core.quit()
        #reset the vertices to their begining position
        vert[1]=(vert[1][0], vert[1][1]-inc)
        vert[2]=(vert[2][0], vert[2][1]-inc)
        fillBar.vertices = vert   
        #If we have a spaceship - draw it here 
        if expInfo['Spaceship']:
           # Spaceship.pos=(0, vert[2][1]-(Spaceship_height_cm/2))
            Spaceship.pos=(0, vert[2][1])
        #Count down before trial starts
        # if taskInfo_brief['Count down']:                      
        countdown()
        if block_type == 1:
            Threatfeed.setAutoDraw(True)
        else:
            Threatfeed.setAutoDraw(False)  
        trialClock.reset()#reset the clock as the bar has started filling 
        win.frameIntervals=[]
        win.recordFrameIntervals = True
        waiting=1  
        inc=0
        safer = 0 
        print('here')
        ser.reset_input_buffer()
        while vert[1][1]<fullvert[1][1] and waiting==1:#whilst we are waiting for the button to be lifted OR for the trial to reach its max time limit (i.e the time it would have taken the bar to reach the top)
            line = ser.readline()
            print('Signal from arduino',line)
            if 0 <= safer <= 5:
                line = '---'
                safer +=1
                print('safer',safer)
            if len(line)>0:  #keyboard[key.SPACE]:
                #Draw the background bar
                Bar.setAutoDraw(True)##change to "background bar"
                inc=inc+increase
                # Draw warning if block type = Threat [1]
                if block_type == 1:
                    Threatfeed.setAutoDraw(True)
                else:
                    Threatfeed.setAutoDraw(False)
                #Set the vertices of the filling bar 
                vert[1]=(vert[1][0], vert[1][1]+increase)
                vert[2]=(vert[2][0], vert[2][1]+increase)
                #but only actually carry on filling if its not a StopS trial
                # print('Vert config',vert)
                # print('Vert Stop condition', vert[1][1])
                # print('where to stop',stoppos)
                if trial==1 or (trial==0 and vert[1][1]<stoppos):
                    fillBar.vertices = vert
                    if expInfo['Spaceship']:
                        print(increase)
                       # Spaceship.pos=(0, vert[2][1]-(Spaceship_height_cm/2))
                        Spaceship.pos=(0, vert[2][1])
                fillBar.setAutoDraw(True) 
                if expInfo['Spaceship']:
                    Spaceship.setAutoDraw(True)
                
                #make sure the target line is drawn over the bar
                targetLine.setAutoDraw(True)
                win.flip()
                distance=np.abs(vert[1][1]-Target_pos_adjusted)
                distance_ms=distance/(cm_per_frame/frame_dur)
                distance_from_base=np.abs(vert[0][1]-vert[1][1])
                distance_from_base_ms=distance_from_base/(cm_per_frame/frame_dur)
            else:
                print('Finger Lifted')
                waiting=0 #say we are not waiting anymore and break the loop 
        win.recordFrameIntervals = False #stop recording the frame intervals
        #the actual velocity is the distance traveled (i.e. the number of frames * the cm per frame)/the total time (i.e. the sum of the duration of the frames)
        actual_trial_velocity=(len(win.frameIntervals)*cm_per_frame)/sum(win.frameIntervals)
        # print('Actual trial velocity was %.3f'%(actual_trial_velocity))
        if waiting==1:#give feedback that they incorrectly stopped
            lifted = 0
            success = 0
            RT='NaN'
            if trial==1:
                if block_type ==1:
                    ser.write([1])
                    print('FEEDBACK SHOCK')
                feedback=incorrectstop
                targetLine.fillColor='Red'
                correct=-2
                print('Trial time was %s'%(trialClock.getTime()))
            elif trial==0:#give feedback that they correctly stopped
                success = 1
                correct=2
                targetLine.fillColor='Green'
                feedback=correctstop
                correct_StopSs=correct_StopSs+1
                print('Trial time was %s'%(trialClock.getTime()))
        else:
            lifted=1
            RT=trialClock.getTime()
            if trial==1:#give feedback they correctly lifted and give distance/time from target
                correct=1
                if distance_ms > 100:
                    success = 0
                    targetLine.fillColor='Red'
                    correctgo = visual.TextStim(win, pos=[feedback_dist, 0], height=1, color=[1,1,1],
                        # text="%.2f cm\n%.0f ms from target! Try to be more accurate next time!"%(distance, distance_ms), units='cm')
                        text="%.0f ms from target! Try to be more accurate next time!"%(distance_ms), units='cm')
                    if block_type == 1:
                        ser.write([1])
                        print('FEEDBACK SHOCK')
                else:
                    targetLine.fillColor='Green'
                    success = 1 
                    correctgo = visual.TextStim(win, pos=[feedback_dist, 0], height=1, color=[1,1,1],
                        # text="%.2f cm\n%.0f ms from target!"%(distance, distance_ms), units='cm')
                        text="%.0f ms from target!"%(distance_ms), units='cm')
                if trial_label=="main":#only add to the feedback if this is a main trial (i.e. dont count the practice trials)
                    correct_go_distances.append(distance)
                    correct_go_distances_ms.append(distance_ms)
                    correct_gos=correct_gos+1
                feedback=correctgo
                print('Trial time was %s'%(trialClock.getTime()))
            elif trial==0:#give feedback they incorrectly lifted -- and this is an unsuccessfull trial, so the trial should restart (it will be noted in the output that the trial restarted)
                success = 0
                if block_type ==1:
                    ser.write([1])
                    print('FEEDBACK SHOCK')
                feedback=incorrectgo
                targetLine.fillColor='Red'
                correct=-1
                print('Trial time was %s'%(trialClock.getTime()))
        if taskInfo_brief['Trial by trial feedback']:
            feedback.setAutoDraw(True)
        win.flip()
        with open(Output+'.txt', 'a') as b:
            #b.write('%s	%s	%s	%s	%s	%s	%s\n'%(block_count, trial_label, trial_count, trial, lifted, RT, StopSpos_time))
            b.write('%s	%s	%s	%s	%s	%s %s %s %s\n'%(block_type, block_count, trial_label, trial_count, trial, lifted, success, RT, StopSpos_time))
        with open(log_filename+'.txt', 'a') as b:
            b.write('\n\n %s %s 	%s	%s	%.3f'%(block_type, block_count, trial_label, trial_count, actual_trial_velocity))
        core.wait(2)
        
        #wipe the message
        feedback.setAutoDraw(False)
        
        #Wipe the last image from the screen
        targetLine.setAutoDraw(False)
        fillBar.setAutoDraw(False) 
        Bar.setAutoDraw(False)
        if expInfo['Spaceship']:
            Spaceship.setAutoDraw(False)
        count=count+1#only add to the trial could if we have been successfull
    #Write a nice thank-you message and some feedback on performance
    EndMessage = visual.TextStim(win, pos=[0, 0], height=.1, color=[1,1,1],
        text="The End!\n\nAverage distance from target: %.3f\n\nAverage time from target: %.3f\n\nCorrect Go: %s out of %s\n\nCorrect Stop: %s out of %s"%(
        np.average(correct_go_distances), np.average(correct_go_distances_ms), correct_gos, taskInfo_brief['n_go_trials (per block)']*taskInfo_brief['n blocks'], correct_StopSs, taskInfo_brief['n_stop_trials (per block)']*taskInfo_brief['n blocks']))
    
EndMessage.draw()
Threatfeed.setAutoDraw(False)
win.flip()
while True:  
    keys = event.getKeys()
    if keys:
        # q quits the experiment
        if keys[0] == 'q':
            ser.close()
            win.close()
            core.quit()

import psychopy as psy
from psychopy import sound, gui, visual, core, data, event,monitors
import numpy as np  # whole numpy lib is available, prepend 'np.'
import os  # handy system and path functions
import sys  # to get file system encoding
import serial  #connecting to the serial port (Arduino)
import math
import copy
import random
from datetime import datetime


class Participant:
    def __init__(self, expInfo):
        self.expInfo = expInfo

    def collect_info(self):
        dlg = gui.DlgFromDict(dictionary=self.expInfo, title='Participant Information', tip=None)
        if dlg.OK == False:
            core.quit()
        self.expInfo['date'] = data.getDateStr()

class Experiment(object):
    def __init__(self):
        psy.prefs.hardware['audioLib'] = ['PTB', 'pyo', 'pygame']
        self.arduino = None
        self.expInfo = None
        self.taskInfo_brief = None
        self.trials = []
        self.block_count = -1
        self.init_arduino()
        self.get_exp_info()
        self.get_task_info()
        self.setup_window()
        self.setup_stimuli()
    
    def init_arduino(self):
        self.arduino = serial.Serial('COM6', 9600, timeout=0.1)

    def get_exp_info(self):
        self.expInfo = {'Participant code': 0000, 'Age (Years)': 00, 
                   'Gender': ['M', 'F', 'Other'], 
                   'Would you like to run this task using its default parameters?': True}
        dlg = gui.DlgFromDict(dictionary=self.expInfo, title='Participant Information', tip=None)
        if dlg.OK == False:
            self.arduino.close()
            core.quit()
        self.expInfo = self.expInfo

    def get_task_info(self):
        # 4 types of trials
        taskInfo_brief = {'GoTrials (per block)': 4, 
                        'GKTrials': 4,'GFITrials': 4,'DeTrials': 4, 'n blocks': 2,
                        'Full Screen': True,
                        'Pressure':True,
                        'Time_1(ms)':1000,'Time_2(ms)':1100, 'Time_3(ms)':1200, 'Time_4(ms)':1300}
        dlg = gui.DlgFromDict(dictionary= taskInfo_brief, title='Experiment Setup', tip=None)
        self.taskInfo_brief = taskInfo_brief
        if dlg.OK == False:
            print('Closing port and exit')
            self.arduino.close()
            core.quit()
        self.expInfo['date'] = data.getDateStr()
        #dlg.Destroy()
    
    def setup_window(self):
        self.win = visual.Window(
            size= [1920, 1080],
            fullscr = self.taskInfo_brief['Full Screen'],
            winType='pyglet',
            monitor='testMonitor',
            screen=1,
            # monitor = 'Wired Display',
            color=[-1, -1, -1], colorSpace='rgb',
            # blendMode='avg', mouseVisible = False, allowGUI=False)
            blendMode='avg', allowGUI=False)

    def setup_stimuli(self):
        self.StartImage = visual.ImageStim(self.win, image='Images'+os.sep+'Start.jpg')
        self.TargetR    = visual.ImageStim(self.win, image='Images'+os.sep+'Go_right.jpg')
        self.TargetL    = visual.ImageStim(self.win, image='Images'+os.sep+'Go_left.jpg')
        self.DefR       = visual.ImageStim(self.win, image='Images'+os.sep+'Defence_right.jpg')
        self.DefL       = visual.ImageStim(self.win, image='Images'+os.sep+'Defence_left.jpg')
        self.GkIgR      = visual.ImageStim(self.win, image='Images'+os.sep+'Goalkeeper_ignore_right.jpg')
        self.GkIgL      = visual.ImageStim(self.win, image='Images'+os.sep+'Goalkeeper_ignore_left.jpg')
        self.GkR        = visual.ImageStim(self.win, image='Images'+os.sep+'Goalkeeper_right.jpg')
        self.GkL        = visual.ImageStim(self.win, image='Images'+os.sep+'Goalkeeper_left.jpg')
        self.instr      = visual.ImageStim(self.win, image='Images'+os.sep+'Instructions.jpg')

    def run(self):
        for block in range(self.taskInfo_brief['n blocks']):
            self.block_count += 1
            trial_block = TrialBlock(block, self)
            trial_block.run_block()

class TrialBlock:
    def __init__(self, block_number, experiment):
        self.block_number = block_number
        self.experiment = experiment
        self.generate_trials_and_sides()

    def generate_trials_and_sides(self):
        # Trial type
        trials = [0]*self.experiment.taskInfo_brief['GoTrials (per block)'] + \
                 [1]*self.experiment.taskInfo_brief['GKTrials'] + \
                 [2]*self.experiment.taskInfo_brief['GFITrials'] + \
                 [3]*self.experiment.taskInfo_brief['DeTrials']
        # Side of stim
        side = [0]*int(math.ceil(len(trials)/2)) + [1]*int(math.floor(len(trials)/2))
        # Times
        time_delays = [self.experiment.taskInfo_brief['Time_1(ms)'],
                   self.experiment.taskInfo_brief['Time_2(ms)'],
                   self.experiment.taskInfo_brief['Time_3(ms)'],
                   self.experiment.taskInfo_brief['Time_4(ms)']]
        random_time_delays = [random.choice(time_delays) for _ in range(len(trials))]
        
        #Randomize
        np.random.shuffle(trials)
        np.random.shuffle(side)
        np.random.shuffle(random_time_delays)
        
        self.trials = trials
        self.sides = side 
        self.times = random_time_delays

    def run_block(self):
        for k in range(len(self.trials)):
            trial = Trial(k, self)
            print ('Block #', self.experiment.block_count, 'Trial #', k)
            trial.run_trial()

class Trial:
    def __init__(self, trial_number, trial_block):
        self.trial_number = trial_number
        self.trial_block = trial_block
        self.trialClock = core.Clock()
        self.results = {
            'Pressure': None,
            'block_count': None,
            'trial_count': None,
            'trial_type': None,
            'Cue': None,
            'RT': None,
            'MT': None,
            'success': None
        }
    
    def waitSwitch(self):
        #self.trial_block.experiment.PressSW.draw()
        self.trial_block.experiment.win.flip()
        line = self.trial_block.experiment.arduino.readline()
        print('Waiting for switch!!')
        while True:
            line = self.trial_block.experiment.arduino.readline().decode('UTF-8')
            if line:
                if line[0] == "B":
                    print('Start clock')
                    return

    def waitRelease(self):
        while True:
            line = self.trial_block.experiment.arduino.readline().decode('UTF-8')
            if line[0] == "A":
                RT = self.trialClock.getTime()
                print('Reaction time = ', RT)
                return RT

    def waitGate(self):
        gatecount = 0
        while True:
            line = self.trial_block.experiment.arduino.readline().decode('UTF-8')
            if line[1] == "D":  # if kicked
                MT = self.trialClock.getTime()
                return MT
            elif line[1] == "C":  # if not
                gatecount += 1
                if gatecount > 1500:
                    return 0

    def run_trial(self):
        self.trial_type = self.trial_block.trials[self.trial_number]
        self.side = self.trial_block.sides[self.trial_number]
        self.timing = self.trial_block.times[self.trial_number]

        while True:
            # Initialize Results
            self.results['trial_type'] = self.trial_type
            self.results['block_count'] = self.trial_block.block_number
            self.results['trial_count'] = self.trial_number
            self.results['Pressure'] = self.trial_block.experiment.taskInfo_brief['Pressure']
            self.results['TrialNumber'] = self.trial_number
            
            # Instructions screen 
            print('Draw instructions')
            self.trial_block.experiment.instr.draw()
            
            
            # Draw the goalkeeper
            self.waitSwitch()
            self.trial_block.experiment.StartImage.draw()
            self.trial_block.experiment.win.flip()

            # randome pause stimulus by first defining the task. 
            core.wait(random.uniform(3,7))

            if self.side == 1:
                self.trial_block.experiment.TargetR.draw()
                self.trial_block.experiment.win.flip() #Show the stimulus either at left or right.
            else:
                self.trial_block.experiment.TargetL.draw()
                self.trial_block.experiment.win.flip() #Show the stimulus either at left or right.

            # Reset th clock once the stimulus is displayed
            self.trialClock.reset()
            
            #Get the reaction time
            self.RT = self.waitRelease()

            #Repeat the task if necessary
            if self.RT >= 1:
                print('RT Restart Trial')
                continue
            else:
                print('RT Good Trial')

            self.results['RT'] = self.RT
            
            # Reset clock for MT 
            self.trialClock.reset()
            
            # Run Logic according to trial type.
            # Missing the MT and succes classification 
            print ('Trial Type = ', self.trial_type)
            if self.trial_type == 0:
                self.run_go_trial()
                self.MT = self.waitGate()
            elif self.trial_type == 1:
                self.MT, self.succes = self.run_gk_trial()
            elif self.trial_type == 2:
                 self.MT, self.succes = self.run_gfi_trial()
            elif self.trial_type == 3:
                 self.MT, self.succes = self.run_de_trial()
            
            print ('MT is = ', self.MT)
            if self.MT >= 2:
                print('MT restart Trial')
                continue
            else:
                print('MT Good trial')

            self.results['MT'] = self.MT

            # Save Results
            self.save_results()
            return

    def run_go_trial(self):
        while True:
            timer = self.trialClock.getTime()
            if timer*1000 >= 0.1:
                return

    def run_gk_trial(self):
        # Logic for GK Trial
        while True:
                timer = self.trialClock.getTime()
                #print ('stop',timer)
                if timer *1000 >= self.timing: #Assign the time in time.
                    if self.side == 1:
                        self.trial_block.experiment.GkR.draw()
                    else:
                        self.trial_block.experiment.GkL.draw()
                    self.trial_block.experiment.win.flip()
                    MT = self.waitGate()
                    if MT != 0:
                        success = 0
                    else:
                        success = 1
                        MT = 0
                    self.results['MT'] = MT
                    self.results['success'] = success
                    return(MT, success)

    def run_gfi_trial(self):
        ## Logic for GK Trial
        while True:
                timer = self.trialClock.getTime()
                #print ('stop',timer)
                if timer *1000 >= self.timing: #Assign the time in time.
                    if self.side == 1:
                       self.trial_block.experiment.GkIgR.draw() 
                    else:
                        self.trial_block.experiment.GkIgL.draw()
                    self.trial_block.experiment.win.flip()
                    MT = self.waitGate()

                    if MT != 0:
                        success = 0
                    else:
                        success = 1
                        MT = 0
                    self.results['MT'] = MT
                    self.results['success'] = success
                    return(MT, success)

    def run_de_trial(self):
        # Logic for Defense Trial
        while True:
                timer = self.trialClock.getTime()
                if timer *1000 >= self.timing: #Assign the time in time.
                    if self.side == 1:
                        self.trial_block.experiment.DefR.draw()
                    else:
                        self.trial_block.experiment.DefL.draw()
                    self.trial_block.experiment.win.flip()
                    MT = self.waitGate()
                    if MT != 0:
                        success = 0
                    else:
                        success = 1
                        MT = 0
                    self.results['MT'] = MT
                    self.results['success'] = success
                    return(MT, success)

    def collect_RT_data(self):
        self.trialClock.reset()  # Reset the clock
        while True:
            line = self.trial_block.experiment.arduino.readline().decode('UTF-8')
            if line[0] == "A":
                RT = self.trialClock.getTime()
                if RT >= 1:
                    continue  # Restart the trial if needed
                else:
                    return RT  # Return the collected RT
    
    def collect_MT_data(self):
        self.trialClock.reset()  # Reset the clock
        gatecount = 0
        while True:
            line = self.trial_block.experiment.arduino.readline().decode('UTF-8')
            if line[1] == "D":  # if kicked
                MT = self.trialClock.getTime()
                return MT
            elif line[1] == "C":  # if not
                gatecount += 1
                if gatecount > 1500:
                    return 0  # No Gate input, next trial

    def save_results(self):
        Subject = self.trial_block.experiment.expInfo['Participant code']
        current_day = datetime.now().day
        filename = "ID_{}_Day_{}.txt".format(Subject, current_day)
        #Save
        with open(filename, 'a') as b:
            b.write('{Pressure} {block_count} {TrialNumber} {trial_type} {RT} {MT}\n'.format(**self.results))

if __name__ == "__main__":
    experiment = Experiment()
    experiment.run()
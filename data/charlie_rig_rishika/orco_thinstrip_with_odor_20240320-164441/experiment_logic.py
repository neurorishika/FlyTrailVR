# Experiment by Rishika Mohanta
# Design started on: Mar 18 2024

# Goal:
# To test whether flies can perform rudimentary trail tracking like behavior in an OdorVR in the Ruta lab.

# Background:
# In the presense of a strong upwind cue, flies reliable track the edge of an odor strip (~60%) of the time. 
# However, my hypothesis is that the flies are likely using the same logic even in the absence of wind. 
# Here the wind is a compass cue and a symmetry breaking stimulus. In essence, this is local search behavior,
# but along a line.


## IMPORTS ##
import numpy as np
from cl.utilities import SlidingWindow, FTData, InstantReplayParse
import cl.config as cfg
from time import sleep
from collections import deque

# SETUP THE INITIAL CONDITIONS

pre = True # TRUE if the experiment is in the pre-air phase, FALSE otherwise
live = True # TRUE if the experiment is in the live mode, FALSE if it is in the replay mode
irp_parsed = False # this should always start as False
time_stamp = True 
switch_direction = True
pulse = False
time_1 = 0

# Get replay file from template filling
log_dir = cfg.log_dir

# Parse times and playback deques
irp = InstantReplayParse(log_dir)
# irp.parse()

log_vals = {}
def experiment_logic(time, sw, ft):
    global pre, x0, y0, t0, live, log_vals, irp_parsed, switch_direction, pulse, time_stamp, time_1

    print(f'\nT={time:.1f}',end=' (')

    ## CHECK MODE (LIVE OR REPLAY)
    if live:
        print('LIVE', end=') ')

        # if before pre-onset time
        if time < cfg.pre_onset_time and pre:
            print('Pre-Onset', end=' ')
            air_sp = cfg.flowrate/1000.
            odor1_sp, odor2_sp, led1_sp, led2_sp = 0.0, 0.0, 1.0, 0.0
            pre = True
            log_vals['instrip'] = False
            log_vals['adapted_center'] = np.nan
            log_vals['strip_thresh'] = np.nan
        
        # if after pre-onset time for the first time
        elif time > cfg.pre_onset_time and pre:
            print('Onset', end=' ')
            air_sp = cfg.flowrate/1000.
            odor1_sp, odor2_sp, led1_sp, led2_sp = 0.0, 0.0, 1.0, 0.0
            log_vals['instrip'] = False
            log_vals['adapted_center'] = np.nan
            log_vals['strip_thresh'] = np.nan
            pre = False # set pre to False so that this block doesn't run again
            x0 = ft.posx
            y0 = ft.posy
            t0 = time

        # if after pre-onset time
        else:
            print(f'Running | Currently {"in odor" if log_vals["instrip"] else "outside"}')

            # get the current position of the fly and the time since the onset of the experiment
            x_temp = ft.posx - x0
            y_temp = ft.posy - y0
            t_temp = time - t0

            # adjust x_temp for periodic boundary conditions
            if cfg.periodic_boundary:
                boundary = cfg.period_width/2
                x_temp = (x_temp + boundary) % cfg.period_width - boundary
            
            # calculate the adapted center and the strip threshold according to the strip angle and direction
            if cfg.strip_direction=="left":
                adapted_center = -1*(y_temp*(np.tan(np.deg2rad(cfg.strip_angle))))
            if cfg.strip_direction=="right":
                adapted_center = y_temp*(np.tan(np.deg2rad(cfg.strip_angle)))

            strip_thresh = (cfg.strip_width/2)/np.sin(np.deg2rad(90-cfg.strip_angle))

            # out of the strip
            if np.abs(x_temp - adapted_center) > strip_thresh:
                log_vals['instrip'] = False
                air_sp = float(cfg.flowrate/1000.)
                odor1_sp, odor2_sp, led1_sp, led2_sp = 0.0, 0.0, 1.0, 0.0
                
                    
            # in the strip and not at the absolute edge
            elif y_temp > -100000 and y_temp < 100000:
                log_vals['instrip'] = True
                odor1_sp = (cfg.flowrate/1000.)*(cfg.percent_odor/100)
                controller_max = float(cfg.flowrate/1000.)
                air_sp = controller_max - odor1_sp
                odor2_sp = 0.0
                led1_sp, led2_sp = 0.0, 0.0
                log_vals['adapted_center'] = adapted_center
                log_vals['strip_thresh'] = strip_thresh

            # at the absolute edge, reset the onset time and the position
            else: 
                air_sp = cfg.flowrate/1000.
                odor1_sp, odor2_sp, led1_sp, led2_sp = 0.0, 0.0, 1.0, 0.0
                pre = True
                log_vals['instrip'] = False
                log_vals['adapted_center'] = np.nan
                log_vals['strip_thresh'] = np.nan

            print(f'Exp. Time: {t_temp:.1f} | X: {x_temp:.1f} | Y: {y_temp:.1f} | Odor : {"ON" if log_vals["instrip"] else "OFF"}', end=' ')

    ## REPLAY PORTION
    else:
        print('REPLAY')
        ####### TRANSITION (once) #######
        if not irp_parsed:
            if cfg.include_pre_air:
                irp.parse()
            else:
                irp.parse_from_time(cfg.pre_onset_time)
            irp_parsed=True

        try:
            next_time = irp.times[0]
        except IndexError:
            next_time = -1

        # start the replay

        if time > next_time - 0.05 and time < next_time + 0.05:
            print('A')
            _ = irp.times.popleft()
            sp = irp.playback.popleft()
            air_sp, odor1_sp, odor2_sp = sp[0], sp[1], sp[2]

        elif time < next_time - 0.05:
            print('B')
            sleep(next_time-time)
            _ = irp.times.popleft()
            sp = irp.playback.popleft()
            air_sp, odor1_sp, odor2_sp = sp[0], sp[1], sp[2]

        elif next_time>0:
            print('C')
            while time - next_time > 0.05:
                print("C-WHILE")
                _ = irp.times.popleft()
                _ = irp.playback.popleft()
                next_time = irp.times[0]
            _ = irp.times.popleft()
            sp = irp.playback.popleft()
            air_sp, odor1_sp, odor2_sp = sp[0], sp[1], sp[2]

        else:
            air_sp, odor1_sp, odor2_sp = 0.0, 0.0, 0.0
            print('END OF REPLAY')
            live = True
            pre  = True

        led1_sp, led2_sp = 0.0, 0.0


    #pass the mode through the log_vals.
    # Note that the last frame of the live experiment should be 'replay' (TODO: change this)
    if live:
        log_vals['mode'] = 'live'
    else:
        log_vals['mode'] = 'replay'
    # DONT ADD ANYTHING (BESIDES RETURN) BELOW THIS LINE

    return air_sp, odor1_sp, odor2_sp, led1_sp, led2_sp, log_vals

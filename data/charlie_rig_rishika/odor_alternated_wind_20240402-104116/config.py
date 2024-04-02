########### INSTANT REPLAY CONFIG ############
instant_replay = False #this just tells Run.run() to treat this differently.
include_pre_air = True # Set to TRUE for baseline clean air before live and replay, set to false for clean air only before live

##############################################
# specify the log directory exactly as you entered on the command line.
# Don't forget to change this if you need to!
log_dir = '/home/rutalab/Desktop/log_files/'

##############################################
# ODOR PROPERTIES

strip_angle = 0 # in degrees cannot be 90
strip_direction = "right" # "left" or "right"
strip_width = 10 # in mm
periodic_boundary = True # True or False
period_width = 200 # in mm

flowrate = 300 # in standard ml/min
flowrate_high = 300 # in standard ml/min
flowrate_low = 20 # in standard ml/min
alternation_time = 120 # in seconds

percent_odor = 20 # in percent
pre_onset_time = 60 # in seconds

##############################################
led_intensity = 0 # in percent
led_color = "red"
window_len = 120 # for computing sliding window values
pulse_period = 10.0 # period for hardware pulse

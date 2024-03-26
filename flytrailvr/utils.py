# Description: Utility functions for the flytrailvr package

import os
import pandas as pd

def extract_data(folder):
    '''
    Extract data from a folder.

    The folder should contain a log file, a config file, a experiment_logic file and a comments file.
    '''

    # find log file in folder
    log_file = list(filter(lambda x: x.endswith('.log'), os.listdir(folder)))
    assert len(log_file) == 1, 'More than one log file found'
    log_file = log_file[0]

    # read log file line by line
    with open(os.path.join(folder, log_file), 'r') as f:
        lines = f.readlines()
    
    # function to extract variables
    def vars(line):
        return line.strip().replace(' -- ', ',').split(',')

    # get columns and data
    columns = vars(lines[0])
    data = [vars(line) for line in lines[1:]]

    # create dataframe
    df = pd.DataFrame(data, columns=columns)
    df = df.apply(pd.to_numeric, errors='ignore')

    # convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m/%d/%Y-%H:%M:%S.%f')

    # convert instrip to boolean
    df['instrip'] = df['instrip'].astype(bool)

    # see if a config file exists
    config_file = list(filter(lambda x: x=='config.py', os.listdir(folder)))
    assert len(config_file) <= 1, 'More than one config file found'

    if len(config_file) == 1:
        with open(os.path.join(folder, config_file[0]), 'r') as f:
            lines = f.readlines()

        config = {}
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            key, value = line.strip().split('=')

            # clean up key and value
            key = key.strip()
            value = value.replace('"', "'").split('#')[0].strip()

            config[key] = value.replace("'","") if value.startswith("'") else eval(value)
    else:
        config = None

    # see if a experiment_logic file exists, if so, keep it as a string
    logic_file = list(filter(lambda x: x.endswith('.experiment_logic'), os.listdir(folder)))
    assert len(logic_file) <= 1, 'More than one experiment_logic file found'

    if len(logic_file) == 1:
        with open(os.path.join(folder, logic_file[0]), 'r') as f:
            lines = f.readlines()

        logic = '\n'.join(lines)
    else:
        logic = None

    # get the additional comments
    comments_names = ['additional_comments.txt', 'metadata.txt']
    comments_file = list(filter(lambda x: x in comments_names, os.listdir(folder)))
    assert len(comments_file) <= 1, 'More than one comments file found'

    if len(comments_file) == 1:
        with open(os.path.join(folder, comments_file[0]), 'r') as f:
            comments = f.readlines()
        # if there is a single line its the comments, else make a dictionary
        if len(comments) == 1:
            comments = {'comments': comments[0].strip()}
        else:
            comments = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in comments}
    else:
        comments = None

    return df, config, logic, comments


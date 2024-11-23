# Description: Utility functions for the flytrailvr package

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

def process_important_variables(df, config):
    """
    Process important variables from the data file
    
    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe containing the data
    config : dict
        Dictionary containing the config information
        
    Returns
    -------
    var_dict : dict
        Dictionary containing the important variables:
        - t : time
        - x : x position
        - y : y position
        - heading : heading
        - odor : odor
        - flowrate : flowrate
        - led : led
        - strip_width : strip width
        - periodic_boundary : periodic boundary
        - period_width : period width
    """
    t = (df['timestamp']-df['timestamp'].iloc[0]).dt.total_seconds()
    pre_duration = float(config['pre_onset_time'])
    t0 = t[t > pre_duration].iloc[0]
    x0 = df['ft_posx'][t > pre_duration].iloc[0]
    y0 = df['ft_posy'][t > pre_duration].iloc[0]

    x = (df['ft_posx']-x0) / 1000
    y = (df['ft_posy']-y0) / 1000
    t = t-t0
    heading = df['ft_heading']*180/np.pi

    flowrate = df['mfc2_stpt'].values + df['mfc1_stpt'].values

    odor = df['mfc2_stpt'].values
    odor = (odor - odor.min()) / (odor.max() - odor.min())

    led = 1-df['led1_stpt'].values

    # create a dictionary of the variables
    var_dict = {
        't': t,
        'x': x,
        'y': y,
        'heading': heading,
        'odor': odor,
        'flowrate': flowrate,
        'led': led,
    }

    return var_dict

def config_to_title(
        config,
        prefix='',
        suffix='',
        include=['flowrate', 'strip_width']
        ):
        # create a title from the config file
        assert np.all([x in config.keys() for x in include]), 'include variables not in config'
        title = prefix
        for key in include:
            title += f'{key}={config[key]} '
        title += suffix
        return title

def plot_trajectory(
        df,
        config,
        scale_factor=1,
        show=True,
        save=None,
        config_title=True,
        colormaps=[],
        odor_or_led='odor',
        black_background=False
):
    # process the important variables
    processed_data = process_important_variables(df, config)
    t = processed_data['t']
    x = processed_data['x']
    y = processed_data['y']
    odor = processed_data['odor']
    led = processed_data['led']
    colorvar = odor if odor_or_led == 'odor' else led
    flowrate = processed_data['flowrate']

    unique_flow_rates = np.unique(flowrate)
    # sort the unique flow rates
    unique_flow_rates = np.sort(unique_flow_rates)
    assert unique_flow_rates.size <= len(colormaps), 'Number of colormaps should be less than equal to the number of unique flowrates'

    # set the figure size
    xby = (x.max()-x.min())/(y.max()-y.min())
    fig, ax = plt.subplots(figsize=(xby*scale_factor+1, 1*scale_factor))
    if black_background:
        # make the background black
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['right'].set_color('white')
        # set the ticks to white
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        # set the labels to white
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        # set the title to white
        ax.title.set_color('white')
    
    
    # plot the trajectory (different colors for different flow rates)
    for i, flow_rate in enumerate(unique_flow_rates):
        idx = flowrate == flow_rate
        ax.scatter(x[idx], y[idx], c=colorvar[idx], cmap=colormaps[i], s=0.5)


    # mark the start
    ax.plot(x[0], y[0], '*', color='black', markersize=10)
    ax.text(x[0], y[0], '  start', fontsize=10, color='black')


    # add the odor lines
    if config['periodic_boundary']:
        period_width = config['period_width']/1000
        strip_width = config['strip_width']/1000
        max_x = int(x.max()//period_width)
        min_x = int(x.min()//period_width)
        for i in range(min_x, max_x+1, 1):
            start_x = i*period_width-strip_width/2
            end_x = i*period_width+strip_width/2
            ax.fill_betweenx([y.min(), y.max()], start_x, end_x, color='grey', alpha=0.2)
    else:
        strip_width = config['strip_width']/1000
        ax.fill_betweenx([y.min(), y.max()], -strip_width/2, strip_width/2, color='grey', alpha=0.2)
        
    # set axis properties
    ax.set_aspect('equal')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')

    if config_title:
        title = config_to_title(config)
        ax.set_title(title)
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout()


    if save is not None:
        if type(save) == str:
            plt.savefig(save, dpi=300)
        elif type(save) == list:
            for s in save:
                plt.savefig(s, dpi=300)
        else:
            raise ValueError('save should be a string or a list of strings')

    if show:
        plt.show()
    else:
        plt.close()

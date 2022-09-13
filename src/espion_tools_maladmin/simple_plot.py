#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import parse_espion_export
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import logging
import argparse
import os
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

defaults = [{'name': 'DA 0.01', 'desc': 'Dark-adapted 0.01 blink reduce', 'ylims': (-100,250)},
             {'name': 'DA 3.0', 'desc': 'Dark-adapted 3.0 ERG + OPs', 'ylims': (-300,150), 'xlims': (-20,75)},
             {'name': 'DA OPs', 'desc': 'Dark-adapted 3.0 ERG + OPs', 'type': 'ops', 'ylims': (-50,50), 'xlims': (-20,100)},
             {'name': 'LA 3.0', 'desc': 'Light-adapted 3.0 ERG', 'ylims': (-50,100), 'xlims': (-20,100)},
             {'name': '30Hz Flicker', 'desc': 'Light-adapted 3.0 flicker ERG', 'ylims': (-100,100), 'xlims': (-20,100)}]
             
             #,
             #{'name': 'On Response', 'desc': 'Rapid - On', 'ylims': (-100,100), 'xlims': (-20,200)},
             #{'name': 'Off Response', 'desc': 'Rapid - Off',  'ylims': (-100,100), 'xlims': (-20,200)}]
default_xlims = [-20, 100]
default_ylims = [-50, 50]     

def load_file(fname):
    data = parse_espion_export.load_file(fname)
    data = data[1]
    return data
    

def plot_steps(data, step_opts, outpath, eye):
    """
    Do the plotting
    data - list of step objects
    step_opts - list of xlims etc same length data
    """
    assert len(data) == len(step_opts)
    
    nsteps = len(step_opts)
    
    # set some plotting defaults
    sns.set_style('dark')
    sns.set_context('talk', font_scale=0.7)
    
    if args.plot_individual:
        for idx in range(nsteps):
            plot_individual(data[idx], step_opts[idx], eye, outpath)
    if args.plot_multiple:
        plot_multiple(data, step_opts, eye, outpath)
            
def plot_individual(data, step_opts, eye, outpath):
    fig = plt.figure()
    fig.set_size_inches(4,4)
    ax = fig.add_axes([0.25,0.2,0.7,0.7])
    plot_result(ax, data, step_opts, eye)
    ax.set_ylabel(r'Amplitude ($\mu$V)')
    ax.set_xlabel('Time (ms)')
    ax.get_xaxis().set_visible(True)
    ax.get_yaxis().set_visible(True)
        
    # plt.tight_layout()
    fname = outpath + '_{}_{}'.format(step_opts['name'], eye)
    #fname = slugify(fname)
    fname = fname + '.svg'
    fig.savefig(fname, format="svg")
    
def plot_multiple(data, step_opts, eye, outpath):
    nsteps = len(data)
    fig = plt.figure()
    axs=[]

    fig, ax = plt.subplots(2, nsteps)
    fig.set_size_inches(10,2)
    for idx in range(nsteps):
        ax = plt.subplot2grid((4, nsteps), (0, idx), rowspan=3)
        plot_result(ax, data[idx], step_opts[idx], eye)
        axs.append(ax)
    ax = plt.subplot2grid((4, nsteps), (3, 0), colspan=nsteps)
    ax.text(0.5,0.5,'Time (ms)',
            verticalalignment='center',
            horizontalalignment='center')    
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.axis('off')
    axs[0].set_ylabel(r'Amplitude ($\mu$V)' )
    plt.tight_layout(pad=0.2,w_pad=0)
    fname = outpath + '_multiple_{}'.format(eye)
    #fname = slugify(fname)
    fname = fname + '.svg'
    logger.info('saving to {}'.format(fname))
    fig.savefig(fname, format="svg")


    
def plot_result(ax, data, opts, eye):
    linetypes = ['solid', 'dashed', 'dashdot']
    colors = ['blue', 'green', 'red']
    
    if opts.get('is_op') == 'ops':
        if eye == 'od':
            channel = 3
        else: 
            channel = 4
    else:
        if eye == 'od':
           channel = 1
        else:
            channel = 2

    channel = data.channels[channel]
    result_keys = list(channel.results.keys())
    
    result_key = max(result_keys) # ensure we have the last result (the average)
    result = channel.results[result_key].data #time series object
    # generate the x value list
    endval = result.start + (len(result.values) - 1 * result.delta)
    xvals = np.linspace(start=result.start, stop=endval, num=len(result.values))

    yvals = [val / 1000 for val in result.values]

    
    ax.set_title(opts['name'])
    ax.set_ylim(opts['ylims'])
    ax.set_xlim(opts['xlims'])

    truncate = opts['truncate']
    
    result_count = 0 # fix this for plotting multiple results
    
    if truncate:
        # import pdb; pdb.set_trace()
        xvals_signal = xvals[xvals <= truncate]
        yvals_signal = yvals[xvals <= truncate]
        xvals_truncate = xvals[xvals > truncate]
        yvals_truncate = np.repeat(yvals_signal[-1], len(xvals_truncate))
        
        p = ax.plot(xvals_signal, yvals_signal, linestyle=linetypes[result_count], color=colors[result_count])
        p = ax.plot(xvals_truncate, yvals_truncate, linewidth=1, linestyle='dotted', color=colors[result_count])
    else:
        p = ax.plot(xvals, yvals, linestyle=linetypes[result_count], color=colors[result_count])
        
    result_count = result_count + 1
    return(p)


def get_steps(data):
    """Get the list of steps to process"""
    for k,v in data.items():
        print('{}, {}'.format(k, v.description))
    steps = input("Enter list of steps to process (comma seperated):")
    steps = steps.split(',')
    steps = [int(s.strip()) for s in steps]
    return steps


def get_default_steps(data):
    """Get the step keys corresponding to the default ISCEV steps"""
    steps = []
    for item in defaults:
        desc = item['desc']
        for k, v in data.items():
            if desc == v.description:
                steps.append([k, item.get('type', None)])

    return steps
            
def get_step_options(data, steps):
    """prompt user for additional plotting options"""
    def parse_lims(input_str):
        lims = input_str.split(',')
        lims = [int(i) for i in lims]
        return lims
    
    def find_default(desc, type):
        for d in defaults:
            if d['desc'] == desc and d.get('type', None) == type:
                return d
        return {}
            
    step_opts = []
    
    for step in steps:
        print('step:{}'.format(data[step[0]].description))

        step_data = data[step[0]]
        default = find_default(step_data.description, step[1])
        
        xlims = default.get('xlims', default_xlims)
        i = input('Xlims {}:'.format(xlims))
        if i: xlims = parse_lims(i)
            
        ylims = default.get('ylims', default_ylims)
        i = input('Ylims {}:'.format(ylims))
        if i: ylims = parse_lims(i) 
        
        name = default.get('name', step_data.description)
        i = input('Label {}:'.format(name))
        if i: name = i
        
        truncate = input('Trucate:')
        
        step_opts.append({'xlims': xlims,
                          'ylims': ylims,
                          'name': name,
                          'truncate': truncate,
                          'is_op': step[1]})
    return step_opts

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Plot traces from espion export files")
    parser.add_argument('-f', '--file', required=True, action='append' )
    parser.add_argument('-b', '--base', help="base path for input files, value is prefixed to paths specified by -f")
    parser.add_argument('-s', '--step', action='append', help='enter steps to print')
    parser.add_argument('--noprompt', help="Dont prompt for options. Use default settings or command line options", action='store_true')
    parser.add_argument('-d', '--defaults', help="Use default settings i.e. print ISCEV standard waves", action="store_true")
    parser.add_argument('--stepInfo', type=json.loads, action='append', help="Add a step to the default settings")
    parser.add_argument('-e' ,'--eye', help="od, os, both", default="both")
    parser.add_argument('-i', '--plot_individual', help="plot individual traces", action="store_true")
    parser.add_argument('-m', '--plot_multiple', help="plot all traces as a single figure", action="store_true")
    parser.add_argument('-o', '--output', help="base name for output figures")
    parser.add_argument('--nops', help="Don't plot oscillatory potentials", action="store_true", default=False)
    args = parser.parse_args()
    

    filenames = [os.path.join(args.base, f) for f in args.file]
    data = [load_file(fname) for fname in filenames]
    
    # merge the data dict from all specified files
    # going to merge the description to the step object
    for file_data in data:
        step_keys = file_data['stimuli'].keys()
        assert file_data['data'].keys() == step_keys
        for k in step_keys:
            file_data['data'][k].description = file_data['stimuli'][k]['description']
            file_data['data'][k].stim = file_data['stimuli'][k]['stim']
            
    data_merged = data.pop(0)

    data_merged = data_merged['data']
    idx = max(data_merged.keys())
    for d in data:
        for _, step in d['data'].items():
            idx = idx + 1
            data_merged[idx] = step
    
    # process any step information
    if args.stepInfo:
        for item in args.stepInfo:
            defaults.append(item)
    
    # Get the list of steps to process
    if args.step:
        steps = args.step
    elif args.noprompt:
        steps = data_merged.keys()
    elif args.defaults:
        steps = get_default_steps(data_merged)
    else:
        steps = get_steps(data_merged)
        
    # extract just the steps we are interested in
    data = [data_merged[step[0]] for step in steps]

    if not args.noprompt:
        lims = get_step_options(data_merged, steps)
    
    
    logger.info('Processing steps:{}'.format(steps))
    
    plot_steps(data, lims, args.output, args.eye)
    
    
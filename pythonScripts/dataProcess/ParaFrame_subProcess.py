# File: ParaFrame_subProcess.py
# Author: Weilin Zhang
# Desc: This program demonstrates parallel computations with pp module
# It process each subjob by a subprocess work.

import os,subprocess,sys,re,shutil,time
import argparse
import pp
from XXXX import paraClass

def init_options():
    description = "This is the description of the scirpt"
    
    parser=argparse.ArgumentParser(description=description)

    parser.add_argument("--np",dest="np",
        help="number of processors",type=int,default=1,
        required = False)
    parser.add_argument("--debug",dest="debug",
        help="debug switch True or False", type=bool,default=False,
        required = False)
    parser.add_argument("--verbose",help=("Verbose output"),
        default='', action="store_true")

    parser.add_argument("--clusterList",dest="clusterList",
        help="clusterList file contains each cavity job's input protein's info",
        required = True)
    parser.add_argument("--resultDir",dest="resultDir",
        help="Top level directory contains subdirs as /xx/yyyy/explicit_filenames",
        required = True)
    parser.add_argument("--sourceDir",dest="sourceDir",
        help="after join step all dat file will be in pkaDir/xx/yyyy",
        required = True)
    
    return parser

options = init_options().parse_args()
debug = options.debug

## Initialize pp server
ppservers = ()
if debug:
    ncpus = 1
else:
    ncpus = int(options.np)

job_server = pp.Server(ncpus, ppservers=ppservers,socket_timeout=36000)
# job_server = pp.Server(ppservers=ppservers,socket_timeout=36000)
print "Starting pp with", job_server.get_ncpus(), "workers"

# Prepare dependency tuples
moduleTuple = (MODULETUPLE,)
depFuncTuple = (FUNCTUPLE,)
# initialize a working class
CLASSINSTANCE = CLASSInitial(options) 

# Submit each argument, argument is not within the class
batchsize = 200
start = 0
FinalIndex = FINALINDEX

# Use Template to avoid debug and normal difference
fn = pp.Template(job_server,CLASSMETHOD,moduleTuple,depFuncTuple)
jobs = []
for start in xrange(0,FinalIndex,batchsize):
    stop = start+batchsize
    for i in xrange(start,stop):
        try:
            ARGUMENT=FUNCTION(i)
        except IndexError:
            break
        f = fn.submit(ARGUMENT)
        jobs.append(f)
    job_server.wait()   

# Sumbit a range of index (argument data is within class) 
nPart = 200
step = (end - FinalIndex) / nPart + 1
jobs = []
for index in xrange(nPart):
    starti = start+index*step
    endi = min(start+(index+1)*step, end)

    f = job_server.submit(CLASSMETHOD, (starti, endi),depFuncTuple,moduleTuple)
    jobs.append(f)
job_server.wait() 


job_server.print_stats()
job_server.destroy()
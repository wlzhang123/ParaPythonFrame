import os,subprocess,sys,re,shutil,time
import errno
from glob import glob
import argparse
import pp
#import ResEnv.ppUtil #import function from a file
from ResEnv.ppUtil import paraCavity # import a class from a file
def init_options():
    description = "This is the description of the scirpt"
    
    parser=argparse.ArgumentParser(description=description)
    
    #parser.add_argument("--cavityPath",dest="cavityPath",
    #    help=("The cavity exe path. Copy it here with directory "+
    #    "default and parameter is better"),
    #     default='',type=str,required=True)
    parser.add_argument("--clusterList",dest="clusterList",
        help="clusterList file contains each cavity job's input protein's info",
        required = True)
    parser.add_argument("--resultDir",dest="resultDir",
        help="Top level directory contains subdirs as /xx/yyyy/explicit_filenames",
        required = True)
    parser.add_argument("--sourceDir",dest="sourceDir",
        help="after join step all dat file will be in pkaDir/xx/yyyy",
        required = True)
    parser.add_argument("--np",dest="np",
        help="number of processors",type=int,default=1,
        required = False)
    parser.add_argument("--debug",dest="debug",
        help="debug switch True or False", type=bool,default=False,
        required = False)
    parser.add_argument("--verbose",help=("Verbose output"),
        default='', action="store_true")
    
    return parser

print """Usage: python run_cavity.py [ncpus]
    [ncpus] - the number of workers to run in parallel,
    if omitted it will be set to the number of processors in the system
"""

# tuple of all parallel python servers to connect with
#ppservers = ("*",) # auto-discover
#ppservers = ("10.0.0.1","10.0.0.2") # list of static IPs
## Parse arguments from command line

options = init_options().parse_args()

## initialize main running instance

runCavity = paraCavity(options)

## Restart File Handling to be incoporated
# process = wlutil.BackupOpen("Stage4_process.list")

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


moduleTuple = ('os','subprocess','re','time','errno','shutil','argparse','ResEnv.ppUtil')
depFuncTuple = ()
results = []

batchsize = 200
start = 0

# start Loop
FinalIndex = len(runCavity.paraList)

if debug:
    for start in xrange(0,FinalIndex,batchsize):
        stop = start+batchsize
        for i in xrange(start,stop):
            try:
                proteinInfo = runCavity.paraList[i]
            except IndexError:
                break

            # if proteinInfo not in runCavity.checkedList:
            #f = job_server.submit(runCavity.say_hello,(proteinInfo,),depFuncTuple,moduleTuple)
            runCavity.say_hello(proteinInfo)
            
            #print proteinInfo
            #results.append(f)
        #job_server.wait()
        # progress(100,int(float(stop)/len(runCavity.proteinList)*100))
        # for i in xrange(start,stop):
        #     try:
        #         proteinInfo = runCavity.proteinList[i]
        #     except IndexError:
        #         break
        #     if proteinInfo not in runCavity.checkedList:
        #         runCavity.updateInfo(proteinInfo)
else:
    for start in xrange(0,FinalIndex,batchsize):
        stop = start+batchsize
        for i in xrange(start,stop):
            try:
                proteinInfo = runCavity.paraList[i]
            except IndexError:
                break

            # if proteinInfo not in runCavity.checkedList:
            f = job_server.submit(runCavity.say_hello,(proteinInfo,),depFuncTuple,moduleTuple)
            # runCavity.say_hello(proteinInfo)
            
            #print proteinInfo
            results.append(f)
        job_server.wait()
        # progress(100,int(float(stop)/len(runCavity.proteinList)*100))

        # for i in xrange(start,stop):
        #     try:
        #         proteinInfo = runCavity.proteinList[i]
        #     except IndexError:
        #         break
        #     if proteinInfo not in runCavity.checkedList:
        #         runCavity.updateInfo(proteinInfo)





# print results
# for f in results:
#     print f()




# for proteinInfo in runCavity.proteinList:
#     print proteinInfo
#     if proteinInfo not in runCavity.processedList:
#         f = runCavity.say_hello(proteinInfo)
#         results.append(f)




job_server.print_stats()
job_server.destroy()
import os,subprocess,sys,re,shutil,time
import errno
from glob import glob
import argparse
import pp

import ResEnv.wlutil

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
    
    #  parser.add_argument('--resultPath',dest='resultPath',
    # help="path to the result path.",
    # required = True)
    # parser.add_argument('--mmcifPath',dest='mmcifPath',
    #     help="path to the original mmcif file path.",
    #     required = True)
    #parser.add_argument('--processPrefix',dest='processPrefix',
    #     help="prefix for Prefix-processed.list and Prefix-bad.list",
    #     default='default')
    # parser.add_argument("ddd",help="fake positional argument")
    # parser.add_argument("eee",help="fake positional argument 2. anyway, after ddd")
    return parser

class paraCavity(object):
    # def __init__(self, proteinDirPath='',cavityPath='',inputPath=''):
    def __init__(self, options):
        """
        This class contains methods which will be executed in parallel
        """
        
        self.proteinList=[] # this is used for parallel
        self.readInList(options)
        
        self.sourceDir = options.sourceDir
        self.resultDir = options.resultDir
        # self.envDir = options.envDir
        # self.pkaDir = options.pkaDir
        # self.resultDir = './loopTest'
        

        pass

    def readInList(self,options):
        fh = open(options.clusterList,'r')
        AllLines = fh.readlines()
        for line in AllLines:
            tempList = line.strip().split(' ')
            # self.proteinList
            # cleanPDBDir = "%s/%s/%s"%(self.cleanDir,tempList[0],tempList[1].lower())
            # self.mkdir_p(cleanPDBDir)
            # resultPDBDir = "%s/%s/%s"%(self.resultDir,tempList[0],tempList[1].lower())
            # self.mkdir_p(resultPDBDir)
            self.proteinList.append(tempList[1]+":"+tempList[2])
        # print AllLines
        pass
    def mkdir_p(self,path):
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5 (except OSError, exc: for Python <2.5)
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise

    def makeCavityInput(self,pdb,chain,pdbPath):

        inputfile = '%s/%s_%s_cavity.in'%(os.path.dirname(pdbPath),pdb,chain)
        with open(inputfile,'w') as fh:
            fh.write('INCLUDE                ./default/cavitydefault.input\n')
            fh.write('DETECT_MODE            0\n')
            fh.write('RECEPTOR_FILE             %s\n'%(pdbPath))
            fh.write('LIGBUILDER            0\n')
            fh.write('VISUAL_OUTPUT            0\n')
            fh.write('INCLUDE                ./default/standard.input\n')
        return inputfile
    # prepare inputfiles
    # unzip in shaft

    def retrieveInfo(self,proteinInfo):
        pdbID = proteinInfo[0:4].lower()
        subDir = pdbID[1:3].lower()
        chainID = proteinInfo[5]
        return pdbID,subDir,chainID

    def unzipFile(self,proteinInfo):
        pdbID,subDir,chainID= self.retrieveInfo(proteinInfo)
        cleanDir = self.cleanDir+'/'+subDir+'/'+pdbID
        resultDir = self.resultDir+'/'+subDir+'/'+pdbID
        mmcifPath = self.mmcifPath+'/'+subDir+'/'+pdbID+'.cif.gz'
        # pass

        cmdline = '"D:\\Program Files\\7-Zip\\7z.exe" e -y %s -o%s'%(mmcifPath,cleanDir)
        # cmdline = '/lustre1/lhlai_pkuhpc/wlzhang/usr/local/7z/bin/7z e -y %s'%(compoundLib)
        # cmdline = '"D:\\Program Files\\7-Zip\\7z.exe" e %s'%(compoundLib)
        # print cmdline
        outname = "%s/%s_unzip.out"%(cleanDir,pdbID)
        fh = open(outname,'w')

        # subprocess.Popen(cmdline,shell=True,stdout=fh,stderr=fh,close_fds=True).wait()
        subprocess.Popen(cmdline,shell=True,stdout=fh,stderr=fh).wait()

    def cif2pdb(self,proteinInfo):
        pdbID,subDir,chainID = self.retrieveInfo(proteinInfo)
        # removed and check other file for detail
        pass
    def checkExist(self,proteinInfo):
        pdbID,subDir,chainID = self.retrieveInfo(proteinInfo)
        pdbFile = pdbID.lower()+'_'+chainID+'.pdb'
        sourceDir = self.sourceDir+'/'+subDir+'/'+pdbID
        # cifPath = cleanDir  + '/'+cifFile
        pdbPath = sourceDir  + '/'+pdbFile
        print chainID,proteinInfo,pdbPath
        pdbKey = pdbID+":"+chainID
        # if pdbKey in self.checkedList:
        #     # print "%s has been checked"%(proteinInfo)
        #     return False

        if os.path.isfile(pdbPath):
            return True
        else:
            return False
        pass
    def updateInfo(self,proteinInfo):
        pdbID,subDir,chainID = self.retrieveInfo(proteinInfo)
        cleanDir = self.cleanDir+'/'+subDir+'/'+pdbID
        # print cleanDir
        pass 
    def runSaveSubprocess(self,cmdline='',outPrefix='out',):
        # cmdline = "python ../../../CYS_cavity_grep_single.py --pdbID %s --residue %s"%(pdbID,"CYS")
        if cmdline=='':
            return 0

        outname = "%s.out"%(outPrefix)   
        fh = open(outname,'w')
        subprocess.Popen(cmdline,shell=True,stdout=fh,stderr=fh).wait()
        fh.flush()
        os.fsync(fh)
        time.sleep(1)
        fh.close()

    def prepareInput(self,proteinInfo):
        ###############################To be changed ###########################################
        # 1. make Result dir in __init__ by readinList function
        # 2. The sourceDir has the same architecture as resultDir: /xx/yyyy/exsitFiles
        # 3. copy file to resultDir
        # 4. chdir to resultDir and run workhorse script there

        
        pdbID,subDir,chainID = self.retrieveInfo(proteinInfo)

        # pdbReady = self.checkExist(proteinInfo)
        # if not pdbReady:
        #     print "notready"
        #     return False

        # 
        pdbFile = pdbID.lower()+'_'+chainID+'.pdb'

        pkaDir = self.pkaDir+'/'+subDir+'/'+pdbID
        envDir = self.envDir+'/'+subDir+'/'+pdbID
        #   
        pkaPDB = pkaDir  + '/'+pdbFile
        envPDB  = envDir + '/' +pdbFile

        pdbInfo = pdbID+'_'+chainID
        grepResidue = "CYS"

        envFile = envDir + '/' +"%s_%s.dat"%(pdbInfo,grepResidue)
        destFile = pkaDir + '/' +"%s_%s.dat"%(pdbInfo,grepResidue)
        # if os.path.isfile(envFile):
        #     shutil.copy(envFile,destFile)
        # else:
        #     return False


    
        # Step 1
        # This is done by propka but doing it once more doesn't hurt
        # it should be mocked on windows as there is no pdb4amber on windows
        # setup commandline argument

        # whether to import platform
        pdbFileAmber = re.sub('.pdb','_amb.pdb',pdbFile)

        # import platform
        # if platform.system() == 'Linux':
            
        pkaPDB = pkaDir  + '/'+ pdbFileAmber

        
        workDir = os.path.dirname(pkaPDB)
        print workDir
        topDir = os.getcwd()
        print topDir

        os.chdir(workDir)
        print os.getcwd()



        pdbInfo = "%s_%s"%(pdbID,chainID)
        grepResidue = "CYS"

        pkaFile = 'pka_%s_%s.list'%(pdbInfo,grepResidue)
        renumFile = 'Renumber_%s.list'%(pdbInfo)
        cavityFile = 'Cav_%s.list'%(grepResidue)
        envFile = "%s_%s.dat"%(pdbInfo,grepResidue)

        with open(envFile) as fh:
            envLines = fh.readlines();
        with open(cavityFile) as fh:
            cavityLines = fh.readlines()
        with open(renumFile) as fh:
            renumLines = fh.readlines()
        with open(pkaFile) as fh:
            pkaLines = fh.readlines()

        # print envLines
        # print cavityLines
        # print renumLines
        # print pkaLines



        def generateDict(AllLines,index):
            Dict = {}
            for line in AllLines:
                tempArray = line.strip().split()
                Dict[tempArray[index]] = tempArray
            return Dict
        def printDict(Dict):
            for key in Dict.keys():
                print Dict[key]

        cavDict = generateDict(cavityLines,1)
        pkaDict = generateDict(pkaLines,1)
        renumDict = generateDict(renumLines,2)
        envDict = generateDict(envLines,4)
        # map(lambda x: print x,[pkaDict[key] for key in pkaDict.keys()])
        # AllResDict All Residue Dict
        # CavResDict: Residue in cavity
        # NonResDict: Residue not in cavity, either surface or buried
        # CavPkaOK = {}
        # CavPkaBad = {}
        # NonCavPkaOK = {}
        # NonCavPkaBad = {}
        class resultDict(object):
            def __init__(self):
                self.AllResDict = {}
                self.CavResDict = {}
                self.NonCavResDict = {}
                self.CavPkaOK = {}
                self.CavPkaBad = {}
                self.NonCavPkaOK = {}
                self.NonCavPkaBad = {}
                ## save your time :type it twice: DRY, it is not working here
                self.outList = ['AllResDict','CavResDict','NonCavResDict','CavPkaOK','CavPkaBad','NonCavPkaOK','NonCavPkaBad']
            # def writeDatFile(self,pdbInfo='protein',Residue='XXX'):
            def writeDatFile(self,pdbInfo='protein',Residue='XXX'):
                for key in self.outList:
                    # print key
                    prefix = key
                    fileName = "%s_%s_%s.dat"%(prefix,pdbInfo,Residue)
                    print fileName
                    with open(fileName,'w') as fh:
                        Dict = getattr(self,key)
                        for key in Dict.keys():
                            tempArray =Dict[key]
                            fh.write(' '.join(tempArray)+'\n')

        outResult = resultDict()

        # AllResDict = {}
        # CavResDict = {}
        # NonCavResDict = {}
        # CavPkaOK = {}
        # CavPkaBad = {}
        # NonCavPkaOK = {}
        # NonCavPkaBad = {}

        for key in renumDict.keys():
            newKey = renumDict[key][1]
            tempArray = [renumDict[key][0],key]
            tempArray.extend(pkaDict[newKey][2:])
            tempArray.extend(envDict[newKey][5:])
            # outResult.AllResDict[key] = tempArray
            # AllResDict[key]=tempArray
            outResult.AllResDict[key]=tempArray

        cavDict['None'] = ['None.pdb','999','0','0','0','0','0','0','None']
        # 1st filter
        for key in renumDict.keys():
            # print newKey,key
            if key in cavDict.keys():
                tempArray = cavDict[key]
                # tempArray.extend(AllResDict[key][2:])
                tempArray.extend(outResult.AllResDict[key][2:])
                outResult.CavResDict[key]=tempArray
            else:
                tempArray = [renumDict[key][0],key]
                tempArray.extend(cavDict['None'])
                tempArray.extend(outResult.AllResDict[key][2:])
                outResult.NonCavResDict[key]=tempArray
        # 2nd filter 2^2
        for key in outResult.CavResDict.keys():
            tempArray = outResult.CavResDict[key]
            if tempArray[11]=='99.99':
               outResult.CavPkaBad[key] = tempArray
            else:
               outResult.CavPkaOK[key] =tempArray

        for key in outResult.NonCavResDict.keys():
            tempArray = outResult.NonCavResDict[key]
            if tempArray[11]=='99.99':
               outResult.NonCavPkaBad[key] = tempArray
            else:
               outResult.NonCavPkaOK[key] =tempArray


        
        outResult.writeDatFile(pdbInfo,grepResidue)
        #printDict(outResult.AllResDict)
        # # print "NonCavRes"
        # printDict(NonCavResDict)
        # # print "CavPkaOK"
        # printDict(CavPkaOK)

        os.chdir(topDir)
        print os.getcwd()
        return True

    def say_hello(self,proteinInfo):
        
        # targetMol2 = self.unzip(compoundLib)
        # cynthia = self.cynthia(targetMol2)
        # return "hello %s unzip %s cynthia %s"%(compoundLib,targetMol2,cynthia)
        cavityInput = self.prepareInput(proteinInfo)


        if cavityInput:
            #self.runCavity(cavityInput)
            return "hello protein success %s %s"%(cavityInput,proteinInfo)
        else:
            return "hello protein problem %s %s"%(cavityInput,proteinInfo)
        # pass
        # runCavity = self.runCavity(cavityInput)
        
        # return "hello protein %s cavity status %s"%(protein,runCavity)
        
        # return "hello protein %s"%(protein)


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

# print debug,ncpus
# exit(0)

job_server = pp.Server(ncpus, ppservers=ppservers,socket_timeout=36000)
# job_server = pp.Server(ppservers=ppservers,socket_timeout=36000)
print "Starting pp with", job_server.get_ncpus(), "workers"


moduleTuple = ('os','subprocess','re','time','errno','shutil','argparse','ResEnv.wlutil')
depFuncTuple = ()
results = []
# print runCavity.checkedList

# used for restart handling
batchsize = 200
start = 0

# progress for waiting
def progress(width, percent):  
    print "%s %d%%\r" % (('%%-%ds' % width) % (width * percent / 100 * '='), percent),  
    if percent >= 100:  
        print  
        sys.stdout.flush()  

# start Loop
FinalIndex = len(runCavity.proteinList)

if debug:
    for start in xrange(0,FinalIndex,batchsize):
        stop = start+batchsize
        for i in xrange(start,stop):
            try:
                proteinInfo = runCavity.proteinList[i]
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
                proteinInfo = runCavity.proteinList[i]
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
    #
    # badpdb.write('####################\n')
# resultList = glob('*.list')
# print resultList
# resultMol2 = glob('*Hits.mol2')
# print resultMol2

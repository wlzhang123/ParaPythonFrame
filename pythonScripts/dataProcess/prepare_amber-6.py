#!/lustre1/lhlai_pkuhpc/wlzhang/python27/bin/python
## 
## Devleena Shivakumar, TSRI 05/24/2006.
##	Master script to process a multiple ligand mol2 file, usually
##	a DOCK ranked ligands file, and a receptor PDB file into the
##	many pieces needed by DOCK's amber_score.
## Scott Brozell, TSRI 2007-8: updated error handling, added -i and -c.
## 
## Weilin Zhang 01/2017 To Python. Parallel on HPC.
##

import sys,re,os,subprocess,errno,shutil,logging
import pp
import argparse


def init_options():
	usage = "% prog prepare_amber-4.py mol2File proteinPDB nodelist" 
	parser = argparse.ArgumentParser(description=usage)
	parser.add_argument('-m',dest='mol2File',required=True,
										help='mol2 File',type=str,default="")
										
	parser.add_argument('-p',dest='pdbFile',required=True,
										help='pdb File as topology',type=str,default="")

	parser.add_argument("-node",help=("Verbose output"),dest="nodelist",
												default='nodelist.out')
	return parser


options = init_options().parse_args()

####################################################################
############   Parallel job setup part                        ######
####################################################################
with open(options.nodelist,'r') as fh:
	ppservers = tuple(fh.readline().strip().split(' '))
print(ppservers)

logging.basicConfig(level = logging.DEBUG)
logger = logging.getLogger("__name__")
logger = logging.getLogger("ppp-5")
handler = logging.FileHandler("log-pp.log")
handler.setLevel(logging.WARNING)
logger.addHandler(handler)

job_server = pp.Server(ppservers=ppservers,socket_timeout=36000)
#job_server.set_ncpus(1)
print("Startng pp with %d workers"%job_server.get_ncpus())

####################################################################

use_existing_ligand_charges = 1
ignore_amberize_errors = 0

mol2_file=options.mol2File
rec_pdb_file=options.pdbFile

# assign basename for output files based on input MOL2 filename:

regSearch=re.search("(\w+).(\w+)",mol2_file)
prefix=regSearch.group(1)
print prefix


#########################################################################
#### SECTION:1: generates receptor files; calls amberize_receptor	####
#########################################################################
#

regSearch=re.search("(\w+).(pdb)",rec_pdb_file)
rec_file_prefix=regSearch.group(1)
print rec_file_prefix

subprocess.Popen("/lustre1/lhlai_pkuhpc/wlzhang/usr/local/tools/amberize_receptor %s 1>amberize_receptor.out 2>&1"%(rec_file_prefix),shell=True).wait()
print "Coordinate and parameter files for the Receptor %s generated.\n"%(rec_pdb_file)

###############################################################################
#### SECTION:2: splits multi-MOLECULE input mol2 into individual mol2 files ###
###############################################################################
#
print("Splitting the multiple Ligand mol2 file into single mol2 files.\n")
print("The single mol2 files will have the prefix: %s"%(prefix))

## assign basename for output files based on input MOL2 filename:
#
with open(mol2_file,'r') as fh:
	allLines = fh.readlines()

global_count = 0
local_count = 0
for line in allLines:
	if re.search('^(@<TRIPOS>MOLECULE)',line):
		global_count=global_count+1
		fh=open("%s.%s.mol2"%(prefix,global_count),'w')
		fh.write(line)
		local_count=local_count+1
		
	
	if re.search('^(@<TRIPOS>MOLECULE)',line) and local_count>1:
		### This is used to avoid deep wrapped if in the above if ###
		### After MOLECULE line is write, just continue for next ####
		local_count=1
		continue
	
	if not re.search('^(@<TRIPOS>MOLECULE)',line) and not re.search('^(#######)',line) and local_count == 1:
		fh.write(line)
		continue


fh.close()
print("The number of single Ligand mol2 files generated is %d"%(global_count))

for index in range(1,global_count+1):
	if not os.path.isfile('%s.%d.mol2'%(prefix,index)):
		print '%s.%d.mol2 is not ready in stage 3'%(prefix,index)

###############################################################################
##### Stage 3 make each subdir with batch size # of mol2                #######
###############################################################################

# Auxillary Function
def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5 (except OSError, exc: for Python <2.5)
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else: raise
# Auxillary Function 
def subDirMoving(prefix,rec_file_prefix,start,stop,subDir):
	logger = logging.getLogger("__name__")
	suffixList = ['amber.pdb','inpcrd','prmtop']
	suffixList2 = ['mol2']
	
	# copy protein
	for suffix in suffixList:
		fileName = "%s.%s"%(rec_file_prefix,suffix)
		shutil.copy(fileName,'./%s/%s'%(subDir,fileName))

	# copy ligands
	mcount = 0
	for lignum in range(start,stop):
		mcount = mcount + 1
		try:
			for suffix in suffixList2:
				fileName = "%s.%d.%s"%(prefix,lignum,suffix)
				newName = "%s.%d.%s"%(prefix,mcount,suffix)
				logger.debug(fileName,newName)
				#shutil.move(fileName,'./%s/%s'%(subDir,newName))
				shutil.copy("./%s"%(fileName),"./%s/%s"%(subDir,newName))
		except Exception,e:
			raise	
			#with open("move.%s.%d.err"%(prefix,lignum),'w') as efh:
				#efh.write(Exception) #efh.write(e.str())
			exit(-1)
	
batchSize = 1000

#### Assign dependency before submit ##### 
depfuncs=()
modules=('shutil','logging',)
##########################################

totalIndex = global_count/batchSize+1
start = 1
#for lignum in range(1,global_count+1):

resultList=[]
for subDirIndex in range(0,totalIndex):
	#mCount = mCount + 1
	subDir = "amber-%d"%(subDirIndex)
	mkdir_p(subDir)
	
	starti = start + subDirIndex*batchSize
	stopi = min(start + (subDirIndex+1)*batchSize,global_count+1)
	print subDirIndex,starti,stopi
	job=job_server.submit(subDirMoving,(prefix,rec_file_prefix,starti,stopi,subDir),depfuncs,modules)
	#subDirProcess(prefix,rec_file_prefix,start,stop,subDir)
	resultList.append(job)

######  logging Later ######
for job in resultList:
	#logger.info(job())
	print job()
	logger.info(job())
print "stop for moving"


################################################################################
#### SECTION:4: generate files for ligand and complex; call amberize scripts ###
################################################################################
#
print("Generating coordinate and parameter files for Ligands and Complexes.\n")
if use_existing_ligand_charges:
	print("Using existing charges from %s\n"%(mol2_file))

else:
	print("Generating AM1-BCC charges.  This may be time consuming.\n")


def round(sum1):
	if sum1>0:
		multi=1
	elif sum1<0:
		multi=-1
	else:
		multi=0
	return int(sum1 + 0.5 * multi)

# This step should be paralleled:

def prepareTopFiles(prefix,lignum,chargeOption):
	#print "%s.%d.mol2"%(prefix,lignum)
	sum1 = 0
	with open("%s.%d.mol2"%(prefix,lignum),'r') as fh:
		sAllLines=fh.readlines()
	
	for line in sAllLines:
		tempList =line.strip().split()
		#print len(tempList)
		if len(tempList)==9 and not re.search('ROOT',line):
			sum1=sum1+float(tempList[8])
			sum = round(sum1)
			#print sum
	print("Ligand %s.%d has total charge %d,%f\n"%(prefix,lignum,sum,sum1));
	
	charge_method = ''
	if chargeOption:
		charge_method = "-s 2" 
	else:
		charge_method = "-nc $sum -c bcc"
	#print charge_method
	stat = subprocess.Popen("/lustre1/lhlai_pkuhpc/wlzhang/usr/local/tools/amberize_ligand %s.%d %s 1> amberize_ligand.%s.%d.out 2>&1"%(prefix,lignum,charge_method,prefix,lignum),shell=True).wait()
	if stat!=0:
		#print "\nError from amberize_ligand; the name of the ligand is\n";
		#print "	%s\n"%(fileName)

		shutil.copy("%s.%d.mol2"%(prefix,lignum),"%s.%d.mol2.err"%(prefix,lignum))
		#shutil.copy("amberize_ligand.%s.%d.out"%(prefix,lignum),
		#"amberize_ligand.%s.%d.err"%(prefix,lignum))
		shutil.copy("/lustre1/lhlai_pkuhpc/wlzhang/usr/local/tools/FAKE-lig.mol2","%s.%d.mol2"%(prefix,lignum))
		stat2=subprocess.Popen("/lustre1/lhlai_pkuhpc/wlzhang/usr/local/tools/amberize_ligand %s.%d %s 1> amberize_ligand.%s.%d.out 2>&1"%(prefix,lignum,charge_method,prefix,lignum),shell=True).wait()
		if stat2!=0:
			print "Fix Failed for ligand %s.%d.mol2"%(prefix,lignum)
			with open("PP-error-File.err",'w') as fh:
				fh.write("%s.%d.mol2 caused the program to stop\n")

			exit(-1)
	subprocess.Popen("/lustre1/lhlai_pkuhpc/wlzhang/usr/local/tools/amberize_complex %s %s.%d 1> amberize_complex.%s.%d.out  2>&1"%(rec_file_prefix,prefix,lignum,prefix,lignum),shell=True).wait()

#######################
#### Dependency #######
#######################
#depfuncs=(round,)
# modules=()

#######################
##  work frame ########
# resultList=[]
#for index in range(0,totalIndex):
#	job = job_server.submit(function,(argument),depfuncs,modules=()
#	resultList.append(job)
#for job in resultList:
#	logger.info(job())
#	print job()
#	logger.info(job())
#job_server.print_stats()
########################

depfuncs=(round,)
modules=('subprocess','shutil',)
resultList=[]
for subDirIndex in range(0,totalIndex):
	#mCount = mCount + 1
	subDir = "amber-%d"%(subDirIndex)

	topDir = os.getcwd()
	os.chdir(subDir)
	for lignum in range(1,batchSize+1): 
		job = job_server.submit(prepareTopFiles,(prefix,lignum,use_existing_ligand_charges),depfuncs,modules)
	os.chdir(topDir)
	resultList.append(job)

######  logging Later ######
for job in resultList:
	#logger.info(job())
	print job()
	logger.info(job())
print "stop for moving"


################################################################################
#### SECTION:5: generate .amber_score.mol2 for processed data                ###
################################################################################
#
def catMol2(prefix,subDir,batchSize)
	fh=open('%s/%s.amber_score.mol2'%(subDir,prefix),'w')
	for index in range(1,batchSize+1):
		with open("%s/%s.%d.mol2"%(subDir,prefix,index),'r') as tfh:
			sAllLines = tfh.readlines()

		for line in sAllLines:
			fh.write(line)

		fh.write("@<TRIPOS>AMBER_SCORE_ID\n")
		fh.write("%s.%d\n\n\n"%(prefix,index))

depfuncs=(round,)
modules=('subprocess','shutil',)

resultList=[]
for subDirIndex in range(0,totalIndex):
	#mCount = mCount + 1
	subDir = "amber-%d"%(subDirIndex)
	
	job = job_server.submit(catMol2,(prefix,subDir,batchSize),depfuncs,modules)
	resultList.append(job)

print("completed.\n")

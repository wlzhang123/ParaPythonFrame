#!/lustre1/lhlai_pkuhpc/wlzhang/python27/bin/python
##
## Devleena Shivakumar, TSRI 05/24/2006.
##	Master script to process a multiple ligand mol2 file, usually
##	a DOCK ranked ligands file, and a receptor PDB file into the
##	many pieces needed by DOCK's amber_score.
## Scott Brozell, TSRI 2007-8: updated error handling, added -i and -c.
#
##
#my $ignore_amberize_errors = 0 ;
import sys,re,os,subprocess,errno
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

with open(options.nodelist,'r') as fh:
    ppservers = tuple(fh.readline().strip().split(' '))
print(ppservers)


job_server = pp.Server(ppservers=ppservers,socket_timeout=36000)
print("Startng pp with %d workers"%job_server.get_ncpus())


use_existing_ligand_charges = 1
ignore_amberize_errors = 0
# mol2_file=sys.argv[1]
# rec_pdb_file=sys.argv[2]

mol2_file=options.mol2File
rec_pdb_file=options.pdbFile

#########################################################################
#### SECTION:1: generates receptor files; calls amberize_receptor	####
#########################################################################
#

regSearch=re.search("(\w+).(pdb)",rec_pdb_file)
rec_file_prefix=regSearch.group(1)
print rec_file_prefix

subprocess.Popen("/lustre1/lhlai_pkuhpc/wlzhang/usr/local/tools/amberize_receptor %s 1>amberize_receptor.out 2>&1"%(rec_file_prefix),shell=True).wait()
print "Coordinate and parameter files for the Receptor %s generated.\n"%(rec_pdb_file)
#
##############################################################################
#### SECTION:2: adds the AMBER_SCORE_ID to each MOLECULE in the input mol2 ###
##############################################################################
#

global_count=0
local_count=0


# assign basename for output files based on input MOL2 filename:

regSearch=re.search("(\w+).(\w+)",mol2_file)
prefix=regSearch.group(1)
print prefix

with open(mol2_file,'r') as fh:
	allLines = fh.readlines()
fh=open('%s.amber_score.mol2'%(prefix),'w')
for line in allLines:
	if re.search('^(@<TRIPOS>MOLECULE)',line):
		if local_count!=0:
			fh.write("@<TRIPOS>AMBER_SCORE_ID\n")
			fh.write("%s.%d\n\n\n"%(prefix,global_count))
		fh.write(line)
		local_count=local_count+1
		global_count=global_count+1
	
	if re.search('^(@<TRIPOS>MOLECULE)',line) and local_count>1:
		local_count=1
		continue
	
	if not re.search('^(@<TRIPOS>MOLECULE)',line) and not re.search('^(#######)',line) and local_count == 1:
		fh.write(line)
		continue

fh.write("@<TRIPOS>AMBER_SCORE_ID\n")
fh.write("%s.%d\n\n\n"%(prefix,global_count))
fh.close()

print "The AMBER score tagged mol2 file %s.amber_score.mol2 generated."%(prefix)

###############################################################################
#### SECTION:3: splits multi-MOLECULE input mol2 into individual mol2 files ###
###############################################################################
#
print("Splitting the multiple Ligand mol2 file into single mol2 files.\n")
print("The single mol2 files will have the prefix: %s"%(prefix))

global_count = 0
local_count = 0


## assign basename for output files based on input MOL2 filename:
#
with open(mol2_file,'r') as fh:
	allLines = fh.readlines()

for line in allLines:
	if re.search('^(@<TRIPOS>MOLECULE)',line):
		global_count=global_count+1
		fh=open("%s.%s.mol2"%(prefix,global_count),'w')
		fh.write(line)
		local_count=local_count+1
		
	
	if re.search('^(@<TRIPOS>MOLECULE)',line) and local_count>1:
		local_count=1
		continue
	
	if not re.search('^(@<TRIPOS>MOLECULE)',line) and not re.search('^(#######)',line) and local_count == 1:
		fh.write(line)
		continue

print("The number of single Ligand mol2 files generated is %d"%(global_count))
fh.close()

for index in range(1,global_count+1):
	if not os.path.isfile('%s.%d.mol2'%(prefix,index)):
		print '%s.%d.mol2 is not ready in stage 3'%(prefix,index)


##### Stage 5 make each subdir for with batch size and fixed amber_score file ########################

def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5 (except OSError, exc: for Python <2.5)
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else: raise

def subDirProcess(prefix,rec_file_prefix,lignum,mCount,subDir,fh):
	suffixList = ['amber.pdb','inpcrd','prmtop']
	suffixList2 = ['mol2']
	try:
		#for prot:
		for suffix in suffixList:
			fileName = "%s.%s"%(rec_file_prefix,suffix)
			# shutil.move(fileName,'./%s/%s'%(subDir,fileName))
			shutil.copy(fileName,'./%s/%s'%(subDir,fileName))
		for suffix in (suffixList+suffixList2):
			fileName = "%s.%d.%s"%(prefix,lignum,suffix)
			newName = "%s.%d.%s"%(prefix,mCount,suffix)
			# shutil.move(fileName,'./%s/%s'%(subDir,newName))
			shutil.copy(fileName,'./%s/%s'%(subDir,newName))
	except Exception,e:
		print Exception
		print e

	with open("%s/%s.%d.mol2"%(subDir,prefix,mCount),'r') as tfh:
		sAllLines = tfh.readlines()
	
	for line in sAllLines:
		fh.write(line)

	fh.write("@<TRIPOS>AMBER_SCORE_ID\n")
	fh.write("%s.%d\n\n\n"%(prefix,mCount))
	
batchSize = 1000
subDirIndex = 0
mCount = 0

depfuncs=()
modules=()

subDir = "amber-%d"%(subDirIndex)
mkdir_p(subDir)
fh=open('%s/%s.amber_score.mol2.fix'%(subDir,prefix),'w')

for lignum in range(1,global_count+1):
	mCount = mCount + 1
	subDir = "amber-%d"%(subDirIndex)

	job_server.submit(subDirProcess,(prefix,rec_file_prefix,lignum,mCount,subDir,fh),depfuncs,modules)

	if mCount%batchSize==0:
		subDirIndex = subDirIndex + 1
		subDir = "amber-%d"%(subDirIndex)
		mkdir_p(subDir)
		mcount = 0
		fh.close()
		fh=open('%s/%s.amber_score.mol2.fix'%(subDir,prefix),'w')

fh.close()


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
		# if re.search('@<TRIPOS>MOLECULE',line):
		# 	forName=True
		# if forName:
		# 	mol_name=line.strip()
		# 	mol_name=re.sub('\s+$','',mol_name)
		# 	forName=False
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
depfuncs=('round')
modules=()
for index in range(0,subDirIndex+1):
    subDir = "amber-%d"%(index)
    topDir = os.getcwd()
    os.chdir(subDir)
	for lignum in range(1,batchSize+1): 
	    job_server.submit(prepareTopFiles,(prefix,lignum,use_existing_ligand_charges),depfuncs,modules)
    os.chdir(topDir)

print("completed Stage 4.\n")



print("completed.\n")

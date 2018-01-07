# Submit a job: Normal syntax. 
job_server = pp.Server(ncpus, ppservers=ppservers)
# 
job_server.submit(func1, args1, depfuncs1, modules1)
job_server.submit(sum_primes, (100,), (isprime,), ("math",))
#  func1: sum_primes - the function
#  arg1: (100,) - tuple with arguments for sum_primes
#  depfuncs1: (isprime,) - tuple with functions on which function sum_primes depends
#  modules1: ("math",) - tuple with module names which must be imported before sum_primes execution

# depfuncs1: the functions used by func1.
# modules1:  modules that contain methods used within func1 or depfuncs1


# Submit a job: Via template submission:
fn = pp.Template(job_server, sum_primes, (isprime,), ("math",))
#  Initialize with such arguments:
#  func1: sum_primes - the function
#  depfuncs1: (isprime,) - tuple with functions on which function sum_primes depends
#  modules1: ("math",) - tuple with module names which must be imported before sum_primes execution
job1 = fn.submit(100)

### submit(self, *args)

# Setup Sub job for better load balancing
# 10000 job: into 200*50 job, 
# each time submit 200 job, with outer loop 50 times
# each time: 10*20,for 50 times. 
#
# To avoid: 500*20 into 20 queue, then one worker is overloaded
# It may be not necessary 
# Worst case: 1 job is longer than all other 10 (199/20) jobs.
# 1 job is longer than 10 jobs.

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

# Use simple sub job to Run 
nPart = 200
step = (end - FinalIndex) / nPart + 1
jobs = []
for index in xrange(nPart):
    starti = start+index*step
    endi = min(start+(index+1)*step, end)
    f = job_server.submit(CLASSMETHOD, (starti, endi),depFuncTuple,moduleTuple)
    jobs.append(f)
job_server.wait() 


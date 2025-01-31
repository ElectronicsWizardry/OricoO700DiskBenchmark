#!/usr/bin/env python3


#Disk Bench, mostly for ew videos
#By Brandon Aitken 2023-12-31

#version 0.2, now with a log file of trim times

import argparse
import os
import sys
import time
from shutil import copyfile
import csv

if os.system('which fio'):
    print("fio isn't found, please install")

try:
    WORKING_DIR=sys.argv[2]
except:
    WORKING_DIR=os.getcwd()

print(WORKING_DIR)

# test data = 
#2d array first d = test
#2nd d = test configs
#Test Name, Trim before run, queue depth, num jobs, block size, data operation(read,write, randread,randwrite), runtime(0 = complete full drive read/write)
EMPTY_TESTS=[['emptySeqRead','1','1','4','1M','read','0','async'], ['emptySeqWrite','1','1','4','1M','write','0','async'], ['empty1qdRandRead','1','1','1','4k','randread','180','async'], ['empty1qdRandWrite','1','1','1','4k','randwrite','180','async'],['emptySyncRandWrite','1','1','1','4k','randwrite','180','sync'], ['empty8qdRandRead','1','2','4','4k','randread','180','async'], ['empty8qdRandWrite','1','2','4','4k','randwrite','180','async'], ['emptyqd1Mixed','1','1','1','8k','randrw','180','async'], ['emptyqd16Mixed','1','4','4','8k','randrw','180','async']]
FULL_TESTS=[['fullSeqRead','0','1','4','1M','read','0','async'], ['fullSeqWrite','0','1','4','1M','write','0','async'], ['full1qdRandRead','0','1','1','4k','randread','180','async'], ['full1qdRandWrite','0','1','1','4k','randwrite','180','async'], ['fullSyncRandWrite','0','1','1','4k','randwrite','180','sync'], ['full8qdRandRead','0','2','4','4k','randread','180','async'], ['full8qdRandWrite','0','2','4','4k','randwrite','180','async'], ['fullqd1Mixed','0','1','1','8k','randrw','180','async'], ['fullqd16Mixed','0','4','4','8k','randrw','180','async']]

#Variables, mostly for tweaking when set

IDLE_TIME=180 #Time in seconds to idle drive between tests
#IDLE_TIME=4 #set to 4 to speed up testing FIX ME!!!

DRIVE_PATH=sys.argv[1] # get path from first argument

trimDict = {}

def fioRun(testName,qd,trds,bs,datOp,runTime,sync):
    testDir=(WORKING_DIR+"/"+testName)
    os.makedirs(testDir,exist_ok=True)
    os.chdir(testDir)
    fioOutput = testDir + "/fioOutput.txt"
    if sync == 'sync':
        os.system(f'sudo fio --bandwidth-log --name=diskBench --ioengine=libaio --direct=1 --fsync=1 --filename={DRIVE_PATH} --rw={datOp} --bs={bs} --iodepth={qd} --numjobs={trds} --output={fioOutput} --runtime={runTime}')
    else:
        if runTime != '0':
            os.system(f'sudo fio --bandwidth-log --name=diskBench --ioengine=libaio --direct=1 --filename={DRIVE_PATH} --rw={datOp} --bs={bs} --iodepth={qd} --numjobs={trds} --output={fioOutput} --runtime={runTime}')
        else:    
            os.system(f'sudo fio --bandwidth-log --name=diskBench --ioengine=libaio --direct=1 --filename={DRIVE_PATH} --rw={datOp} --bs={bs} --iodepth={qd} --numjobs={trds} --output={fioOutput}')

    if datOp in ("read","randread","randrw"):
        copyfile('agg-read_bw.log','fioBandLog.csv')
    else:
        copyfile('agg-write_bw.log','fioBandLog.csv')


def trimDrive():
    print("trimming Drive")
    startTime=time.time()
    os.system(f'sudo blkdiscard -f {DRIVE_PATH}')
    totalTIme = time.time() - startTime
    print(f'Trimming took {totalTIme} seconds')
    return(totalTIme)

def driveIdle():
    print("pausing to give drive time to idle")
    for i in range(IDLE_TIME):
        time.sleep(1)
        print(f'{i} out of {IDLE_TIME}', end='\r')
    
def fillDrive():
    print("filling drive with randomData for full test")
    os.system(f'sudo dd if=/dev/urandom of={DRIVE_PATH} bs=1M status=progress')
    print("filled drive with random data, back to benchmarks")

def runJob(testName,trimFirst,qd,trds,bs,datOp,runTime,sync):
    if trimFirst == '1':
        trimTime = trimDrive()
        trimDict[testName] = trimTime

    driveIdle()
    fioRun(testName,qd,trds,bs,datOp,runTime,sync)
    #print(testName,qd,trds,bs,datOp,runTime,sync)
    print(f'finished {testName} ontto next job')

def runJobList(listOfJobs):
    for i in listOfJobs:

        runJob(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7])


def getSmartData():
    smartPath=(WORKING_DIR+"/"+"smartData.txt")
    os.system(f'sudo smartctl -x {DRIVE_PATH} > {smartPath}')

def getSystemInfo():
    systemInfoPath=(WORKING_DIR+"/"+"sysInfo.txt")
    neoFetchPath=(WORKING_DIR+"/"+"neoFetch.txt")
    os.system(f'neofetch > {neoFetchPath}')
    os.system(f'sudo hwinfo > {systemInfoPath}')

def logTrimTimes():
    csvHeader="driveTest,time"
    trimLogPath=(WORKING_DIR+"/"+"trimTimes.csv")
    with open(trimLogPath, 'w') as file:
        file.write(csvHeader)
        file.write('\n')
        for i in trimDict.keys():
            file.write(f'{i},{trimDict[i]}\n')


def main():

    #trimmed tests first
    runJobList(EMPTY_TESTS)
    fillDrive()
    runJobList(FULL_TESTS)    
    getSmartData()
    getSystemInfo()
    logTrimTimes()

main()



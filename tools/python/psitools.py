import select
import csv
import re
import subprocess


import sys
from DBSAPI.dbsApi import DbsApi
from DBSAPI.dbsException import *
from DBSAPI.dbsApiException import *
from DBSAPI.dbsOptions import DbsOptionParser

def strToNumbers( numString ):
    numbers = []
    if len(numString)==0:
        return numbers;
    
    items = numString.split(',')
    for item in items:
        nums = item.split('-')
        if len(nums) == 1:
            # single number
            numbers.append(int(item))
        elif len(nums) == 2:
            i = int(nums[0])
            j = int(nums[1])
            if i > j:
                raise ValueError('Invalid interval '+item)
            numbers.extend(range(i,j+1))
        else:
            raise ValueError('Argument '+item+' is not valid')

    return set(numbers)


# non blocking read for subprocess.Process.stdout
def readAllSoFar(proc, retVal=''): 
    while (select.select([proc.stdout],[],[],.5)[0]!=[]):   
        c = proc.stdout.read(1)
        if c == '':
            break
        retVal+=c
    return retVal

# helper class to check the command line options against a set of required ones
class ReqOptions:
    def __init__(self, args, required):
        missing = []
        for r in required:
            if r not in args.keys() or args[r] is None:
                missing.append(r)

        if len(missing) != 0:
            raise ValueError('Required option are missing: '+' '.join(missing))

        self.__dict__ = dict(args.items())


class Dataset:
    def __init__(self, id, nick, ver, name):
        self.id = id
        self.nick = nick
        self.ver  = ver
        self.name = name
        self.transfer = False
        self.t0 = None
        self.t1 = None

def getDataSets( csvFile, ids ):
    reader = csv.reader(open(csvFile,'rb'),delimiter=',')
    header = reader.next()
    l = len(header)
    #         print 'header len',l

    datasets = []

    cols = dict(zip(header,range(len(header))))
    print cols
    for row in reader:
        if len(row) != l:
            continue

        d = Dataset(row[cols['ID']],row[cols['Nickname']],row[cols['Skim Version']],row[cols['Output Dataset']])

        numId = int(re.search('[0-9]+',d.id).group(0))
        if len(ids) != 0 and not numId in ids:
            continue

        datasets.append(d);

        if d.ver == '':
            print 'Dataset',d.nick,'doesn\'t have a version number'
            continue

    return datasets

def dbsGetExistingDatasets(version, site):

    cmd=['dbs', 
         'search',
         '--url=http://cmsdbsprod.cern.ch/cms_dbs_ph_analysis_02/servlet/DBSServlet',
         '--query=find dataset where dataset like /*%s* and site like %s' % (version,site)]
    print ' '.join(cmd)
    dbsQuery = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout,stderr) = dbsQuery.communicate()
    outRows = stdout.splitlines()

    # no dataset found
    if len(outRows) == 1:
        return []

    for i in range(4):
        outRows.pop(0)

    print '---'
    print '\n'.join(outRows)
    print '---'

    return outRows

# def dbsGetFileList( dataset ):
#     cmd=['dbs', 
#          'lsf',
#          '--url=http://cmsdbsprod.cern.ch/cms_dbs_ph_analysis_02/servlet/DBSServlet',
#          '--path=%s' % (dataset.name,),
#         ]
#     print ' '.join(cmd)
#     dbsQuery = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     (stdout,stderr) = dbsQuery.communicate()
#     outRows = stdout.splitlines()

#     print '\n'.join(outRows)

def dbsGetFileList( dataset ):
    d = {}
    d['url']='http://cmsdbsprod.cern.ch/cms_dbs_ph_analysis_02/servlet/DBSServlet'
    api = DbsApi( d )
    return [ afile['LogicalFileName'] for afile in api.listLFNs(path=dataset.name) ]
    
def dbsGetDatasetType( dataset ):
    d = {}
    d['url']='http://cmsdbsprod.cern.ch/cms_dbs_ph_analysis_02/servlet/DBSServlet'
    d['quiet']=True
    api = DbsApi( d )
    print api.listDatasetSummary(dataset.name)
    res = api.executeQuery('find datatype where dataset=%s' % dataset.name)
#     print res

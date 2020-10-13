# PYTHON 2

import tkFileDialog
import os
from os import listdir
from os.path import isfile, join, isdir
import sys
import xml.etree.ElementTree
import pprint
import re 
import cPickle as pickle
from operator import attrgetter

# SELECT PROYECT DIR
PROYECT = "full-teaching-experiment"
DIRNAME = "../full-teaching-experiment/docker-compose/full-teaching-env"
PATH = "full-teaching-experiment/src/test/java/"

def getCode(tc):

    with open(PATH + tc['classname'].replace('.','/') + '.java', "rb") as f:

        code = ""
        inMethod = False
        bracket_lvl = 0
        for line in f.readlines():
            if inMethod:
                m = re.findall("{", line)
                bracket_lvl = bracket_lvl + len(m)
                m = re.findall("}", line)
                bracket_lvl = bracket_lvl - len(m)
                code = code + line
                if bracket_lvl == 0:
                    break
            if not inMethod and re.search("void "+tc['name']+"\(.*\).+\{", line) is not None:
                bracket_lvl = 1
                code = code + line
                inMethod = True
        return code.replace("\n", "")+'\n'


output = ""
tcs = dict()
n = 1
if os.path.exists(DIRNAME):
    bugs = [ d for d in listdir(DIRNAME) if isdir(join(DIRNAME,d))]
    for b in bugs:        
        for report in listdir(join(DIRNAME,b)):
            if not isdir(join(DIRNAME,b,report)):
                continue
            current_dir = join(DIRNAME,b,report)
            for f in listdir(current_dir):
                if not f.endswith('.xml'):
                    continue
                root = xml.etree.ElementTree.parse(join(current_dir,f)).getroot()
                for tc in root.iter('testcase'):
                    name = tc.get("name")
                    if not name in tcs:
                        tc_dict = {
                            'id': n,
                            'name': name,
                            'classname': tc.get("classname"),
                            'times': [tc.get("time")],
                            'errors': set()
                        }
                        n=n+1
                        tcs[name] = tc_dict
                    else:
                        tcs[name]['times'].append(tc.get("time"))
                    if tc.find('error') != None:
                        tcs[name]['errors'].add(int(re.search(r'\d+', b).group()))
    fault_matrix = {}
    tcs_list = sorted(tcs.values(), key=lambda k: k['id'])

    with open(PROYECT+"-bbox.txt", "w+") as out:
        for tc in tcs_list:
            tc['time'] = reduce(lambda x, y: float(x) + float(y), tc['times']) / len(tc['times'])
            tc.pop('times', None)
            out.write(getCode(tc))
            for error_id in tc['errors']:
                if not error_id in fault_matrix:
                    fault_matrix[error_id] = [tc['id']]
                else:
                    fault_matrix[error_id].append(tc['id'])
    
    with open( "fault_matrix.pickle", "wb" ) as fm:
        pickle.dump( fault_matrix , fm )
    
    with open( "times.txt", "wb" ) as tm:
        for tc in tcs_list:
            tm.write(str(tc['time'])+'\n')

    pprint.pprint(tcs_list)
    print fault_matrix 

# python py/prioritize.py fullteachingexperimente2e_v0 bbox FAST-pw 50
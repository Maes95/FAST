import subprocess
import tkFileDialog
import os
from os import listdir
from os.path import isfile, join, isdir
import sys
import xml.etree.ElementTree
import pprint
import re 
import cPickle as pickle
import shutil
from operator import attrgetter

class ProcessManager:

    def __init__(self, output):
        self.outfile = output

    def call(self, params, output=None):
        if output is None:
            output=self.outfile
        return subprocess.call(params, shell=True, stdout=output, stderr=self.outfile)

    def runAndGetOutput(self, command):
        text=""
        with open('run', 'w') as out:
            self.call(command, output=out)
        with open('run', 'r') as out:
            text = out.read()
        self.call("rm run")
        return text
    
    def close(self):
        self.outfile.close()

class ExtractorManager:

    def __init__(self, project):
        
        self.project = project
        self.folder_name = self.project['name'].lower()+"_v0"
        self.init_folder = os.getcwd()
        
        if os.path.exists(self.folder_name):
            shutil.rmtree(self.folder_name)
        os.mkdir(self.folder_name)
        
        self.bbox = ""
        self.times= ""
        self.fault_matrix = dict()
        self.tcs = dict()
        self.n=1
        self.pm = ProcessManager(open(join(self.folder_name, 'outputs.log'), 'w+'))
        self.project['n_bugs'] = int(self.pm.runAndGetOutput("defects4j info -p %s | grep 'Number of bugs:' | cut -d':' -f2" % project['name']))
    
    def create_and_test(self, folder, change_version_command):
        print "> Getting version %s" % folder
        if os.path.exists( folder ):
            print "> Project available: %s" % folder
            os.chdir(os.getcwd()+"/"+folder)
        else:
            self.pm.call(change_version_command)
            os.chdir(os.getcwd()+"/"+folder)
            self.pm.call(self.project['build'])
            print "> Running test: %s" % folder
            self.pm.call(self.project['test'])
       

    def getTimesAndBBox(self):
        # GET TIMES AND BBOX

        print "\033[95mProject: %s \033[0m" % self.project['name']

        self.create_and_test(self.project['base_folder'], self.project['base'])

        reports = listdir(self.project['reports_path'])
        #reports.sort()

        for report in reports:
            if report.endswith('.xml'):
                root = xml.etree.ElementTree.parse(join(self.project['reports_path'],report)).getroot()
                suit_name = root.get('name')
                # ADD TIME
                self.times += root.get('time')+'\n'
                # ADD BBOX
                with open(join(self.project['test_path'], suit_name.replace('.','/')+".java"), "r+") as code_file:  
                    self.bbox += code_file.read().replace("\n"," ").replace("\r"," ") +'\n'
                # SAVE TO GET FAULT MATRIX
                self.tcs[suit_name] = {
                    'id': self.n,
                    'name': suit_name
                }
                self.n = self.n+1
        os.chdir(self.init_folder)
    
    def getFaultMatrix(self):
        for n in xrange(self.project['n_bugs']):
            bug_id = n+1 # FIRST BUG 1, NOT 0
            tc_classes = self.pm.runAndGetOutput("defects4j info -p %s -b %d | grep -oP \" \- \K(.+)::\" | cut -d\":\" -f1" % (self.project['name'], bug_id) )

            for tc_class in tc_classes.split('\n'):
                tc_class = tc_class.strip()
                if tc_class in self.tcs.keys():
                    tc_id = self.tcs[tc_class]['id']
                    if not bug_id in self.fault_matrix:
                        self.fault_matrix[bug_id] = [tc_id]
                    else:
                        if not tc_id in self.fault_matrix[bug_id]: # MULTIPLES FAILS IN SAME CLASS
                            self.fault_matrix[bug_id].append(tc_id)

        print(self.fault_matrix)

            # folder = self.project['name'] + "_BUG" +n
            # change_version_command = 'defects4j checkout -p %s -v %db -w %s' % (self.project['name'], n, self.project['name'])
            # self.create_and_test(folder, change_version_command)
            # if n == 3:
            #     break
            # os.chdir(self.init_folder)
            # shutil.rmtree(self.project['name'])

    def save(self):
        with open(join(self.folder_name, self.project['name']+"-bbox.txt"), "w+") as out:
            out.write(self.bbox)
        with open(join(self.folder_name,"times.txt"), "wb" ) as tm:
            tm.write(self.times)

if __name__ == "__main__":

    xxx = {
        'name' : 'Chart',
        'base': 'defects4j checkout -p Chart -v 1f -w ChartBase',
        'base_folder': 'ChartBase',
        'build': 'sed -i \'s/<formatter type=\"plain\" usefile=\"false\"\/>/<formatter type=\"xml\"\/>/g\' ant/build.xml',
        'test'   : 'ant -f ant/build.xml test',
        'reports_path': "build-tests-reports",
        'test_path': "tests"
    }

    em = ExtractorManager(xxx)
    em.getTimesAndBBox()
    em.getFaultMatrix()
    #em.save()
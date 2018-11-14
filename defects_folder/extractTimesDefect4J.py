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
        self.tcs = dict()
        self.n=1
        self.pm = ProcessManager(open(join(self.folder_name, 'outputs.log'), 'w+'))
        self.project['n_bugs'] = int(self.pm.runAndGetOutput("defects4j info -p %s | grep 'Number of bugs:' | cut -d':' -f2" % project['name']))
       

    def getTimesAndBBox(self):
        # GET TIMES AND BBOX

        print "\033[95mProject: %s \033[0m" % project['name']
        print "> Getting project"
        if os.path.exists( project['name'] ):
            print "> Project available"
            os.chdir(os.getcwd()+"/"+project['name'])
        else:
            self.pm.call("defects4j checkout -p Chart -v 1f -w Chart")
            os.chdir(os.getcwd()+"/"+project['name'])
            self.pm.call(project['build'])
            print "> Running test"
            self.pm.call(project['test'])

        reports = listdir(project['reports_path'])
        reports.sort()

        for report in reports:
            if report.endswith('.xml'):
                root = xml.etree.ElementTree.parse(join(project['reports_path'],report)).getroot()
                suit_name = root.get('name')
                # ADD TIME
                self.times += root.get('time')+'\n'
                # ADD BBOX
                with open(join(project['test_path'], suit_name.replace('.','/')+".java"), "r+") as code_file:  
                    self.bbox += code_file.read().replace("\n"," ").replace("\r"," ") +'\n'
                # SAVE TO GET FAULT MATRIX
                self.tcs[suit_name] = {
                    'id': self.n,
                    'name': suit_name
                }
                self.n = self.n+1

    def getFaultMatrix(self):
        pass

    def save(self):
        os.chdir(self.init_folder)
        with open(join(self.folder_name, project['name']+"-bbox.txt"), "w+") as out:
            out.write(self.bbox)
        with open(join(self.folder_name,"times.txt"), "wb" ) as tm:
            tm.write(self.times)

if __name__ == "__main__":

    project={
        'name' : 'Chart',
        'build': 'sed -i \'s/<formatter type=\"plain\" usefile=\"false\"\/>/<formatter type=\"xml\"\/>/g\' ant/build.xml',
        'test'   : 'ant -f ant/build.xml test',
        'reports_path': "build-tests-reports",
        'test_path': "tests"
    }

    em = ExtractorManager(project)
    em.getTimesAndBBox()
    em.save()
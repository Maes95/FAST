import tkFileDialog
import os
from os import listdir
from os.path import isfile, join
import sys
import xml.etree.ElementTree

usage = """USAGE: python tools/getBBox.py <filters>
OPTIONS:
  <filters>: keys like 'unitary' or 'integration' to filter test. You can also concatenate filters"""

keys = [ key for key in sys.argv if not key.endswith('.py')]

def checkKeys(s):
    for key in keys:
        if key in s:
            return True
    return False

# SELECT PROYECT DIR
#dirname = tkFileDialog.askdirectory()
dirname = "/home/michel/Investigacion/full-teaching"

# GET REPORTS
REPORTS_PATH = dirname+"/target/surefire-reports/"
JAVA_PATH = dirname+"/src/test/java/"
output = ""
if os.path.exists(REPORTS_PATH):
    files_in_dir = [ f for f in listdir(REPORTS_PATH) if isfile(join(REPORTS_PATH,f)) and f.endswith('.xml') and checkKeys(f)]
    for f in files_in_dir:
        e = xml.etree.ElementTree.parse(REPORTS_PATH+f).getroot()
        with open(JAVA_PATH+e.get('name').replace('.','/')+".java") as f:
            data = f.read()
            output += "#"+e.get('time')+"#" + data.replace("\n", " ")+'\n'

print output
# path = "fullteachingall_v0"
# name = "fullteachingall"
# fileout = "output-bbox.txt"         
# with open(fileout, "w") as fout:
#     fout.write(output)


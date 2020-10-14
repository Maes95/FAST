import subprocess
import os
from os import listdir
from os.path import join, isdir
import re
import xml.etree.ElementTree
import cPickle as pickle
import sys

WORKDIR = '/home/fast/defects_folder/'

def cmd(command):
    output = ""
    print("\033[95m  > CMD: %s \033[0m" % command)
    try:
        output = subprocess.check_output(
            command, shell=True, stderr=-1)
    except subprocess.CalledProcessError as e:
        output = e.output
    finally:
        return output

class Defects4JFAST:

    @staticmethod
    def allProjects():
        print(" - Get Defects4J projects")
        projects = cmd("defects4j pids")
        not_used = ['Cli', 'Collections', 'Cli',
                    'Codec', 'Compress', 'Gson', 'JacksonCore', 'JacksonXml']
        return [x for x in projects.split('\n') if len(x) > 1 and not x in not_used]

    def __init__(self, project_name, forceUpdate=False):
        print("Init project: %s"%project_name)
        self.project_name = project_name
        self.bbox = ""
        self.times = ""
        self.times_avg = ""
        self.fault_matrix = dict()
        self.tcs = dict()
        self.forceUpdate = forceUpdate

        print(" - Calculate number of bugs")
        self.n_bugs = int(cmd("defects4j bids -p %s | tail -n 1" % self.project_name))

        project_folder = "projects/%s" % self.project_name

        if self.forceUpdate or not isdir(project_folder):
            print(" - Checkout project at %s" % (os.getcwd() + project_folder))
            cmd("rm -rf %s" % project_folder)
            cmd(
                "defects4j checkout -p %s -v 1f -w %s" % (project_name, project_folder))
        else:
            print(" - Using current project folder (%s)" % (os.getcwd() + project_folder))

        self.test_path = join(WORKDIR, project_folder, cmd(
            "cd projects/%s/ && defects4j export -p dir.src.tests" % project_name))
        print(" - Getting test path: %s" % self.test_path)
    
    def runAllTests(self):

        if self.forceUpdate or not isdir("projects/%s/target/test-reports/" % self.project_name):
            print(" - Running all tests")
            # Compile sources
            cmd("cd projects/%s/ && defects4j compile" % self.project_name)
            # Execute all test
            cmd("cd projects/%s/ && defects4j test" % self.project_name)
        else:
            print(" - Using existing data of tests")

    def searchTestFile(self, test_classpath):
        # join(self.test_path, suit_name.replace('.','/')+".java"
        test_path = "src/test/java"
 
        file_name = test_classpath.split('.')[-1]+'.java'
        test_path = [join(dir_, f) for dir_, dirs, files in os.walk(
            self.test_path) for f in files if f == file_name][0]
        return test_path

    def getTestReports(self):

        print(" - Getting test reports (get time and generate bbox file)")

        reports_path = [join(dir_, d) for dir_, dirs, files in os.walk(
            "projects/%s/" % self.project_name) for d in dirs if d == "test-reports"][0]

        reports = listdir(reports_path)
        reports.sort()

        report_index = 1

        for report in reports:
            if report.endswith('.xml'):
                root = xml.etree.ElementTree.parse(
                    join(reports_path, report)).getroot()

                suit_name = root.get('name')

                try:
                    # ADD BBOX
                    with open(self.searchTestFile(suit_name), "r+") as code_file:
                        self.bbox += code_file.read().replace("\n"," ").replace("\r"," ") +'\n'
                     # ADD TIME
                    self.times += root.get('time')+'\n'
                    # SAVE TO GET FAULT MATRIX
                    self.tcs[suit_name.split('.')[-1]] = {
                        'id': report_index,
                        'name': suit_name
                    }
                    report_index += 1
                except IOError as err:
                    # Except when exist a class in another class, i.e. SpecializeModuleTest$SpecializeModuleSpecializationStateTest.java
                    print(
                        "\033[91m  > ERROR: Can't include %s TestCase \033[0m" % suit_name)
                    continue

    def getTestCaseJavaClasses(self, bug_id):
        # defects4j info -p Lang -b 1 | grep -oP " \- \K(.+)::" | cut -d":" -f1
        tc_classes = cmd(
            "defects4j info -p %s -b %d | grep -oP \" \- \K(.+)::\" | cut -d\":\" -f1" % (self.project_name, bug_id))
        return [x for x in tc_classes.split('\n') if len(x) > 1]

    def generateFaultMatrix(self):
        print(" - Generating fault matrix")
        missing_classes = 0
        for n in xrange(self.n_bugs):
            bug_id = n+1  # FIRST BUG 1, NOT 0
            tc_classes = self.getTestCaseJavaClasses(bug_id)

            for tc_class in tc_classes:
                tc_class = tc_class.strip().split('.')[-1]
                if tc_class in self.tcs.keys():
                    tc_id = self.tcs[tc_class]['id']
                    if not bug_id in self.fault_matrix:
                        self.fault_matrix[bug_id] = [tc_id]
                    else:
                        # MULTIPLES FAILS IN SAME CLASS
                        if not tc_id in self.fault_matrix[bug_id]:
                            self.fault_matrix[bug_id].append(tc_id)
                else:
                    missing_classes+=1
                    print(
                        "\033[91m  > ERROR: Can't found class %s for bug %d \033[0m" % (tc_class, bug_id))
        print(" - Bugs: %d | Missing classes: %d" % (self.n_bugs, missing_classes))

    def save(self):
        output_folder = "output/%s"%self.project_name
        if not isdir(output_folder): os.mkdir(output_folder)
        print(" - Saving results at %s"%output_folder)
        with open(join(output_folder, self.project_name.lower()+"-bbox.txt"), "w+") as out:
            out.write(self.bbox)
        with open(join(output_folder, "times.txt"), "wb") as tm:
            tm.write(self.times)
        # with open(join(output_folder, "times_avg.txt"), "wb") as tma:
        #     tma.write(self.times_avg)
        with open(join(output_folder, "fault_matrix.pickle"), "wb") as fm:
            pickle.dump(self.fault_matrix, fm)

if __name__ == "__main__":

    availableProjects = Defects4JFAST.allProjects()

    usage = """ - USAGE: python2 generateInfoD4J.py <project> 
 - AVAILABLE PROJECTS: %s""" % ", ".join(availableProjects)

    if len(sys.argv) != 2 or sys.argv[1] not in availableProjects:
        print(usage)
        exit(1)

    
    os.chdir(WORKDIR)
    project = Defects4JFAST(sys.argv[1])
    # Compile and run all test
    project.runAllTests()
    # Get Test report to:
    # -> Generate bbox file
    # -> Generate times file
    project.getTestReports()
    project.generateFaultMatrix()
    project.save()

    
    
    

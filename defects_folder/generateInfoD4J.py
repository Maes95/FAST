import subprocess
import os
from os import listdir
from os.path import join, isdir
import re
import xml.etree.ElementTree
import cPickle as pickle
import sys

WORKDIR = '/home/fast/defects_folder/'

def cmd(command, silent=False):
    output = ""
    if not silent: print("\033[95m  > CMD: %s \033[0m" % command)
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
        projects = cmd("defects4j pids", silent=True)
        not_used = ['Cli', 'Collections', 'Codec', 'Compress', 'Gson', 'JacksonCore', 'JacksonXml']
        return [x for x in projects.split('\n') if len(x) > 1]

    def __init__(self, project_name, forceUpdate=False, iterations=10):
        print("Init project: %s"%project_name)
        self.project_name = project_name
        self.bbox = ""
        self.times = ""
        self.times_avg = ""
        self.fault_matrix = dict()
        self.tcs = dict()
        self.forceUpdate = forceUpdate
        self.iterations = iterations

        print(" - Calculate number of bugs")
        self.n_bugs = int(cmd("defects4j bids -p %s | tail -n 1" % self.project_name))

        project_folder = "projects/%s" % self.project_name

        if self.forceUpdate or not isdir(project_folder):
            print(" - Checkout project at %s" % join(os.getcwd() + project_folder))
            cmd("rm -rf %s" % project_folder)
            cmd(
                "defects4j checkout -p %s -v 1f -w %s" % (project_name, project_folder))
        else:
            print(" - Using current project folder (%s)" % (os.getcwd() + project_folder))

        self.test_path = join(WORKDIR, project_folder, cmd(
            "cd projects/%s/ && defects4j export -p dir.src.tests" % project_name))
        print(" - Getting test path: %s" % self.test_path)

    def _getSurefireReportsData(self):
        reports_path = [join(dir_, d) for dir_, dirs, files in os.walk("projects/%s/" % self.project_name) for d in dirs if d == "test-reports"][0]
        reports = listdir(reports_path)
        reports.sort()
        xml_reports = []
        for report in reports:
            if report.endswith('.xml'):
                root = xml.etree.ElementTree.parse(join(reports_path, report)).getroot()
                xml_reports.append((root.get('name'), root.get('time')))
        return xml_reports
    
    def runAllTests(self):

        if not self.forceUpdate or isdir("projects/%s/target/test-reports/" % self.project_name):
            print(" - Using existing data of tests")
        else:
            print(" - Running all tests (%d iterations)" % self.iterations)
            # Compile sources
            cmd("cd projects/%s/ && defects4j compile" % self.project_name)

            print(" - Getting test reports (get time and generate bbox file)")

            

            for it in xrange(self.iterations):
                # Execute all test
                cmd("cd projects/%s/ && defects4j test" % self.project_name)  

                report_index = 1
                for suit_name, time in self._getSurefireReportsData():
                    try:
                        # Need to ensure that test file exist (class in class is posible)
                        with open(os.path.join(self.test_path, suit_name.replace('.', '/')+".java"), "r+") as code_file:
                            # ADD BBOX (ONLY IN FIRST ITERATION)
                            if it == 0:
                                self.bbox += code_file.read().replace("\n", " ").replace("\r", " ") + '\n'
                        
                        suit_name_class = suit_name.split('.')[-1]

                        if suit_name_class in self.tcs:
                            self.tcs[suit_name_class]['times'].append(
                                float(time))
                        else:
                            # SAVE TO GET FAULT MATRIX
                            self.tcs[suit_name_class] = {
                                'id': report_index,
                                'name': suit_name,
                                'times': [float(time)]
                            }
                            report_index += 1
                        
                    except IOError as err:
                        # Except when exist a class in another class, i.e. SpecializeModuleTest$SpecializeModuleSpecializationStateTest.java
                        print(
                            "\033[91m  > ERROR: Can't include %s TestCase \033[0m" % suit_name)
                        continue

            tcs_list = self.tcs.values()
            tcs_list.sort(key=lambda tc: tc['id'])

            for tc in tcs_list:
                avg_time = str(sum(tc['times']) / len(tc['times']))
                self.times += avg_time+'\n'

    def getTestCaseJavaClasses(self, bug_id):
        # defects4j info -p Lang -b 1 | grep -oP " \- \K(.+)::" | cut -d":" -f1
        tc_classes = cmd(
            "defects4j info -p %s -b %d | grep -oP \" \- \K(.+)::\" | cut -d\":\" -f1" % (self.project_name, bug_id), silent=True)
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
        with open(join(output_folder, "times_avg.txt"), "wb") as tm:
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
    project = Defects4JFAST(sys.argv[1], forceUpdate=True)
    # Compile and run all test N times
    # -> Get Test report
    # -> Generate bbox file
    # -> Generate times file
    project.runAllTests()
    project.generateFaultMatrix()
    project.save()

    
    
    

import subprocess
import os
import re
import xml.etree.ElementTree

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

class Defects4J:

    @staticmethod
    def allProjects(self):
        projects = cmd("defects4j pids")
        return [x for x in projects.split('\n') if len(x) > 1]

    def __init__(self, project_name, clean=False):
        print("Init project: %s"%project_name)
        self.project_name = project_name
        self.bbox = ""
        self.times = ""
        self.times_avg = ""
        self.fault_matrix = dict()
        self.tcs = dict()

        print(" - Calculate number of bugs")
        self.n_bugs = int(cmd("defects4j bids -p %s | tail -n 1" % self.project_name))

        project_folder = "projects/%s" % self.project_name

        print(" - Getting test path")
        self.test_path = os.path.join(WORKDIR,project_folder,cmd("cd projects/%s/ && defects4j export -p dir.src.tests" % project_name))

        if clean or not os.path.isdir(project_folder):
            print(" - Checkout project at %s" % (os.getcwd() + project_folder))
            cmd("rm -rf %s" % project_folder)
            cmd(
                "defects4j checkout -p %s -v 1f -w %s" % (project_name, project_folder))
        else:
            print(" - Using current project folder (%s)" % (os.getcwd() + project_folder))
    
    def runAllTests(self):
        # Compile sources
        cmd("cd projects/%s/ && defects4j compile" % self.project_name)
        # Execute all test
        cmd("cd projects/%s/ && defects4j test" % self.project_name)

    def getTestReports(self):

        reports_path = "projects/%s/target/test-reports/" % self.project_name
        reports = os.listdir(reports_path)
        reports.sort()

        report_index = 1

        for report in reports:
            if report.endswith('.xml'):
                root = xml.etree.ElementTree.parse(
                    os.path.join(reports_path, report)).getroot()

                suit_name = root.get('name')

                try:
                    # ADD BBOX
                    #print(os.path.join(self.test_path, suit_name.replace('.', '/')+".java"))
                    with open(os.path.join(self.test_path, suit_name.replace('.','/')+".java"), "r+") as code_file:
                        self.bbox += code_file.read().replace("\n"," ").replace("\r"," ") +'\n'
                     # ADD TIME
                    self.times += root.get('time')+'\n'
                    # SAVE TO GET FAULT MATRIX
                    self.tcs[suit_name] = {
                        'id': report_index,
                        'name': suit_name
                    }
                    report_index += 1
                except IOError as err:
                    # Except when exist a class in another class, i.e. SpecializeModuleTest$SpecializeModuleSpecializationStateTest.java
                    print "> Can't include %s TC" % suit_name
                    continue

    def getTestCaseJavaClasses(self, bug_id):
        tc_classes = cmd(
            "defects4j info -p %s -b %d | grep -oP \" \- \K(.+)::\" | cut -d\":\" -f1" % (self.project_name, bug_id))
        return [x for x in tc_classes.split('\n') if len(x) > 1]


if __name__ == "__main__":
    os.chdir(WORKDIR)
    project = Defects4J("Math")
    # Compile and run all test
    project.runAllTests()
    # Get Test report to:
    # -> Generate bbox file
    # -> Genrate times file
    project.getTestReports()
    
    

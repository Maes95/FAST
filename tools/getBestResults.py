import os 
import csv

OUTPUT_FOLDER = 'output/'

project_map = {}

for project in os.listdir('output/'):

    if project.startswith("_"): continue

    project_map[project] = {}

    for algoritm in os.listdir('output/%s/' % project):
        
        with open('output/%s/%s/%s-results.tsv' % (project, algoritm, algoritm), 'r+') as fd:
            
            read_tsv = csv.reader(fd, delimiter="\t")
            
            max_value = 0.0

            for row in read_tsv:

                if row[0] == 'Index': continue # Skip header

                if algoritm == 'FAST-time':
                    APFD_c = float(row[3])
                else:
                    APFD_c = float(row[1])

                if APFD_c > max_value:
                    max_value = APFD_c

            project_map[project][algoritm] = max_value
    
    with open('output/%s/FAST-time/FAST-time-pareto-frontier.csv' % (project), 'r+') as fd:

        read_tsv = csv.reader(fd)

        max_value = 0.0

        for row in read_tsv:

            if row[3] == 'APFD_c': continue  # Skip header

            APFD_c = float(row[3])
            if APFD_c > max_value:
                max_value = APFD_c

            project_map[project]['best_pareto_solution'] = max_value


for project, algorithms in project_map.items():
    print(project)
    for alg, value in algorithms.items():
        print("-> [%s]:%f"%(alg, value))



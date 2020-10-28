import os 
import csv

OUTPUT_FOLDER = 'output/'

project_map = {}

for project in os.listdir('output/'):

    if project.startswith("_"): continue

    project_map[project] = {}

    for algoritm in os.listdir('output/%s/' % project):

        project_map[project][algoritm] = {}

        for it in (50, 100, 500, 1000):
        
            with open('output/%s/%s/%d_iterations/%s-results.tsv' % (project, algoritm, it, algoritm), 'r+') as fd:
                
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

                project_map[project][algoritm][str(it)] = { "max_value": max_value }

            if algoritm == 'FAST-time':
    
                with open('output/%s/%s/%d_iterations/pareto-frontier.csv' % (project, algoritm, it), 'r+') as fd:

                    read_tsv = csv.reader(fd)

                    max_value = 0.0

                    for row in read_tsv:

                        if row[3] == 'APFD_c': continue  # Skip header

                        APFD_c = float(row[3])
                        if APFD_c > max_value:
                            max_value = APFD_c

                        project_map[project][algoritm][str(it)]['best_pareto_solution'] = max_value


fast_filter = {
    'alg': 'FAST-pw',
    'it' : '50'
}

for project, algorithms in project_map.items():
    for alg, iterations in algorithms.items():   
        for it, results in iterations.items():
            if (alg == fast_filter['alg'] and it == fast_filter['it']):
                print("%s   [%s][%s iterations][max_value]: %f" % (project, alg, it, results['max_value']))
                if alg == "FAST-time":
                    print("%s   [%s][%s iterations][best_pareto_solution]: %f" %(project, alg, it, results['best_pareto_solution']))


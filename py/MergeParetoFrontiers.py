import numpy as np
import pandas as pd
import matplotlib
import sys
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import csv

def identify_pareto(scores):
    # Count number of items
    population_size = scores.shape[0]
    # Create a NumPy index for scores on the pareto front (zero indexed)
    population_ids = np.arange(population_size)
    # Create a starting list of items on the Pareto front
    # All items start off as being labelled as on the Parteo front
    pareto_front = np.ones(population_size, dtype=bool)
    # Loop through each item. This will then be compared with all other items
    for i in range(population_size):
        # Loop through all other items
        diss = scores[i][1]
        time = scores[i][2]
        for j in range(population_size):
            # Check if our 'i' point is dominated by out 'j' point
            if (
                (diss < scores[j][1] and time > scores[j][2])
                or
                (diss == scores[j][1] and time > scores[j][2])
                or
                (time == scores[j][2] and diss < scores[j][1])
            ):
                pareto_front[i] = 0
                #print(scores[i],scores[j])
                break
    # Return ids of scenarios on pareto front
    return population_ids[pareto_front]


def get_pareto_frontier_and_plot(results, project):

    data1, data2, data3 = results

    ax = plt.gca()

    colors = ('r', 'b', 'y')
    labels = []

    for idx, data in enumerate(results):

        scores = np.array(data)
        pareto_front = []
        points = []
        pareto = identify_pareto(scores)
        for solution in scores[pareto]:
            point = (solution[1], solution[2], solution[3])
            if point not in points:
                points.append(point)
                pareto_front.append(solution)
        pareto_front_df = pd.DataFrame(pareto_front)
        pareto_front_df.sort_values(1, inplace=True)
        pareto_front = pareto_front_df.values
        pareto_front_df[0] = pareto_front_df[0].astype(int)
        x_all = scores[:, 1]
        y_all = scores[:, 2]
        x_pareto = pareto_front[:, 1]
        y_pareto = pareto_front[:, 2]

        ax.scatter(x_all, y_all, color=colors[idx])
        ax.plot(x_pareto, y_pareto, color=colors[idx])

        patch = mpatches.Patch(
            color=colors[idx], label='%d iterations' % len(scores))
        labels.append(patch)

    plt.xlabel('Dissimilarity')
    plt.ylabel('Time (sec)')
    plt.title("Solutions for project %s" % project)
    plt.show()

    plt.legend(handles=labels)
    plt.savefig("output/_charts/%s.png" % project)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python py/MergeParetoFrontiers.py <project>")
        exit(1)

    project = sys.argv[1]

    data = ()

    for it in (1000, 500, 100):

        data_aux = []

        with open("output/%s/FAST-time/%d_iterations/FAST-time-results.tsv" % (project, it)) as fd:
            tsvreader = csv.reader(fd, delimiter="\t")
            for i, line in enumerate(tsvreader):
                if i is 0:
                    continue
                data_aux.append([int(line[0]), float(line[1]),
                                float(line[2]),  float(line[3])])
        data = data + (data_aux,)

    get_pareto_frontier_and_plot(data, project)


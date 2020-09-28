'''
This file is part of an ICSE'18 submission that is currently under review. 
For more information visit: https://github.com/icse18-FAST/FAST.
    
This is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as 
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this source.  If not, see <http://www.gnu.org/licenses/>.
'''

import math
import os
import pickle
import sys

import competitors
import fast
import metric

import priorTime
import pprint

from pareto import get_pareto_frontier_and_plot


usage = """USAGE: python py/prioritize.py <dataset> <entity> <algorithm> <repetitions>
OPTIONS:
  <dataset>: test suite to prioritize.
    options: flex_v3, grep_v3, gzip_v1, make_v1, sed_v6, closure_v0, lang_v0, math_v0, chart_v0, time_v0
  <entity>: BB or WB (function, branch, line) prioritization.
    options: bbox, function, branch, line
  <algorithm>: algorithm used for prioritization.
    options: FAST-pw, FAST-one, FAST-log, FAST-sqrt, FAST-all, STR, I-TSD, ART-D, ART-F, GT, GA, GA-S
  <repetitions>: number of prioritization to compute.
    options: positive integer value, e.g. 50
NOTE:
  STR, I-TSD are BB prioritization only.
  ART-D, ART-F, GT, GA, GA-S are WB prioritization only."""

# output/<program>_<type>/<alg>/
OUTPUT_FOLDER = "output/{}_{}/{}/"

def bboxPrioritization(name, prog, v, ctype, k, n, r, b, repeats, selsize):
    javaFlag = True if v == "v0" else False

    fin = "input/{}_{}/{}-{}.txt".format(prog, v, prog, ctype)
    if javaFlag:
        fault_matrix = "input/{}_{}/fault_matrix.pickle".format(prog, v)
    else:
        fault_matrix = "input/{}_{}/fault_matrix_key_tc.pickle".format(prog, v)
    outpath = OUTPUT_FOLDER.format(prog, v, name)
    ppath = outpath + "prioritized/"

    timesMap = priorTime.getTimesMap("input/{}_{}/".format(prog, v))

    objective_function_values = []

    if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
        ptimes, stimes, apfds, realDetectionTime, apfds_c = [], [], [], [], []
        for run in xrange(repeats):
            print " Run", run
            # SELECT APROACH
            memory = not javaFlag
            if name == "FAST-" + selsize.__name__[:-1]:
                stime, ptime, prioritization = fast.fast_(
                        fin, selsize, r, b, bbox=True, k=k, memory=memory)
            elif name == "FAST-pw":
                stime, ptime, prioritization = fast.fast_pw(
                        fin, r, b, bbox=True, k=k, memory=memory)
            elif name == "FAST-time":
                stime, ptime, prioritization, dissimilarity_value, time_value = fast.fast_time(
                        fin, r, b, "input/{}_{}/".format(prog, v), bbox=True, k=k, memory=memory)
            elif name == "TIME-FAST":
                stime, ptime, prioritization = fast.time_fast(
                        fin, r, b, "input/{}_{}/".format(prog, v), bbox=True, k=k, memory=memory)
            elif name == "I-TSD":
                stime, ptime, prioritization = competitors.i_tsd(fin)
            elif name == "STR":
                stime, ptime, prioritization = competitors.str_(fin)
            else:
                print("Wrong input.")
                print(usage)
                exit()

            writePrioritization(ppath, name, ctype, run, prioritization)
            apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
            apfd_c = metric.apfd_c(prioritization, fault_matrix, timesMap)
            realDetectionTime = metric.getUsedTime(prioritization, fault_matrix, "input/{}_{}/".format(prog, v))
            apfds.append(apfd)
            apfds_c.append(apfd_c)
            stimes.append(stime)
            ptimes.append(ptime)
            print("  Progress: 100%  ")
            print "  Running time:", stime + ptime
            if javaFlag:
                print "  APFD:", sum(apfds[run]) / len(apfds[run])
            else:
                print "  APFD:", apfd

            # Only for multi-objetive
            if name == "FAST-time":
                objective_function_values.append((dissimilarity_value, time_value, apfd_c))

        rep = (name, stimes, ptimes, apfds, apfds_c, realDetectionTime)
        #writeOutput(outpath, ctype, rep, javaFlag)
        writeOutputWithTestTime(outpath, ctype, rep, javaFlag)
        print("")

        # Save all solutions
        outpath = OUTPUT_FOLDER.format(prog, v, name)
        fileout = "{}/{}-{}.tsv".format(outpath, name, 'results')
        with open(fileout, "w") as fout:

            # Only for multi-objetive
            if name == "FAST-time":
                solutions = []
                fout.write("Index\tDissimilarity\tTime\tAPFD_c\n")
                for idx, (dissimilarity_value, time_value, apfd_c) in enumerate(objective_function_values):
                    fout.write("{}\t{}\t{}\t{}\n".format(
                        idx, dissimilarity_value, time_value,  sum(apfd_c)/len(apfd_c)))
                    solutions.append(
                        [idx, dissimilarity_value, time_value,  sum(apfd_c)/len(apfd_c)])
                # Generate and save pareto frontier and graphic
                get_pareto_frontier_and_plot(solutions, "{}_{}".format(prog, v), name)
            
            # Others algorithms
            else: 
                fout.write("Index\tAPFD_c\n")
                for idx, apfd_c in enumerate(apfds_c):
                    fout.write("{}\t{}\n".format( idx, sum(apfd_c)/len(apfd_c)))
    else:
        print name, "already run."

def wboxPrioritization(name, prog, v, ctype, n, r, b, repeats, selsize):
    javaFlag = True if v == "v0" else False

    fin = "input/{}_{}/{}-{}.txt".format(prog, v, prog, ctype)
    if javaFlag:
        fault_matrix = "input/{}_{}/fault_matrix.pickle".format(prog, v)
    else:
        fault_matrix = "input/{}_{}/fault_matrix_key_tc.pickle".format(prog, v)

    outpath = OUTPUT_FOLDER .format(prog, v, name)
    ppath = outpath + "prioritized/"

    if name == "GT":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in xrange(repeats):
                print " Run", run
                stime, ptime, prioritization = competitors.gt(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print "  Running time:", stime + ptime
                if javaFlag:
                    print "  APFD:", sum(apfds[run]) / len(apfds[run])
                else:
                    print "  APFD:", apfd
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print name, "already run."

    elif name == "FAST-" + selsize.__name__[:-1]:
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in xrange(repeats):
                print " Run", run
                if javaFlag:
                    stime, ptime, prioritization = fast.fast_(
                        fin, selsize, r=r, b=b, memory=False)
                else:
                    stime, ptime, prioritization = fast.fast_(
                        fin, selsize, r=r, b=b, memory=True)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print "  Running time:", stime + ptime
                if javaFlag:
                    print "  APFD:", sum(apfds[run]) / len(apfds[run])
                else:
                    print "  APFD:", apfd
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print name, "already run."

    elif name == "FAST-pw":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in xrange(repeats):
                print " Run", run
                if javaFlag:
                    stime, ptime, prioritization = fast.fast_pw(fin, r, b)
                else:
                    stime, ptime, prioritization = fast.fast_pw(
                        fin, r, b, memory=True)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print "  Running time:", stime + ptime
                if javaFlag:
                    print "  APFD:", sum(apfds[run]) / len(apfds[run])
                else:
                    print "  APFD:", apfd
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print name, "already run."

    elif name == "GA":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in xrange(repeats):
                print " Run", run
                stime, ptime, prioritization = competitors.ga(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print "  Running time:", stime + ptime
                if javaFlag:
                    print "  APFD:", sum(apfds[run]) / len(apfds[run])
                else:
                    print "  APFD:", apfd
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print name, "already run."

    elif name == "GA-S":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in xrange(repeats):
                print " Run", run
                stime, ptime, prioritization = competitors.ga_s(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print "  Running time:", stime + ptime
                if javaFlag:
                    print "  APFD:", sum(apfds[run]) / len(apfds[run])
                else:
                    print "  APFD:", apfd
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print name, "already run."

    elif name == "ART-D":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in xrange(repeats):
                print " Run", run
                stime, ptime, prioritization = competitors.artd(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print "  Running time:", stime + ptime
                if javaFlag:
                    print "  APFD:", sum(apfds[run]) / len(apfds[run])
                else:
                    print "  APFD:", apfd
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print name, "already run."

    elif name == "ART-F":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in xrange(repeats):
                print " Run", run
                stime, ptime, prioritization = competitors.art_f(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print "  Running time:", stime + ptime
                if javaFlag:
                    print "  APFD:", sum(apfds[run]) / len(apfds[run])
                else:
                    print "  APFD:", apfd
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print name, "already run."

    else:
        print("Wrong input.")
        print(usage)
        exit()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def writePrioritization(path, name, ctype, run, prioritization):
    fout = "{}/{}-{}-{}.pickle".format(path, name, ctype, run+1)
    pickle.dump(prioritization, open(fout, "wb"))

def writeContextAwarePrioritization(path, name, ctype, run, context_aware_matrix):
    pprint.pprint(context_aware_matrix)


def writeOutput(outpath, ctype, res, javaFlag):
    if javaFlag:
        name, stimes, ptimes, apfds = res
        fileout = "{}/{}-{}.tsv".format(outpath, name, ctype)
        with open(fileout, "w") as fout:
            fout.write("SignatureTime\tPrioritizationTime\tAPFD\n")
            for st, pt, apfdlist in zip(stimes, ptimes, apfds):
                for apfd in apfdlist:
                    tsvLine = "{}\t{}\t{}\n".format(st, pt, apfd)
                    fout.write(tsvLine)
    else:
        name, stimes, ptimes, apfds = res
        fileout = "{}/{}-{}.tsv".format(outpath, name, ctype)
        with open(fileout, "w") as fout:
            fout.write("SignatureTime\tPrioritizationTime\tAPFD\n")
            for st, pt, apfd in zip(stimes, ptimes, apfds):
                tsvLine = "{}\t{}\t{}\n".format(st, pt, apfd)
                fout.write(tsvLine)

def writeOutputWithTestTime(outpath, ctype, res, javaFlag):
    if javaFlag:
        name, stimes, ptimes, apfds, apfds_c, testTimes = res
        fileout = "{}/{}-{}.tsv".format(outpath, name, ctype)
        with open(fileout, "w") as fout:
            fout.write("SignatureTime\tPrioritizationTime\tAPFD\tAPFD_c\tTimeToDetect\n")
            for st, pt, apfdlist, apfds_c_list in zip(stimes, ptimes, apfds, apfds_c):
                for idx, apfd in enumerate(apfdlist):
                    time = testTimes[idx]
                    tsvLine = "{}\t{}\t{}\t{}\t{}\n".format(st, pt, apfd, apfds_c_list[idx], time)
                    fout.write(tsvLine)
    else:
        name, stimes, ptimes, apfds = res
        fileout = "{}/{}-{}.tsv".format(outpath, name, ctype)
        with open(fileout, "w") as fout:
            fout.write("SignatureTime\tPrioritizationTime\tAPFD\n")
            for st, pt, apfd in zip(stimes, ptimes, apfds):
                tsvLine = "{}\t{}\t{}\n".format(st, pt, apfd)
                fout.write(tsvLine)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Wrong input.")
        print(usage)
        exit()
    prog_v, entity, algname, repeats = sys.argv[1:]

    repeats = int(repeats)
    algnames = {"FAST-pw", "FAST-one", "FAST-log", "FAST-sqrt", "FAST-all",
                "STR", "I-TSD",
                "ART-D", "ART-F", "GT", "GA", "GA-S", "FAST-time", "FAST-time-mem", "TIME-FAST"}
    prog_vs = {"flex_v3", "grep_v3", "gzip_v1", "make_v1", "sed_v6",
               "closure_v0", "lang_v0", "math_v0", "chart_v0", "time_v0", 
               "fullteaching_v0", "fullteachingint_v0","fullteachingall_v0", "fullteachingexperimente2e_v0","kurento_v0"}
    entities = {"bbox", "function", "branch", "line"}

    if prog_v not in prog_vs:
        print("<dataset> input incorrect.")
        print(usage)
        exit()
    elif entity not in entities:
        print("<entity> input incorrect.")
        print(usage)
        exit()
    elif algname not in algnames:
        print("<algorithm> input incorrect.")
        print(usage)
        exit()
    elif repeats <= 0:
        print("<repetitions> input incorrect.")
        print(usage)
        exit()

    prog, v = prog_v.split("_")

    directory = OUTPUT_FOLDER .format(prog, v, algname)
    if not os.path.exists(directory):
        os.makedirs(directory)
    directory += "prioritized/"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # FAST parameters
    k, n, r, b = 5, 10, 1, 10

    # FAST-f sample size
    if algname == "FAST-all":
        def all_(x): return x
        selsize = all_
    elif algname == "FAST-sqrt":
        def sqrt_(x): return int(math.sqrt(x)) + 1
        selsize = sqrt_
    elif algname == "FAST-log":
        def log_(x): return int(math.log(x, 2)) + 1
        selsize = log_
    elif algname == "FAST-one":
        def one_(x): return 1
        selsize = one_
    else:
        def pw(x): pass
        selsize = pw

    if entity == "bbox":
        bboxPrioritization(algname, prog, v, entity, k, n, r, b, repeats, selsize)
    else:
        wboxPrioritization(algname, prog, v, entity, n, r, b, repeats, selsize)

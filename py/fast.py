# -*- coding: UTF-8 -*-
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

from collections import defaultdict
from collections import OrderedDict
from struct import pack, unpack
import os
import random
import sys
import time
import priorTime

import lsh


def loadTestSuite(input_file, bbox=False, k=5):
    """INPUT
    (str)input_file: path of input file

    OUTPUT
    (dict)TS: key=tc_ID, val=set(covered lines)
    """
    TS = defaultdict()
    with open(input_file) as fin:
        tcID = 1
        for tc in fin:
            if bbox:
                TS[tcID] = tc[:-1]
            else:
                TS[tcID] = set(tc[:-1].split())
            tcID += 1
    shuffled = TS.items()
    random.shuffle(shuffled)
    TS = OrderedDict(shuffled)
    if bbox:
        TS = lsh.kShingles(TS, k)
    return TS


def storeSignatures(input_file, sigfile, hashes, bbox=False, k=5):
    with open(sigfile, "w") as sigfile:
        with open(input_file) as fin:
            tcID = 1
            for tc in fin:
                if bbox:
                    # shingling
                    tc_ = tc[:-1]
                    tc_shingles = set()
                    for i in xrange(len(tc_) - k + 1):
                        tc_shingles.add(hash(tc_[i:i + k]))

                    sig = lsh.tcMinhashing((tcID, set(tc_shingles)), hashes)
                else:
                    tc_ = tc[:-1].split()
                    sig = lsh.tcMinhashing((tcID, set(tc_)), hashes)
                for hash_ in sig:
                    sigfile.write(repr(unpack('>d', hash_)[0]))
                    sigfile.write(" ")
                sigfile.write("\n")
                tcID += 1


def loadSignatures(input_file):
    """INPUT
    (str)input_file: path of input file

    OUTPUT
    (dict)TS: key=tc_ID, val=set(covered lines), sigtime"""
    sig = {}
    start = time.clock()
    with open(input_file, "r") as fin:
        tcID = 1
        for tc in fin:
            sig[tcID] = [pack('>d', float(i)) for i in tc[:-1].split()]
            tcID += 1
    return sig, time.clock() - start

def generate_minhashes(input_file, bbox, memory, n, k):
    hashes = [lsh.hashFamily(i) for i in xrange(n)]

    if memory:
        test_suite = loadTestSuite(input_file, bbox=bbox, k=k)
        # generate minhashes signatures
        mh_t = time.clock()
        tcs_minhashes = {tc[0]: lsh.tcMinhashing(tc, hashes)
                         for tc in test_suite.items()}
        mh_time = time.clock() - mh_t
        ptime_start = time.clock()

    else:
        # loading input file and generating minhashes signatures
        sigfile = input_file.replace(".txt", ".sig")
        sigtimefile = "{}_sigtime.txt".format(input_file.split(".")[0])
        if not os.path.exists(sigfile):
            mh_t = time.clock()
            storeSignatures(input_file, sigfile, hashes, bbox, k)
            mh_time = time.clock() - mh_t
            with open(sigtimefile, "w") as fout:
                fout.write(repr(mh_time))
        else:
            with open(sigtimefile, "r") as fin:
                mh_time = eval(fin.read().replace("\n", ""))

        ptime_start = time.clock()
        tcs_minhashes, _ = loadSignatures(sigfile)
    
    return hashes, tcs_minhashes, mh_time, ptime_start

def dissimilarity_obj_fun(prioritized_tcs, tcs_minhashes):

    # Get first TC
    checked_tcs = [prioritized_tcs.pop()]

    total_dist = 0

    while len(prioritized_tcs) > 0:
        
        # Get next TC
        current_tc = prioritized_tcs.pop()

        # Get average distance from others TCs
        acc_dist = 0
        for tc in checked_tcs:
            acc_dist += lsh.jDistanceEstimate(
                        tcs_minhashes[current_tc], tcs_minhashes[tc])
        
        total_dist += acc_dist / len(checked_tcs)
        
        # Add to checked TCs to compare with the next
        checked_tcs.append(current_tc)
    
    # Return average distance

    return total_dist / len(checked_tcs)

def time_obj_fun(prioritized_tcs, times):

    median = len(prioritized_tcs) / 2

    total_time_at_median = 0

    for i in xrange(median):
        total_time_at_median += times[prioritized_tcs[i]]
    
    return total_time_at_median


def fast(input_file, r, b, sel_fun, times=None, bbox=False, k=5, memory=False, sub_set=[]):
    """INPUT
    (str)input_file: path of input file
    (int)r: number of rows
    (int)b: number of bands
    (bool)bbox: True if BB prioritization
    (int)k: k-shingle size (for BB prioritization)
    (bool)memory: if True keep signature in memory and do not store them to file

    OUTPUT
    (list)P: prioritized test suite
    """
    n = r * b  # number of hash functions

    hashes, tcs_minhashes, mh_time, ptime_start = generate_minhashes(input_file, bbox, memory, n, k)

    tcs_minhashes_original = tcs_minhashes.copy()

    if len(sub_set)>0:
        # ALLOW US TO APPLY FAST ONLY IN A SUBSET OF TCS
        tcs_minhashes = dict((k,tcs_minhashes[k]) for k in sub_set if k in tcs_minhashes)

    tcs = set(tcs_minhashes.keys())

    BASE = 0.5
    SIZE = int(len(tcs)*BASE) + 1

    bucket = lsh.LSHBucket(tcs_minhashes.items(), b, r, n)

    prioritized_tcs = [0]

    # First TC
    selected_tcs_minhash = lsh.tcMinhashing((0, set()), hashes)
    first_tc = random.choice(tcs_minhashes.keys())
    for i in xrange(n):
        if tcs_minhashes[first_tc][i] < selected_tcs_minhash[i]:
            selected_tcs_minhash[i] = tcs_minhashes[first_tc][i]
    prioritized_tcs.append(first_tc)
    tcs -= set([first_tc])
    del tcs_minhashes[first_tc]

    iteration, total = 0, float(len(tcs_minhashes))
    while len(tcs_minhashes) > 0:
        iteration += 1
        if iteration % 100 == 0:
            sys.stdout.write("  Progress: {}%\r".format(
                round(100*iteration/total, 2)))
            sys.stdout.flush()

        if len(tcs_minhashes) < SIZE:
            bucket = lsh.LSHBucket(tcs_minhashes.items(), b, r, n)
            SIZE = int(SIZE*BASE) + 1

        sim_cand = lsh.LSHCandidates(bucket, (0, selected_tcs_minhash),
                                     b, r, n)
        filtered_sim_cand = sim_cand.difference(prioritized_tcs)
        candidates = tcs - filtered_sim_cand

        if len(candidates) == 0:
            selected_tcs_minhash = lsh.tcMinhashing((0, set()), hashes)
            sim_cand = lsh.LSHCandidates(bucket, (0, selected_tcs_minhash),
                                         b, r, n)
            filtered_sim_cand = sim_cand.difference(prioritized_tcs)
            candidates = tcs - filtered_sim_cand
            if len(candidates) == 0:
                candidates = tcs_minhashes.keys()
        
        sel_fun(candidates, tcs_minhashes, selected_tcs_minhash, prioritized_tcs, tcs, n, times)

    ptime = time.clock() - ptime_start

    # Calculate dissimilarity of prioritization
    dissimilarity = dissimilarity_obj_fun(prioritized_tcs[1:], tcs_minhashes_original)

    return mh_time, ptime, prioritized_tcs[1:], dissimilarity

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# lsh + pairwise comparison with candidate set
def fast_pw(input_file, r, b, bbox=False, k=5, memory=False):
    """INPUT
    (str)input_file: path of input file
    (int)r: number of rows
    (int)b: number of bands
    (bool)bbox: True if BB prioritization
    (int)k: k-shingle size (for BB prioritization)
    (bool)memory: if True keep signature in memory and do not store them to file

    OUTPUT
    (list)P: prioritized test suite
    """

    # ▼ DEFINE SELECTION FUNCTION ▼
    def pw_fn(candidates, tcs_minhashes, selected_tcs_minhash, prioritized_tcs, tcs, n, times):
        selected_tc, max_dist = random.choice(tuple(candidates)), -1
        for candidate in tcs_minhashes:
            if candidate in candidates:
                dist = lsh.jDistanceEstimate(
                    selected_tcs_minhash, tcs_minhashes[candidate])
                if dist > max_dist:
                    selected_tc, max_dist = candidate, dist

        for i in xrange(n):
            if tcs_minhashes[selected_tc][i] < selected_tcs_minhash[i]:
                selected_tcs_minhash[i] = tcs_minhashes[selected_tc][i]

        prioritized_tcs.append(selected_tc)
        tcs -= set([selected_tc])
        del tcs_minhashes[selected_tc]
    # ▲ DEFINE SELECTION FUNCTION ▲

    
    mh_time, ptime, prioritized_tcs, _ = fast(input_file, r, b, pw_fn, times=None, bbox=False, k=5, memory=False)
    return mh_time, ptime, prioritized_tcs



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def cluster(data, maxgap):
    '''Arrange data into groups where successive elements
       differ by no more than *maxgap*

        >>> cluster([1, 6, 9, 100, 102, 105, 109, 134, 139], maxgap=10)
        [[1, 6, 9], [100, 102, 105, 109], [134, 139]]

        >>> cluster([1, 6, 9, 99, 100, 102, 105, 134, 139, 141], maxgap=10)
        [[1, 6, 9], [99, 100, 102, 105], [134, 139, 141]]

    '''
    data.sort(key=lambda tup: tup[1])
    groups = [[data[0]]]
    for x in data[1:]:
        if abs(x[1] - groups[-1][-1][1]) <= maxgap:
            groups[-1].append(x)
        else:
            groups.append([x])
    return groups




# REMOVE ON END EXPERIMENT
import metric 
import numpy as np
from scipy.cluster.vq import kmeans, vq
from operator import itemgetter

def cluster2(data, n_clusters):

    d = np.array([(x[1]) for x in data])

    codebook, _ = kmeans(d, n_clusters)
    cluster_indices, _ = vq(d, codebook)

    groups = [ [] for _ in xrange(n_clusters)]

    for idx, i in enumerate(cluster_indices):
        groups[i].append(data[idx])

    groups.sort(key=lambda x: 0 if len(x)==0 else x[0][1])

    return [x for x in groups if x != []]

def time_fast(input_file, r, b, path, bbox=False, k=5, memory=False, num_clusters=72,fault_matrix=[]):
    """INPUT
    (str)input_file: path of input file
    (int)r: number of rows
    (int)b: number of bands
    (bool)bbox: True if BB prioritization
    (int)k: k-shingle size (for BB prioritization)
    (bool)memory: if True keep signature in memory and do not store them to file

    OUTPUT
    (list)P: prioritized test suite
    """
    times = priorTime.getTimesMap(path)

    # ▼ DEFINE SELECTION FUNCTION ▼
    def pw_fn(candidates, tcs_minhashes, selected_tcs_minhash, prioritized_tcs, tcs, n, times):
        selected_tc, max_dist = random.choice(tuple(candidates)), -1
        for candidate in tcs_minhashes:
            if candidate in candidates:
                dist = lsh.jDistanceEstimate(
                    selected_tcs_minhash, tcs_minhashes[candidate])
                if dist > max_dist:
                    selected_tc, max_dist = candidate, dist

        for i in xrange(n):
            if tcs_minhashes[selected_tc][i] < selected_tcs_minhash[i]:
                selected_tcs_minhash[i] = tcs_minhashes[selected_tc][i]

        prioritized_tcs.append(selected_tc)
        tcs -= set([selected_tc])
        del tcs_minhashes[selected_tc]
    # ▲ DEFINE SELECTION FUNCTION ▲

    groups = cluster2(times.items(), num_clusters)
    prioritization = []
    mh_times = []
    ptimes = []
    for g in groups:
        g_subset = [x[0] for x in g]
        mh_time, ptime, sub_prioritization = fast(input_file, r, b, pw_fn, times=times, bbox=False, k=5, memory=False, sub_set=g_subset)
        mh_times.append(mh_time)
        ptimes.append(ptime)
        prioritization = prioritization + sub_prioritization

    return sum(mh_times), sum(ptimes), prioritization


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# lsh + pairwise comparison with candidate set
def fast_time(input_file, r, b, path, bbox=False, k=5, memory=False):
    """INPUT
    (str)input_file: path of input file
    (int)r: number of rows
    (int)b: number of bands
    (str)path: path to times
    (bool)bbox: True if BB prioritization
    (int)k: k-shingle size (for BB prioritization)
    (bool)memory: if True keep signature in memory and do not store them to file

    OUTPUT
    (list)P: prioritized test suite
    """

    times = priorTime.getTimesMap(path)

    # ▼ DEFINE SELECTION FUNCTION ▼
    def time_fn(candidates, tcs_minhashes, selected_tcs_minhash, prioritized_tcs, tcs, n, times):
        selected_tc = random.choice(tuple(candidates))
        for candidate in candidates:
            if times[candidate] < times[selected_tc]:
                selected_tc = candidate

        for i in xrange(n):
            if tcs_minhashes[selected_tc][i] < selected_tcs_minhash[i]:
                selected_tcs_minhash[i] = tcs_minhashes[selected_tc][i]

        prioritized_tcs.append(selected_tc)
        tcs -= set([selected_tc])
        del tcs_minhashes[selected_tc]
    # ▲ DEFINE SELECTION FUNCTION ▲
        
    mh_time, ptime, prioritized_tcs, dissimilarity_value = fast(input_file, r, b, time_fn, times=times, bbox=False, k=5, memory=False)

    time_value = time_obj_fun(prioritized_tcs, times)

    # print("  Dissimilarity: #%f#"%dissimilarity_value)
    # print("  Time         : #%f#"%time_value)

    return mh_time, ptime, prioritized_tcs, dissimilarity_value, time_value


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def fast_(input_file, selsize, r, b, bbox=False, k=5, memory=False):
    """INPUT
    (str)input_file: path of input file
    (fun)selsize: size of candidate set
    (int)r: number of rows
    (int)b: number of bands
    (bool)bbox: True if BB prioritization
    (int)k: k-shingle size (for BB prioritization)
    (bool)memory: if True keep signature in memory and do not store them to file

    OUTPUT
    (list)P: prioritized test suite
    """
    # ▼ DEFINE SELECTION FUNCTION ▼
    def sel_fn(candidates, tcs_minhashes, selected_tcs_minhash, prioritized_tcs, tcs, n, times):
        to_sel = min(selsize(len(candidates)), len(candidates))
        selected_tc_set = random.sample(tuple(candidates), to_sel)

        for selected_tc in selected_tc_set:
            for i in xrange(n):
                if tcs_minhashes[selected_tc][i] < selected_tcs_minhash[i]:
                    selected_tcs_minhash[i] = tcs_minhashes[selected_tc][i]

            prioritized_tcs.append(selected_tc)
            tcs -= set([selected_tc])
            del tcs_minhashes[selected_tc]
    # ▲ DEFINE SELECTION FUNCTION ▲

    mh_time, ptime, prioritized_tcs, _ = fast(input_file, r, b, sel_fn, times=None, bbox=False, k=5, memory=False)
    return mh_time, ptime, prioritized_tcs

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
from pickle import load
import os
import priorTime


def apfd(prioritization, fault_matrix, javaFlag):
    """INPUT:
    (list)prioritization: list of prioritization of test cases
    (str)fault_matrix: path of fault_matrix (pickle file)
    (bool)javaFlag: True if output for Java fault_matrix

    OUTPUT:
    (float)APFD = 1 - (sum_{i=1}^{m} t_i / n*m) + (1 / 2n)
    n = number of test cases
    m = number of faults detected
    t_i = position of first test case revealing fault i in the prioritization
    Average Percentage of Faults Detected
    """

    if javaFlag:
        # key=version, val=[faulty_tcs]
        faults_dict = getFaultDetected(fault_matrix)
        apfds = []
        for v in faults_dict.keys():
            faulty_tcs = set(faults_dict[v])
            numerator = 0.0  # numerator of APFD
            position = 1
            m = 0.0
            for tc_ID in prioritization:
                if tc_ID in faulty_tcs:
                    numerator, m = position, 1.0
                    break
                position += 1

            n = len(prioritization)
            apfd = 1.0 - (numerator / (n * m)) + (1.0 / (2 * n)) if m > 0 else 0.0
            apfds.append(apfd)

        return apfds

    else:
        # dict: key=tcID, val=[detected faults]
        faults_dict = getFaultDetected(fault_matrix)
        detected_faults = set()
        numerator = 0.0  # numerator of APFD
        position = 1
        for tc_ID in prioritization:
            for fault in faults_dict[tc_ID]:
                if fault not in detected_faults:
                    detected_faults.add(fault)
                    numerator += position
            position += 1

        n, m = len(prioritization), len(detected_faults)
        apfd = 1.0 - (numerator / (n * m)) + (1.0 / (2 * n)) if m > 0 else 0.0

        return apfd

def apfd_c(prioritization, fault_matrix, timesMap, batches=None):
    """INPUT:
    (list)prioritization: list of prioritization of test cases
    (str)fault_matrix: path of fault_matrix (pickle file)

    OUTPUT:
    (float)APFD = 1 - (sum_{i=1}^{m} t_i / n*m) + (1 / 2n)
    n = number of test cases
    m = number of faults detected
    t_i = position of first test case revealing fault i in the prioritization
    Average Percentage of Faults Detected
    """

    cost_map = {}
    if batches is not None:
        for batch in batches:
            if len(batch) is 0: continue
            maxTime = max(list(map(lambda t: timesMap[t], batch))) 
            for tc in batch:
                cost_map[tc] = maxTime/len(batch)
    else:
        cost_map = timesMap  

    # key=version, val=[faulty_tcs]
    faults_dict = getFaultDetected(fault_matrix)
    apfds_c = []
    for i in faults_dict.keys():
        faulty_tcs = set(faults_dict[i])
        
        TF_i = 1
        m = 0.0

        # Get first test that detects fault 'i'
        TF_i_pos = 0
        for tc_ID in prioritization:
            if tc_ID in faulty_tcs:
                m = 1.0
                break
            TF_i += 1
            TF_i_pos += 1
        
        n = len(prioritization)
        numerator = 0.0
        j=TF_i_pos
        while(j<n):
            tc_j = prioritization[j]
            numerator += cost_map[tc_j]
            j += 1
        
        total_time = sum(cost_map.values())
        
        apfd = (numerator- (0.5 * cost_map[TF_i] ))/(total_time*m) if m > 0 else 0.0

        apfds_c.append(apfd)

    return apfds_c

def getUsedTime(prioritization, fault_matrix, times_path):
    faults_dict = getFaultDetected(fault_matrix)
    usedTimes = []
    timesMap = priorTime.getTimesMap(times_path)
    for v in xrange(1, len(faults_dict)+1):
        faulty_tcs = set(faults_dict[v])
        position = 1
        usedTime = 0
        acum = 0
        for tc_ID in prioritization:
            acum += timesMap[tc_ID]
            if tc_ID in faulty_tcs:
                usedTime = acum
                break
            position += 1

        usedTimes.append(usedTime)

    return usedTimes

def getUsedTimeParallel(batches, fault_matrix, times_path):
    faults_dict = getFaultDetected(fault_matrix)
    usedTimes = []
    timesMap = priorTime.getTimesMap(times_path)
    for v in faults_dict.keys():
        faulty_tcs = set(faults_dict[v])
        acum = 0
        
        for batch in batches:
            min_time = None
            max_batch=0
            for tc_ID in batch:
                if timesMap[tc_ID] > max_batch:
                    max_batch = timesMap[tc_ID]
                if tc_ID in faulty_tcs:
                    if min_time is None or timesMap[tc_ID] < min_time:
                        min_time = timesMap[tc_ID]
            if min_time is not None:
                usedTimes.append(acum+min_time)
                break
            else:
                acum += max_batch

    return usedTimes


def getFaultDetected(fault_matrix):
    """INPUT:
    (str)fault_matrix: path of fault_matrix (pickle file)

    OUTPUT:
    (dict)faults_dict: key=tcID, val=[detected faults]
    """
    faults_dict = defaultdict(list)

    if not os.path.exists(fault_matrix): 
        faults_dict = { 1: []}
    else:
        with open(fault_matrix, "rb") as picklefile:
            pickledict = load(picklefile)
        for key in pickledict.keys():
            faults_dict[int(key)] = pickledict[key]

    

    return faults_dict

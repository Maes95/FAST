import time as libtime

def splitArr(arr, size):
    arrs = []
    while len(arr) > size:
        pice = arr[:size]
        arrs.append(pice)
        arr   = arr[size:]
    arrs.append(arr)
    return arrs

def getTimesMap(path):
    with open(path+"times.txt") as tfile:
        times = dict()
        n=1
        for line in tfile.readlines():
            times[n] = float(line) 
            n=n+1
        return times

def priorByTime(prioritization, path, box_size=3):

    start = libtime.clock()

    times = getTimesMap(path)

    boxes = []
    split_list = splitArr(prioritization,box_size)
    last = []

    for box in split_list:
        time = sum([times[tc] for tc in box],0)
        
        # # APROACH 1
        # if len(box) == 1:
        #     time = time*3
        # elif len(box) == 2:
        #     time = time*1.5
        

        # APROACH 2

        if len(box) is box_size:
            boxes.append({
                "tcs": sorted(box, key=lambda tc: times[tc]),
                'time': time
            })
        else:
            last = sorted(box, key=lambda tc: times[tc])

    boxes = sorted(boxes, key=lambda x: x['time'])

    return libtime.clock()-start, sum([box['tcs'] for box in boxes], []) + last
    

if __name__ == "__main__":
    print priorByTime([5, 7, 6, 8, 2, 4, 3, 1],"input/fullteachingexperimente2e_v0/")
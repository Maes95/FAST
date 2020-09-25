import sys
import random

if len(sys.argv) != 4:
    print("USAGE: python tools/generate-times.py <number_of_test> <min_time> <max_time>")
    exit()

number_of_test = int(sys.argv[1])
min_time = int(sys.argv[2])
max_time=int(sys.argv[3])

for i in range(number_of_test):

    time = random.randrange(min_time, max_time)
    print(time)

# python tools/generate-times.py 221 10 1800 > input/closure_v0/times_avg.txt

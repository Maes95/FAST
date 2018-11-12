import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

fast_one = pd.read_csv('output/fullteachingexperimente2e_v0/FAST-one-bbox.tsv', sep='\t')
fast_time = pd.read_csv('output/fullteachingexperimente2e_v0/FAST-time-bbox.tsv', sep='\t')
fast_pw = pd.read_csv('output/fullteachingexperimente2e_v0/FAST-pw-bbox.tsv', sep='\t')

a = pd.DataFrame()
a["FAST_ONE"] = fast_one['APFD']
a["FAST_TIME"] = fast_time['APFD']
a["FAST_PW"] = fast_pw['APFD']

boxplot = a.boxplot(column=["FAST_ONE","FAST_TIME","FAST_PW"])

plt.title('COMPARE APFD')
plt.show()

b = pd.DataFrame()
b["FAST_ONE"] = fast_one['PrioritizationTime']
b["FAST_TIME"] = fast_time['PrioritizationTime']
b["FAST_PW"] = fast_pw['PrioritizationTime']

boxplot = b.boxplot(column=["FAST_ONE","FAST_TIME","FAST_PW"])

plt.title('COMPARE PrioritizationTime')
plt.show()
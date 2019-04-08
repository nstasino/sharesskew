from __future__ import division

import random
import sys

import numpy as np

from scipy.stats import zipf

random.seed(111)


print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)

dataset_size = int(sys.argv[1])
s = float(sys.argv[2])
print 'N = %d, skew = %f' % (dataset_size, s)

# valuerange = 1000000
big = 112312311


# Zipf's Law:
# freq(k; s, N) = \frac{k^{-s}{ \Sum^{n=1}_{n=N} {1/n^s} }
# s: skew parameter
# k: rank
# N: number of elements
# srange = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
krange = [1, 2, 3, 4, 5]
N = 10**6


skews = {}
d = sum([1/n**s for n in xrange(1, N)])
skews[s] = {}
for k in krange:
    freq = k**(-s)/d
    print "Rank: %d, Freq.: %f %.2f" % (k, freq, np.round(freq, 2))
#         print "zipf: %f" % (zipf.pmf(k, s))
    skews[s][k] = np.round(freq, 2)

ranks = skews[s]
remainder = 1 - sum([r for r in ranks.values()])
print s, ranks, remainder

skewed_sample_A2 = range(big, int(dataset_size*(remainder))+big)
skewed_sample_A2.extend([21 for i in xrange(int(dataset_size*ranks[1]))])
skewed_sample_A2.extend([22 for i in xrange(int(dataset_size*ranks[2]))])
skewed_sample_A2.extend([23 for i in xrange(int(dataset_size*ranks[3]))])
skewed_sample_A2.extend([24 for i in xrange(int(dataset_size*ranks[4]))])
skewed_sample_A2.extend([25 for i in xrange(int(dataset_size*ranks[5]))])


skewed_sample_A3 = range(big, int(dataset_size*(remainder))+big)
skewed_sample_A3.extend([31 for i in xrange(int(dataset_size*ranks[1]))])
skewed_sample_A3.extend([32 for i in xrange(int(dataset_size*ranks[2]))])
skewed_sample_A3.extend([33 for i in xrange(int(dataset_size*ranks[3]))])
skewed_sample_A3.extend([34 for i in xrange(int(dataset_size*ranks[4]))])
skewed_sample_A3.extend([35 for i in xrange(int(dataset_size*ranks[5]))])


r1 = [(random.choice(xrange(big)), random.choice(skewed_sample_A2))
      for _ in xrange(dataset_size)]
r2 = [(random.choice(skewed_sample_A2),
       random.choice(skewed_sample_A3),
       random.choice(xrange(big)))
      for _ in xrange(dataset_size)]
r3 = [(random.choice(skewed_sample_A3), random.choice(xrange(big)))
      for _ in xrange(dataset_size)]

filename = 'test_zipfian_'+str(dataset_size)+'_'+str(s)+'.txt'
with open(filename, 'wb') as outfile:
    outfile.write('\n'.join('R1 {} {}'.format(*x) for x in r1))
    outfile.write('\n')
    outfile.write('\n'.join('R2 {} {} {}'.format(*x) for x in r2))
    outfile.write('\n')
    outfile.write('\n'.join('R3 {} {}'.format(*x) for x in r3))
    outfile.write('\n')

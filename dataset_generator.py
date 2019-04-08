import random
dataset_size = 1000
valuerange =   1000000

print "test"
big = 12312314

skew_percentage = 0.05
skew_size = int(dataset_size * skew_percentage)
random.seed(123)
ordinary_sample = random.choice(xrange(int(valuerange*(1-skew_percentage))))

skewed_sample_A2 = range(big,int(valuerange*(1-skew_percentage))+big)
skewed_sample_A2.extend([2 for i in xrange(skew_size)])

skewed_sample_A3 = range(big, int(valuerange*(1-skew_percentage*2))+big)
skewed_sample_A3.extend([31 for i in xrange(skew_size)])
skewed_sample_A3.extend([32 for i in xrange(skew_size)])

# skewed_sample_A2 = random.choice(range(int(valuerange*(1-skew_percentage))) + '2')

r1 = [(random.choice(xrange(big)), random.choice(skewed_sample_A2))
      for _ in xrange(dataset_size)]
r2 = [(random.choice(skewed_sample_A2),
      random.choice(skewed_sample_A3),
      random.choice(xrange(big)))
      for _ in xrange(dataset_size)]
r3 = [(random.choice(skewed_sample_A3), random.choice(xrange(big)))
      for _ in xrange(dataset_size)]
# r4 = [(random.choice(xrange(big)), random.choice(xrange(big)))
#       for _ in xrange(dataset_size)]


with open('test2.txt', 'wb') as outfile:
    outfile.write('\n'.join('R1 {} {}'.format(*x) for x in r1))
    outfile.write('\n')
    outfile.write('\n'.join('R2 {} {} {}'.format(*x) for x in r2))
    outfile.write('\n')
    outfile.write('\n'.join('R3 {} {}'.format(*x) for x in r3))
    outfile.write('\n')

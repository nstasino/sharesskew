#!/usr/bin/env python
from mrjob.job import MRJob
from mrjob.step import MRStep
import mrjob
from mrjob.protocol import RawValueProtocol, RawProtocol, JSONProtocol, UltraJSONProtocol, StandardJSONProtocol, BytesValueProtocol, BytesProtocol, TextProtocol, PickleProtocol, PickleValueProtocol
import pickle
from itertools import imap, product

from collections import defaultdict
from copy import deepcopy
import sys


def hasHH(attr, hhs):
    for hh in hhs:
        if attr in hh.keys():
            return True
    else:
        return False


def allvaluesofHH(hhid, hhs):
    t = []
    for hh in hhs:
        try:
            t.append(hh[hhid])
        except:
            pass
    return list(set(t))

def decideSingleResidual(inputTuple, residualJoin, hhs, hhinverted):
    flag = True
    for idx, (inputVal, residualVal) in enumerate(zip(inputTuple, residualJoin)):
        if flag == True:
            if residualVal == '_':
                try:
                    hhinverted[(idx, inputVal)]
                    flag = False
                    break
                except:

                    flag = True
                    continue

            else:
                if inputVal == residualVal:
#                     print "this is a HH value and this is the correct residual"
                    flag = True
                    continue
                elif inputVal == '_':
                    flag = True
#                         print "this is NOT a HH value and this is the correct residual"
                    continue
                else:
                    flag = False
                    break
#             print "%r %r %r" % (idx, inputVal, residualVal)
    return flag

def decideFromAllResiduals(inputTuple, residualJoins, hhs):
    for residualJoin in residualJoins:
        print decideSingleResidual(inputTuple, residualJoin, hhs)


def extendTupleValue(attributeValues, relationSchema):
        extendedAttributeValues = ['_']*len(relationSchema)
        j = 0
        for i, v in enumerate(relationSchema):
            if v == 1:
                extendedAttributeValues[i] = attributeValues[j]
                j +=1
        return extendedAttributeValues


def extendHeavyHittersValues(attributeValues, databaseSchema):
        extendedAttributeValues = [0]*len(databaseSchema[0])
        j = 0
        for i, v in enumerate(relationSchema):
            if v == 1:
                extendedAttributeValues[i] = attributeValues[j]
                j += 1
        return extendedAttributeValues

def doubleHashJoin(table1, index1, table2, index2, table3, index3):
    h = defaultdict(list)
    h1 = defaultdict(list)
    # hash phase 1-2
    for s in table1:
        h[s[index1]].append(s)
    # join phase 1-2
    table12 = [(r1, r2) for r2 in table2 for r1 in h[r2[index2]]]
    # hash phase (12) - 3
    for s in table12:
        h1[s[1][index3]].append(s)
    # join phase (12) - 3
    return [(r12, r3) for r3 in table3 for r12 in h1[r3[index3]]]


class SharesSkewJob(MRJob):

    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = RawProtocol
#     OUTPUT_PROTOCOL = JSONProtocol


    def mapper_init(self):
        self.schema = pickle.load(open(self.options.schemaFile, 'rb'))
        self.residuals = pickle.load(open(self.options.residualsFile, 'rb'))
        self.heavyhitters = pickle.load(open(self.options.hhFile, 'rb'))
        #         Set HH shares == 1
        self.hhSharesResiduals = deepcopy(self.heavyhitters)
        for i, hhShareResidual in enumerate(self.hhSharesResiduals):
            for k, v in hhShareResidual.iteritems():
                hhShareResidual.pop(k)
                hhShareResidual[str(k)] = 1

        self.shares = pickle.load(open(self.options.sharesFile, 'rb'))
#         self.hhinvertedIndex = pickle.load(open(self.options.hhInvertedIndexFile, 'rb'))
        self.hhinvertedIndex = {}
        for t in self.heavyhitters:
            for k,v in t.iteritems():
                self.hhinvertedIndex[(k,v)] = "HH"
#         print self.schema
#         print self.residuals
#         print self.shares2
#         print self.heavyhitters



    def identityMapper(self, _, line):
        tokens = line.split(' ')
        relation = int(tokens[0][1:])
        attributeValues = tokens[1:]
        thisRelSchema = self.schema[relation-1] # Relations are numbered R1, R2, ..., whereas schema array is 0-numbered
        inputTuple = extendTupleValue(attributeValues, thisRelSchema)
        inputTupleShortened = [0 if v == '_' else int(v) for v in inputTuple[1:]]
        keylist = []
        for residualJoin, residualShare, hhShare in zip(self.residuals, self.shares, self.hhSharesResiduals)[0:1]:
            if True == True:
                residualShare.update(hhShare) # Adds the HH share which is always == 1
                for i in xrange(1, 5): # Some shares(==1) may be missing from the schema because they were not calcaulatied by the MINLPSolver
                    try:
                        residualShare[str(i)]
                    except:
                        residualShare[str(i)] = 1
                ranges = list(imap(range, [residualShare[k] for k in sorted(residualShare)])  )
                ranges = [ [val % len(share)] if h == 1 else share
                          for h, share, val in zip(thisRelSchema[1:], ranges, inputTupleShortened)]
#                 counter = 0
                residualJoinKeyPart = '-'.join(residualJoin)

                for key in product(*ranges):
#                     key.append(residualJoinKeyPart)
                    key = (residualJoinKeyPart,) + key
                    keylist.append( key ) # Hold keys for all residual in a (small = O(k*|residualJoins|)) list
#                 self.increment_counter('group', 'keylist size', 1)
#         # Remove duplicates
        keyset = set(keylist)
        for key in keyset:
            self.increment_counter('group', 'intermediate_tuples', 1)
#             yield key, (relation, inputTuple)
            inputTuple2 = "+".join(inputTuple)

            yield  '.'.join([str(x) for x in key]), str(relation) + ":" + str(inputTuple2)


    def mapper(self, _, line):
        tokens = line.split(' ')
        relation = int(tokens[0][1:])
        attributeValues = tokens[1:]
        thisRelSchema = self.schema[relation-1] # Relations are numbered R1, R2, ..., whereas schema array is 0-numbered
        inputTuple = extendTupleValue(attributeValues, thisRelSchema)
        inputTupleShortened = [0 if v == '_' else int(v) for v in inputTuple[1:]]
        keylist = []
        for residualJoin, residualShare, hhShare in zip(self.residuals, self.shares, self.hhSharesResiduals):
            if decideSingleResidual(inputTuple, residualJoin, self.heavyhitters) == True:
                residualShare.update(hhShare) # Adds the HH share which is always == 1
                for i in xrange(1, 5): # Some shares(==1) may be missing from the schema because they were not calculated by the MINLPSolver
                    try:
                        residualShare[str(i)]
                    except:
                        residualShare[str(i)] = 1
                ranges = list(imap(range, [residualShare[k] for k in sorted(residualShare)])  )
                ranges = [ [val % len(share)] if h == 1 else share
                          for h, share, val in zip(thisRelSchema[1:], ranges, inputTupleShortened)]
#                 counter = 0
                for key in product(*ranges):
                    keylist.append( key ) # Hold keys for all residual in a (small = O(k*|residualJoins|)) list
                    self.increment_counter('group', 'keylist size', 1)
        # Remove duplicates
#         keyset = set(keylist)
        keyset = keylist
        for key in keyset:
            self.increment_counter('group', 'intermediate_tuples', 1)
            yield key, (relation, inputTuple)
#             yield key

    def dummy_reducer(self, bucket, values):
        self.increment_counter('group', 'reducers raised', 1)
        count = 0
        for v in values:
            count += 1
        yield bucket, count


    def countReducer(self, bucket, values):
        self.increment_counter('group', 'reducers raised', 1)
        R1_tuples = []
        R2_tuples = []
        R3_tuples = []
        counter = 0
        count = 0
#         Fill tables
        for val in values:
            tokens = val.split(":")
            relation = int(tokens[0])
            v = tokens[1].split("+")
            if relation == 1:
                R1_tuples.append(v)
#                 R1_values["A2"][v[2]] += 1
            elif relation == 2:
                R2_tuples.append(v)
#                 R2_values["A2"][v[2]] += 1
#                 R2_values["A3"][v[3]] += 1
            elif relation == 3:
                R3_tuples.append(v)
#                 R3_values["A3"][v[3]] += 1
            counter += 1
        for r12, r3 in doubleHashJoin(R1_tuples, 2, R2_tuples, 2, R3_tuples, 3):
#             yield bucket, ','.join(r12[0]) + ' + ' + ','.join(r12[1]) + ' + ' + ','.join(r3)
                count += 1
        yield bucket, count

    def hashReducer(self, bucket, values):
        self.increment_counter('group', 'reducers raised', 1)
        R1_tuples = []
        R2_tuples = []
        R3_tuples = []
        counter = 0
#         Fill tables
        for val in values:
            tokens = val.split(":")
            relation = int(tokens[0])
            v = tokens[1].split("+")
            if relation == 1:
                R1_tuples.append(v)
#                 R1_values["A2"][v[2]] += 1
            elif relation == 2:
                R2_tuples.append(v)
#                 R2_values["A2"][v[2]] += 1
#                 R2_values["A3"][v[3]] += 1
            elif relation == 3:
                R3_tuples.append(v)
#                 R3_values["A3"][v[3]] += 1
            counter += 1
        for r12, r3 in doubleHashJoin(R1_tuples, 2, R2_tuples, 2, R3_tuples, 3):
            yield bucket, ','.join(r12[0]) + ' + ' + ','.join(r12[1]) + ' + ' + ','.join(r3)
#             if not (r12[0][2] == "2" and (r3[3] == "31" or r3[3] == "32")):
#                 yield bucket, r3[3]
#                 yield ','.join(r12[0]), ','.join(r12[1]) + ' + ' + ','.join(r3)

    def reducer(self, bucket, values):
        self.increment_counter('group', 'reducers raised', 1)
        R1_tuples = []
        R2_tuples = []
        R3_tuples = []

        R1_values = defaultdict(list)
        R2_values = defaultdict(list)
        R3_values = defaultdict(list)
        R4_values = defaultdict(list)
        R1_values["A2"] = defaultdict(int)
        R2_values["A2"] = defaultdict(int)
        R2_values["A3"] = defaultdict(int)
#         R2_values["A5"] = defaultdict(list)
        R3_values["A3"] = defaultdict(int)
#         R3_values["A4"] = defaultdict(list)
#         R4_values["A4"] = defaultdict(list)
#         R4_values["A5"] = defaultdict(list)

        counter = 0
        for val in values:
            tokens = val.split(":")
            relation = int(tokens[0])
            v = tokens[1].split("+")
#             if relation == 1:
# #                 R1_values["A2"][v[2]].append(v[2])
#                 R1_values["A2"].append(v[2])
#             elif relation == 2:
#                 R2_values["A2"].append(v[2])
#                 R2_values["A3"].append(v[3])
#                 R2_values["A5"].append(v[5])
#             elif relation == 3:
#                 R3_values["A3"].append(v[3])
#                 R3_values["A4"].append(v[4])
#             elif relation == 4:
#                 R4_values["A4"].append(v[4])
#                 R4_values["A5"].append(v[5])
            if relation == 1:
                R1_tuples.append(v)
                R1_values["A2"][v[2]] += 1
            elif relation == 2:
                R2_tuples.append(v)
                R2_values["A2"][v[2]] += 1
                R2_values["A3"][v[3]] += 1
            elif relation == 3:
                R3_tuples.append(v)
                R3_values["A3"][v[3]] += 1
            counter += 1


        print R1_tuples, R2_tuples, R3_tuples



#         if set(R1_values["A2"]).intersection(R2_values["A2"]):
#             if set(R2_values["A3"]).intersection(R3_values["A3"]):
#                     self.increment_counter('group', 'completed_joins', 1)
#                     yield bucket, "match"
#         for r1v2, r1v2Number in R1_values["A2"].iteritems():
#             r2v2Number = R2_values["A2"][str(r1v2)]
#             if r2v2Number > 0  :
#                 for r2v3 in R2_values["A3"]:
#                     r3v3Number = R3_values["A3"][str(r2v3)]
#                     if r3v3Number > 0:
# #                         print ".".join((r1v2, r2v3)), "MATCH"
#                         self.increment_counter('group', 'MATCHES FOUND', 1)
#                         print r1v2, r2v3
#                         matchesR1 = [x for x in R1_tuples if x[2] == r1v2]
#                         matchesR2 = [x for x in R2_tuples if x[2] == r1v2 and x[3] == r2v3 ]
#                         matchesR3 = [x for x in R3_tuples if x[3] == r2v3]
#                         print R1_tuples, R2_tuples, R3_tuples
#                         print matchesR1, matchesR2, matchesR3
#                     else:
#                         continue
#             else:
#                 continue



# Naive join with loops
#         for r1v in R1_values["A2"]:
#             for r2v in R2_values["A2"]:
#                 if r1v == r2v:
#                     for r2v3 in R2_values["A3"]:
#                         for r3v in R3_values["A3"]:
#                             if r2v3 == r3v:
#                                 yield ".".join((r1v, r2v3)), "MATCH"


    def configure_options(self):
            super(SharesSkewJob, self).configure_options()
            self.add_passthrough_option(
                '--reduce-number',
                type=int,
                help='Number of Reduce tasks.'
            )
            self.add_passthrough_option(
                '--internal-format', default='json', choices=['pickle', 'json', 'raw'],
                help="Specify the internal format of the job")
            self.add_passthrough_option(
                '--jobname', default='myjob',
                help="Specify the name of the job")
            self.add_file_option('--schemaFile')
            self.add_file_option('--residualsFile')
            self.add_file_option('--sharesFile')
            self.add_file_option('--hhFile')
            self.add_file_option('--hhInvertedIndexFile')

    def jobconf(self):
        orig_jobconf = super(SharesSkewJob, self).jobconf()
        custom_jobconf = {
                        'mapreduce.job.name': self.options.jobname,
                        'dfs.block.size': 4*1024*1024,
                        'mapreduce.task.io.sort.factor': 100,
                        'mapreduce.task.io.sort.mb': 2000,
                        'mapreduce.reduce.input.buffer.percent': 0.70,
                        'mapreduce.job.reduce.slowstart.completedmaps': 0.90

#                         'mapred.reduce.tasks': 256,

                         }

        return mrjob.conf.combine_dicts(orig_jobconf, custom_jobconf)

    def internal_protocol(self):
        if self.options.internal_format == 'json':
            return StandardJSONProtocol()
        elif self.options.internal_format == 'pickle':
            return PickleProtocol()
        elif self.options.internal_format == 'raw':
            return RawProtocol()

    def steps(self):
        return [
            MRStep(
                mapper_init=self.mapper_init,
#                    mapper=self.mapper,
                   mapper=self.identityMapper,
#                    combiner=self.combiner_count_words,
                   reducer=self.hashReducer,
#                     reducer=self.countReducer
#                    reducer=self.dummy_reducer
                  )
            ]

if __name__ == '__main__':
    SharesSkewJob.run()
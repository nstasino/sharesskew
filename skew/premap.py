#!/usr/bin/python

""" Premap phase

"""
import itertools

import sharesJoin

heavyHittersFilename = 'heavyhitters.txt'
sizesFilename = 'relationsizes.txt'
schemaFilename = 'relations.txt'
numberAttributes = 5


def readSchema(schemaFilename, numberAttributes):
    """ Constructs a schema representation with 1's denoting when a relation
    has an attribute.

    Input:  schemaFilename  A relations.txt filename.
                            The file is structured as such:
                                R1(A1,A2)
                                R2(A2,A3,A5)
                                R3(A3,A4)

            numberAttributes The total number of attributes in the schema
                                eg 6: [A0:A5]

    Output: schema          A list of lists as such:
                                [
                                [0, 1, 1, 0, 0, 0],
                                [0, 0, 1, 1, 0, 1],
                                [0, 0, 0, 1, 1, 0]
                                ]
    """
    schema = []
    with open(schemaFilename) as f:
        content = f.readlines()
    content = [x.strip('\n') for x in content]
    for line in content:
        rel = [0 for i in range(0, numberAttributes)]
        out = line.split('(')
        # relation = out[0]
        attrs = out[1].translate(None, '(),').split('A')[1:]
        indices = [int(attr) for attr in attrs]
        for idx in indices:
            rel[idx] = 1
        schema.append(rel)
    return schema


def readRelationSizes(sizesFilename):
    """ Reads from file the relation sizes

    input sizesFilename A filename. The file is
    eg R1   5000
       R2   10000
       R3   5000

    output coefficients A list of sizes
    eg [5000, 10000, 5000]
    """
    sizes = []
    lines = [line.rstrip('\n') for line in open(sizesFilename)]
    for l in lines:
        out = l.split('   ')  # 3 spaces separator
        # relation = out[0]
        # get rid of A from A2, transform to int
        size = int(out[1])
        # heavyhitter  value
        sizes.append(size)
    return sizes


def readHeavyHitters(heavyHittersFilename, numberAttributes):
    """ Reads heavy hitters from a given file

    Input: the filename containing HHs, see example below:

    Format example (3 spaces separation):
    (attribute)   (value)   (relation_i:tuples,relation_i:tuples,...)
    A2   2   R1:1000,R2:1000,R3:1000
    A3   31   R1:500,R2:500,R3:500
    A3   32   R1:500,R2:500,R3:500

    Output: hhinfo A complete dict with heavy hitters, their attribute name,
    hh value, skew relation sizes of the form  {'A3:32': {'attribute': 3,
     'R2': 500, 'R1': 500, 'value': 32, 'R3': 500}, 'A3:31': {'attribute': 3,
     'R2': 500, 'R1': 500, 'value': 31, 'R3': 500}, 'A2:2': {'attribute': 2,
     'R2': 1000, 'R1': 1000, 'value': 2, 'R3': 1000}}

            hh A list of lists (denoted in paper by L_x) containing attribute
    types, eg hh values and '_' to denote ordinary (i.e. non HH) type T_{_}

    example: [['_'], []['_', 'A', 'B'], ['_', C', 'D'], ['_']]

    """
    # all attributes also have ordinary values
    hh = [['_'] for x in xrange(numberAttributes)]
    hhinfo = {}
    hhinfo['attributes'] = {}
    lines = [line.rstrip('\n') for line in open(heavyHittersFilename)]
    for l in lines:
        out = l.split('   ')
        attribute = int(out[0].split('A')[1])
        value = int(out[1])
        skewness = out[2]
        relations_percentages = []
        for sk in skewness.split(','):
            relation_skew = float(sk.split(':')[1])
            relations_percentages.append(relation_skew)
        if attribute not in hhinfo['attributes']:
            hhinfo['attributes'][attribute] = {}
        hhinfo['attributes'][attribute][value] = {}
        hhinfo['attributes'][attribute][value]['type'] = 'hh'
        hhinfo['attributes'][attribute][value]['relations'] = relations_percentages
        hh[int(out[0][1:])].append(out[1])
    return (hhinfo, hh)


def refine_sizes(hhinfo):
    for h in hhinfo['attributes']:
        ordinary = [1.0, 1.0, 1.0]
        for v in hhinfo['attributes'][h]:
            h, v
            ordinary = [
                x - y for x, y in zip(ordinary, hhinfo['attributes'][h][v]['relations'])]
        hhinfo['attributes'][h]['_'] = {}
        hhinfo['attributes'][h]['_']['type'] = 'ordinary'
        hhinfo['attributes'][h]['_']['relations'] = ordinary
        print ordinary
    return hhinfo


def combinations(hh):
    """ Provide the product of all combinations of heavyhitter and ordinary
    types

    Input: A list of lists (denoted in paper by L_x) containing attribute
    types, eg hh values and '_' to denote ordinary (i.e. non HH) type T_{_}
    example: [['_', 'A:value1', 'B:value2'], ['C:value3', 'D:value4'], ['_']]

    Output: The cartesian product of all combinations eg C_T, in paper
        ('_', '_', '_', '_')
        ('_', '_', '_', 'C:value23')
        ('_', '_', '_', 'D')
        ('_', '_', 'A:value1', '_')
        ('_', '_', 'A:value1', 'C:value3')
        ('_', '_', 'A:value1', 'D:value4')
        ('_', '_', 'B:value2', '_')
        ('_', '_', 'B:value2', 'C:value3')
        ('_', '_', 'B:value2', 'D:value4')
    """
    return list(itertools.product(*hh))


def replaceSize(combination, relationSizes, hhinfo):
    """ Replaces sizes in original query with the number of tuples
    corresponding to the residual query sizes, depending on the prevalence of
    a HH attribute in the dataset.
    """
    p = [1.0 for i in xrange(len(relationSizes))]
# for each attribute of the residual join = combination
    for attr, value in enumerate(combination):
        '''
        First calculate p_bar which holds the probability
        for a value being ordinary i.e. not heavy hitter
        '''
        p_bar = [0.0 for i in xrange(len(relationSizes))]
        # if attribute not in heavy hitters at all (for example A1, or A0) skip fwd the loop
        try:
            hhinfo['attributes'][attr]
        except KeyError:
            continue
#         print attr, value,
        '''
        p_bar is 1.0 - the sum of all hh probabilities
        '''
        for hhval in hhinfo['attributes'][attr].keys():
            p_bar = [
                x+y for x, y in zip(p_bar, hhinfo['attributes'][attr][hhval]['relations'])]

#         if this is actually an ordinary value
        if value == '_':
            p = [1.0 - p_r for p_r in p_bar]
        else:
            value = float(value)
# -0.0 denotes non participation in relation for this attribute
            p = [p_r if p_r != -0.0 else 1.0 for p_r in hhinfo['attributes']
                 [attr][value]['relations']]
        relationSizes = [p_i * sizes_i
                         for p_i, sizes_i in zip(p, relationSizes)]
    return relationSizes


def calculateResidualJoins(heavyHittersFilename, numberAttributes, numberReducers, relationSizes):
    """ Calculates all residual joins shares
    """
    sharesAllResiduals = []
    hhinfo, hh = readHeavyHitters(heavyHittersFilename, numberAttributes)
    combs = combinations(hh)
    for cmb in combs:
        skewedRelationSizes = replaceSize(cmb, relationSizes, hhinfo)
        heavyhittersList = []
        for attr, value in enumerate(cmb):
            if value == '_':
                pass
            else:
                heavyhittersList.append(attr)
        s = sharesJoin.sharesCalculator(readSchema(schemaFilename, numberAttributes),
                                        numberAttributes, skewedRelationSizes, numberReducers, heavyhittersList, None)

        # print "Residual join: ",
        # print ','.join(str(c) for c in cmb)
        # print "Residual join sizes:",
        # print ','.join(str(size) for size in skewedRelationSizes)

        # print "Residual Join is %s" % cmb
        # print "Residual join sizes: %s" % skewedRelationSizes
        # print s.dominatingAttrs
        # print s.dominatedAttrs
        # print s.expressionVars
        sharesAllResiduals.append(s.getShares())
    return (combs, sharesAllResiduals)


def calculateResidualJoinsQ(heavyHittersFilename, numberAttributes, reducerCapacity, relationSizes):
    """ Calculates all residual joins shares
    """
    sharesAllResiduals = []
    hhinfo, hh = readHeavyHitters(heavyHittersFilename, numberAttributes)
    combs = combinations(hh)
    for cmb in combs:
        skewedRelationSizes = replaceSize(cmb, relationSizes, hhinfo)
        print skewedRelationSizes
        heavyhittersList = []
        for attr, value in enumerate(cmb):
            if value == '_':
                pass
            else:
                heavyhittersList.append(attr)
        s = sharesJoin.sharesCalculatorQ(readSchema(schemaFilename, numberAttributes),
                                         numberAttributes, skewedRelationSizes, reducerCapacity, heavyhittersList, None)

        # print "Residual join: ",
        # print ','.join(str(c) for c in cmb)
        # print "Residual join sizes:",
        # print ','.join(str(size) for size in skewedRelationSizes)

        # print "Residual Join is %s" % cmb
        # print "Residual join sizes: %s" % skewedRelationSizes
        # print s.dominatingAttrs
        # print s.dominatedAttrs
        # print s.expressionVars
        sharesAllResiduals.append(s.getShares())
    return (combs, sharesAllResiduals)

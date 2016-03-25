#!/usr/bin/python

""" sharesCalculator Class

    Construct an instance of a join and calculates the shares values

"""

import minlpSolver
# >>> for k in [2**x for x in range(1, 10)]:
# ...     s = sharesJoin.sharesCalculator('relations.txt', 6, 'relationsizes.txt', k)
# ...     s.getShares()

class sharesCalculator(object):

    def __init__(self, schemaFilename, numberAttributes,
                 sizesFilename, numberReducers):
        self.schemaFilename = schemaFilename
        self.numberAttributes = numberAttributes
        self.sizesFilename = sizesFilename
        self.numberReducers = numberReducers

        self.binaryschema = self.readSchema()
        self.relationSizes = self.readRelationSizes()
        (self.dominatingAttrs, self.dominatedAttrs) = \
            inferDominatingAttrs(constructDominationMatrix(self.binaryschema))
        self.expressionVars = self.constructCostExprVars()

    def getShares(self):
        # expressionVars =
        (shares, commcost) = minlpSolver.calculateShares(self.expressionVars,
                                                         self.relationSizes,
                                                         self.numberReducers)
        return (shares, commcost)

    def readSchema(self):
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
        with open(self.schemaFilename) as f:
            content = f.readlines()
        content = [x.strip('\n') for x in content]
        for line in content:
            rel = [0 for i in range(0, self.numberAttributes)]
            out = line.split('(')
            # relation = out[0]
            attrs = out[1].translate(None, '(),').split('A')[1:]
            indices = [int(attr) for attr in attrs]
            for idx in indices:
                rel[idx] = 1
            schema.append(rel)
        return schema

    def readRelationSizes(self):
        """ Reads from file the relation sizes

        input sizesFilename A filename. The file is
        eg R1   5000
           R2   10000
           R3   5000

        output coefficients A list of sizes
        eg [5000, 10000, 5000]
        """
        sizes = []
        lines = [line.rstrip('\n') for line in open(self.sizesFilename)]
        for l in lines:
            out = l.split('   ')  # 3 spaces separator
            # relation = out[0]
            # get rid of A from A2, transform to int
            size = int(out[1])
            # heavyhitter  value
            sizes.append(size)
        return sizes

    def constructCostExprVars(self):
        """ Find which attributes are terms for the cost expression
        eg ry+s+tx
        For each relation, the term is all the attributes minus the dominated
        ones.
                        [
                        [0, 1, 1, 0, 0, 0],
                        [0, 0, 1, 1, 0, 1],
                        [0, 0, 0, 1, 1, 0]
                        ]
                dominatingAttrs [2, 3]
                dominatedAttrs [1, 4, 5]

        Output terms list of terms to be summed up eg [[2], [], [3]]
        """
        terms = []
        for rel in self.binaryschema:
            #
            relAttrsParticipating = set([x for x in
                                         range(1, self.numberAttributes)])
            for attr, value in enumerate(rel):
                if value == 1:  # relation contains attribute
                    if attr not in self.dominatedAttrs:
                        # leave only non-dominated attrs in the term
                        relAttrsParticipating = relAttrsParticipating - \
                         set([attr])
            terms.append(list(relAttrsParticipating))
        return terms


def constructDominationMatrix(binaryschema):
    """ Applies Domination Rule on a relational schema given in a
    binary representation.
    Domination Rule: An attr X dominates Y iff whenever Y appears in a
    relation schema, X is present as well.

    To construct the domination Matrix, when both X, Y are present the
    respective matrix cell(x,y) is marked with 1.
    Then, if there is a single case that X is present in a schema but
    Y is not, the cell(x,y) is marked with 0.

    Input: binaryschema  A list of lists, typically the output of readSchema
                        function
                        [
                            [0, 1, 1, 0, 0, 0],
                            [0, 0, 1, 1, 0, 1],
                            [0, 0, 0, 1, 1, 0]
                        ]

    Output: A list of lists containing all dominatING attributes in the schema
            eg [
            [-1, -1, -1, -1, -1, -1],
            [-1, 0, 0, -1, -1, -1],
            [-1, 1, 0, 1, -1, 1],
            [-1, -1, 1, 0, 1, 1],
            [-1, -1, -1, 0, 0, -1],
            [-1, -1, 0, 0, -1, 0]
            ]
    """
    # Initialize domination matrix with -1 i.e. no attribute
    # coincidence in same relation
    dominationMatrix = []
    for cur in range(0, len(binaryschema[0])):
        dominationMatrix.append([-1 for x in range(0, len(binaryschema[0]))])
    # Mark attr coincidence with 1
    for cur in range(0, len(dominationMatrix)):
        for idx, rel in enumerate(binaryschema):
            for otherAttr in range(0, len(dominationMatrix)):
                if (rel[cur] == 1 and rel[otherAttr] == 1):
                    dominationMatrix[cur][otherAttr] = 0
    # Mark domination with 0
    for cur in range(0, len(dominationMatrix)):
        for idx, rel in enumerate(binaryschema):
            for otherAttr in range(0, len(dominationMatrix)):
                if (rel[cur] == 1 and rel[otherAttr] == 0 and
                        dominationMatrix[cur][otherAttr] == 0):
                    # print "%d (%d) dominates %d (%d) in %r(%r)" % \
                    #     (cur, rel[cur], otherAttr, rel[otherAttr], idx, rel)
                    dominationMatrix[cur][otherAttr] = 1
    return dominationMatrix


def inferDominatingAttrs(domMatrix):
    """ Infers dominating and dominated attributes from a domination matrix
    Input: a domination matrix typically coming from
    function constructDominationMatrix()

    For attributes X, Y when both matrix(x, y) and matrix(y, x) are equal
    to 1 they are NOT dominating each other.
    If cells m(x,y) = 1 and m(y,x) = 0 (or vice versa), then X dominates Y
    (or equivalently Y dominates X)

    eg [
        [-1, -1, -1, -1, -1, -1],
        [-1, 0, 0, -1, -1, -1],
        [-1, 1, 0, 1, -1, 1],
        [-1, -1, 1, 0, 1, 1],
        [-1, -1, -1, 0, 0, -1],
        [-1, -1, 0, 0, -1, 0]
        ]
    Output: Two lists. The first contains dominatING attrs and the second
    dominated attrs
    eg ([2, 3], [1, 4, 5])
    """
    m = domMatrix
    dominatingAttrs = []
    dominatedAttrs = []
    for i in range(len(m)):
        for j in range(i, len(m)):
            # if both have 1's in domination matrix they are equals
            if m[i][j] == m[j][i] == 1:
                # print "They are not dominating each other", i, j
                pass
            # 1 dominates 0
            elif m[i][j] == 1 and m[j][i] == 0:
                dominatingAttrs.append(i)
                dominatedAttrs.append(j)
                # print "%d dominates %d" % (i, j)
            # 0 is dominated by 1
            elif m[i][j] == 0 and m[j][i] == 1:
                dominatingAttrs.append(j)
                dominatedAttrs.append(i)
                # print "%d dominates %d" % (j, i)
    # Remove duplicate by converting the list to a set and then back to a list
    dominatingAttrs = list(set(dominatingAttrs))
    dominatedAttrs = list(set(dominatedAttrs))
    return (dominatingAttrs, dominatedAttrs)

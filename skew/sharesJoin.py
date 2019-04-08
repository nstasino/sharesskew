#!/usr/bin/python

""" sharesCalculator Class

    Construct an instance of a join and calculates the shares values

"""

import minlpsolver


class sharesCalculator(object):

    def __init__(self, schema, numberAttributes,
                 relationSizes, numberReducers, reducerCapacity, heavyhitters,
                 heavyhittersRelationSizes):
        """
            advanced    boolean If True, then k1*k2*k3=k
        """
        # Class input variables
        self.numberAttributes = numberAttributes
        # self.sizesFilename = sizesFilename
        self.numberReducers = numberReducers
        self.reducerCapacity = reducerCapacity
        self.heavyhitters = heavyhitters
        self.heavyhittersRelationSizes = heavyhittersRelationSizes

        # Class functions
        self.binaryschema = schema
        self.relationSizes = relationSizes
        self.dominationMatrix = self.constructDominationMatrix()
        (self.dominatingAttrs, self.dominatedAttrs) = \
            self.inferDominatingAttrs()
        self.expressionVars = self.constructCostExprVars()

    def getShares(self):
        (shares, commcost, per_red_cost) = minlpsolver.calculateShares(
            self.expressionVars,
            self.relationSizes,
            self.numberReducers,
            self.reducerCapacity)
        return (shares, commcost, per_red_cost)

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

    def constructDominationMatrix(self):
        """ Applies Domination Rule on a relational schema given in a
        binary representation.
        Domination Rule: An attr X dominates Y iff whenever Y appears in a
        relation schema, X is present as well.

        To construct the domination Matrix, when both X, Y are present the
        respective matrix cell(x,y) is marked with 1.
        Then, if there is a single case that X is present in a schema but
        Y is not, the cell(x,y) is marked with 0.

        Particularly, in the case of a residual join (i.e. when heavy hitters
        are present in the current setting), we compensate twofold:
        First, in the outputted domination matrix, each row (=attribute) that
        is a heavy hitter has its elements equal=0. This means that it should
        not come up as dominating against any other attribute.
        Secondly, it can be the case that a hh attribute will not come up as
        dominated should one uses the dominated matrix. This is the case when
        no other attribute in the schema has 1 against the hh value(remember
        1vs0 implies domination). However, as per the sharesskew algorithm
        the share be equal=1, that is this attribute cannot be part of the
        communication cost (see Section 6 - Example). So we explicitly add the
        hh attribute to the dominatedAttrs for this residual join.

        Input: binaryschema  A list of lists, typically the output of
                            self.readSchema function
                            [
                                [0, 1, 1, 0, 0, 0],
                                [0, 0, 1, 1, 0, 1],
                                [0, 0, 0, 1, 1, 0]
                            ]
        Output: A list of lists containing all dominatING attributes
                in the schema
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
        for cur in range(0, len(self.binaryschema[0])):
            dominationMatrix.append([-1 for x in
                                     range(0, len(self.binaryschema[0]))])
        # Mark attr coincidence with 0
        for cur in range(0, len(dominationMatrix)):
            for idx, rel in enumerate(self.binaryschema):
                for otherAttr in range(0, len(dominationMatrix)):
                    if (rel[cur] == 1 and rel[otherAttr] == 1):
                        dominationMatrix[cur][otherAttr] = 0
        # Mark domination with 1
        for cur in range(0, len(dominationMatrix)):
            for idx, rel in enumerate(self.binaryschema):
                for otherAttr in range(0, len(dominationMatrix)):
                    if (rel[cur] == 1 and rel[otherAttr] == 0 and
                            dominationMatrix[cur][otherAttr] == 0):
                        # print "%d (%d) dominates %d (%d) in %r(%r)" % \
                                # (cur, rel[cur], otherAttr, rel[otherAttr],
                                # idx, rel)
                        dominationMatrix[cur][otherAttr] = 1
        # Rule 1 for heavyhitters - set appropriate row = 0
        for h in self.heavyhitters:
            for j in range(len(dominationMatrix[h])):
                dominationMatrix[h][j] = 0
        return dominationMatrix

    def inferDominatingAttrs(self):
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
        m = self.dominationMatrix
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
        # Rule 2 for heavyhitters - add hh explicitly to dominatedAttrs
        for h in self.heavyhitters:
            dominatedAttrs.append(h)
        # Remove duplicate by converting the list to a set and back again
        # Also, if A2 > A1 and A2 < A5, then A2 goes in the dominated list
        dominatingAttrs = list(set(dominatingAttrs) - set(dominatedAttrs))
        dominatedAttrs = list(set(dominatedAttrs))
        return (dominatingAttrs, dominatedAttrs)

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
            allAttrs = set([x for x in range(1, self.numberAttributes)])
            relAttrsParticipating = allAttrs - set(self.dominatedAttrs)
            for attr, value in enumerate(rel):
                if value == 1:  # relation contains attribute
                    # if attr in self.dominatedAttrs:
                        # leave only non-dominated attrs in the term
                    relAttrsParticipating = relAttrsParticipating - set([attr])
            terms.append(list(relAttrsParticipating))
        return terms


class sharesCalculatorQ(object):

    def __init__(self, schema, numberAttributes,
                 relationSizes, reducerCapacity, heavyhitters,
                 heavyhittersRelationSizes):
        """
            advanced    boolean If True, then k1*k2*k3=k
        """
        # Class input variables
        self.numberAttributes = numberAttributes
        # self.sizesFilename = sizesFilename
        # self.numberReducers = numberReducers
        self.reducerCapacity = reducerCapacity
        self.heavyhitters = heavyhitters
        self.heavyhittersRelationSizes = heavyhittersRelationSizes

        # Class functions
        self.binaryschema = schema
        self.relationSizes = relationSizes
        self.dominationMatrix = self.constructDominationMatrix()
        (self.dominatingAttrs, self.dominatedAttrs) = \
            self.inferDominatingAttrs()
        self.expressionVars = self.constructCostExprVars()

    def getShares(self):
        (shares, commcost, per_red_cost) = minlpsolver.calculateSharesQ(
            self.expressionVars,
            self.relationSizes,
            self.reducerCapacity)
        return (shares, commcost, per_red_cost)

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

    def constructDominationMatrix(self):
        """ Applies Domination Rule on a relational schema given in a
        binary representation.
        Domination Rule: An attr X dominates Y iff whenever Y appears in a
        relation schema, X is present as well.

        To construct the domination Matrix, when both X, Y are present the
        respective matrix cell(x,y) is marked with 1.
        Then, if there is a single case that X is present in a schema but
        Y is not, the cell(x,y) is marked with 0.

        Particularly, in the case of a residual join (i.e. when heavy hitters
        are present in the current setting), we compensate twofold:
        First, in the outputted domination matrix, each row (=attribute) that
        is a heavy hitter has its elements equal=0. This means that it should
        not come up as dominating against any other attribute.
        Secondly, it can be the case that a hh attribute will not come up as
        dominated should one uses the dominated matrix. This is the case when
        no other attribute in the schema has 1 against the hh value(remember
        1vs0 implies domination). However, as per the sharesskew algorithm
        the share be equal=1, that is this attribute cannot be part of the
        communication cost (see Section 6 - Example). So we explicitly add the
        hh attribute to the dominatedAttrs for this residual join.

        Input: binaryschema  A list of lists, typically the output of
                            self.readSchema function
                            [
                                [0, 1, 1, 0, 0, 0],
                                [0, 0, 1, 1, 0, 1],
                                [0, 0, 0, 1, 1, 0]
                            ]
        Output: A list of lists containing all dominatING attributes
                in the schema
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
        for cur in range(0, len(self.binaryschema[0])):
            dominationMatrix.append([-1 for x in
                                     range(0, len(self.binaryschema[0]))])
        # Mark attr coincidence with 0
        for cur in range(0, len(dominationMatrix)):
            for idx, rel in enumerate(self.binaryschema):
                for otherAttr in range(0, len(dominationMatrix)):
                    if (rel[cur] == 1 and rel[otherAttr] == 1):
                        dominationMatrix[cur][otherAttr] = 0
        # Mark domination with 1
        for cur in range(0, len(dominationMatrix)):
            for idx, rel in enumerate(self.binaryschema):
                for otherAttr in range(0, len(dominationMatrix)):
                    if (rel[cur] == 1 and rel[otherAttr] == 0 and
                            dominationMatrix[cur][otherAttr] == 0):
                        # print "%d (%d) dominates %d (%d) in %r(%r)" % \
                                # (cur, rel[cur], otherAttr, rel[otherAttr],
                                # idx, rel)
                        dominationMatrix[cur][otherAttr] = 1
        # Rule 1 for heavyhitters - set appropriate row = 0
        for h in self.heavyhitters:
            for j in range(len(dominationMatrix[h])):
                dominationMatrix[h][j] = 0
        return dominationMatrix

    def inferDominatingAttrs(self):
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
        m = self.dominationMatrix
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
        # Rule 2 for heavyhitters - add hh explicitly to dominatedAttrs
        for h in self.heavyhitters:
            dominatedAttrs.append(h)
        # Remove duplicate by converting the list to a set and back again
        # Also, if A2 > A1 and A2 < A5, then A2 goes in the dominated list
        dominatingAttrs = list(set(dominatingAttrs) - set(dominatedAttrs))
        dominatedAttrs = list(set(dominatedAttrs))
        return (dominatingAttrs, dominatedAttrs)

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
            allAttrs = set([x for x in range(1, self.numberAttributes)])
            relAttrsParticipating = allAttrs - set(self.dominatedAttrs)
            for attr, value in enumerate(rel):
                if value == 1:  # relation contains attribute
                    # if attr in self.dominatedAttrs:
                        # leave only non-dominated attrs in the term
                    relAttrsParticipating = relAttrsParticipating - set([attr])
            terms.append(list(relAttrsParticipating))
        return terms

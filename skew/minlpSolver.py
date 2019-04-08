# minlpSolver.py
""" Module tha utilizes couenne solver (needs to be installed and in $PATH)
via the pyomo module.
"""
import math

import numpy as np

from pyomo.environ import *
from pyomo.opt import SolverFactory


def constructObjective(expressionVars, relationSizes):
    """ Construct a string representation of the objective fnc i.e. the
    communication cost.

    input expressionVars A list of lists containing the parts of the key
                        missing in each relation
                        ex. [[3], [1], [2]]
         relationSizes Number of tuples in a given relation
                        ex. [100000, 1000000, 100000]

    output costExpression A string representation of the objective fnc that
            can be evaluated by the MINLP solver. The communication cost is
            a sum of terms, one per relation

            example: 100000 * model.x[3] + 1000000 * model.x[1] +
                    + 100000 * model.x[2]
    """

    costExpression = ""
    for relation, exprVars in enumerate(expressionVars):
        costExpression += " %d" % math.ceil(relationSizes[relation])
        if exprVars:
            for exprVar in exprVars:
                costExpression += " * model.x[%d]" % exprVar
        else:
            costExpression += " * 1"
        costExpression += " +"
    costExpression = costExpression[:-1]  # Remove trailing '+'
    return costExpression


def getUniqueExpressionVars(expressionVars):
    """ From the list of expression vars get a set (that is unique attrs)
    This is necessary to construct the budget constraint on the number
    of reducers

    input expressionVars A list of lists containing the parts of the key
                        missing in each relation
                        ex. [[3,1], [1], [2]]
    output ex. [1, 2, 3]
    """
    return list(set(x for l in expressionVars for x in l))


def constructConstraint(expressionVars, numberReducers):
    """ Construct a string representation of the Reducer constraint fnc i.e.
    the product of all shares is equal to the budget of reducers

    input expressionVars A list of lists containing the parts of the key
                        missing in each relation
                        ex. [[[3], [1], [2]]
         numberReducers Number of reducers
                        ex. 32

    output budgetExpression A string representation of the budget
                        constraint

            example:  model.x[1] * model.x[2] * model.x[3] - 32 == 0
    """
    k = numberReducers
    uniqueExpressionVars = getUniqueExpressionVars(expressionVars)
    budgetExpression = ""
    for relation, exprVars in enumerate(uniqueExpressionVars):
        budgetExpression += " model.x[%d] *" % exprVars
    budgetExpression = budgetExpression[:-1]  # Remove trailing '*'
    budgetExpression += "- %d == 0" % k
    return budgetExpression


def constructCapacityConstraintUB(expressionVars, costExpression, reducerCapacity):
    """ Construct a string representation of the upper bound of
     the single reducer capacity constraint fnc i.e.
    the product of all shares is equal to the budget of reducers

    input expressionVars A list of lists containing the parts of the key
                        missing in each relation
                        ex. [[[3], [1], [2]]
    costExpression the communication cost expression as produced in the construct
                objective fnc
                ex.  100000 * model.x[3] + 1000000 * model.x[1] +
                    + 100000 * model.x[2]
    capacity Maximum  number of tuples a reduce task can handle
                        ex. 100000

    output budgetExpressionUB A string representation of the budget
                        constraint
    example:10000 * model.x[3] * model.x[4] * model.x[5] + 10000 * model.x[4] +
           100000 * model.x[2] * model.x[5] + 1000000 * model.x[2] * model.x[3]
         - 0.99 * 1000000 * model.x[2] * model.x[3] * model.x[4] * model.x[5]
             <= 0
    """
    # budgetExpression_LB = "%s - 0.99 * %d * model.x[2] * model.x[3] * model.x[4] * model.x[5]  >= 0" % (costExpression, reducerCapacity)
    uniqueExpressionVars = getUniqueExpressionVars(expressionVars)
    budgetExpression = ""
    for relation, exprVars in enumerate(uniqueExpressionVars):
        budgetExpression += " model.x[%d] *" % exprVars
    budgetExpression = budgetExpression[:-1]  # Remove trailing '*'
    budgetExpressionUB = "%s - 1.2 * %d * %s <= 0" % (costExpression,
                                                      reducerCapacity,
                                                      budgetExpression)
    return budgetExpressionUB


def constructCapacityConstraintLB(expressionVars, costExpression, reducerCapacity):
    """ Construct a string representation of the upper bound of
     the single reducer capacity constraint fnc i.e.
    the product of all shares is equal to the budget of reducers

    input expressionVars A list of lists containing the parts of the key
                        missing in each relation
                        ex. [[[3], [1], [2]]
    costExpression the communication cost expression as produced in the construct
                objective fnc
                ex.  100000 * model.x[3] + 1000000 * model.x[1] +
                    + 100000 * model.x[2]
    capacity Maximum  number of tuples a reduce task can handle
                        ex. 100000

    output budgetExpressionUB A string representation of the budget
                        constraint
    example:10000 * model.x[3] * model.x[4] * model.x[5] + 10000 * model.x[4] +
           100000 * model.x[2] * model.x[5] + 1000000 * model.x[2] * model.x[3]
         - 0.99 * 1000000 * model.x[2] * model.x[3] * model.x[4] * model.x[5]
             <= 0
    """
    # budgetExpression_LB = "%s - 0.99 * %d * model.x[2] * model.x[3] * model.x[4] * model.x[5]  >= 0" % (costExpression, reducerCapacity)
    uniqueExpressionVars = getUniqueExpressionVars(expressionVars)
    budgetExpression = ""
    for relation, exprVars in enumerate(uniqueExpressionVars):
        budgetExpression += " model.x[%d] *" % exprVars
    budgetExpression = budgetExpression[:-1]  # Remove trailing '*'
    budgetExpressionLB = "%s - 0.8 * %d * %s >= 0" % (costExpression,
                                                      reducerCapacity,
                                                      budgetExpression)
    return budgetExpressionLB


def constructConstraintAdvanced(expressionVars, numberReducers_i):
    """ Construct a string representation of the constraint fnc i.e.
    the product of all shares is equal to the budget of reducers

    input expressionVars A list of lists containing the parts of the key
                        missing in each relation
                        ex. [[[3], [1], [2]]
         numberReducers Number of reducers
                        ex. k_i

    output budgetExpression A string representation of the budget
                        constraint

            example:  model.x[1] * model.x[2] * model.x[3] - model.k[k_i] == 0
    """
    k_i = numberReducers_i
    uniqueExpressionVars = getUniqueExpressionVars(expressionVars)
    budgetExpression = ""
    for relation, exprVars in enumerate(uniqueExpressionVars):
        budgetExpression += " model.x[%d] *" % exprVars
    budgetExpression = budgetExpression[:-1]  # Remove trailing '*'
    budgetExpression += "- model.k[%d]== 0" % k_i
    return budgetExpression


def calculateShares(expressionVars, relationSizes, numberReducers):
    """ Use the MINLP solver to calculate the shares of attribute variables

    input   expressionVars  A list of lists of expression vars
                            ex. [[[3], [1], [2]]
            relationSizes A list ex. [1000, 1000, 1000]
            numberReducers an integer ex. 32

    output (shares, com_cost) Two outputs.
            shares First argument is the shares DICT !! unordered
                    ex. {'1':2, '2': 1, '3': 16}
            com_cost The objective function's value give the shares
                    ex. 2600000
    """
    # print expressionVars
    uniqueVars = getUniqueExpressionVars(expressionVars)
    print uniqueVars
    objectiveExpression = constructObjective(expressionVars, relationSizes)
    budgetExpression = constructConstraint(expressionVars, numberReducers)
    print objectiveExpression
    print budgetExpression
    # Create a solver factory using Couenne
    opt = SolverFactory('couenne')
    model = ConcreteModel()
    model.x = Var(uniqueVars, domain=PositiveIntegers)
    model.OBJ = Objective(expr=eval(objectiveExpression))
    model.Constraint1 = Constraint(expr=eval(budgetExpression))
    # Create a model instance and optimize
    instance = model.create_instance()
    results = opt.solve(instance)
    # instance.display()
    # Save calculated shares
    shares = {}
    for v in instance.component_objects(Var, active=True):
        varobject = getattr(instance, str(v))
        for index in varobject:
            # Round 2.999->3
            shares[str(varobject[index])[2:-1]
                   ] = (int(round(varobject[index].value)))
    # Save communication cost
    for o in instance.component_objects(Objective, active=True):
        oobject = getattr(instance, str(o))
        for idx in oobject:
            com_cost = value(oobject[idx])
    return (shares, com_cost, com_cost/numberReducers)


def calculateSharesQ(expressionVars, relationSizes, reducerCapacity):
    """ Use the MINLP solver to calculate the shares of attribute variables

    input   expressionVars  A list of lists of expression vars
                            ex. [[[3], [1], [2]]
            relationSizes A list ex. [1000, 1000, 1000]
            numberReducers an integer ex. 32

    output (shares, com_cost) Two outputs.
            shares First argument is the shares DICT !! unordered
                    ex. {'1':2, '2': 1, '3': 16}
            com_cost The objective function's value give the shares
                    ex. 2600000
    """
    # print expressionVars
    uniqueVars = getUniqueExpressionVars(expressionVars)
    print uniqueVars
    shares = {}
    # if sum(relationSizes) < reducerCapacity*10:
    # skew_share = int(pow(np.prod(relationSizes)/100000 , 1.0/len(uniqueVars)))
    # shares = {str(var): skew_share for var in uniqueVars}
    # shares = {str(var): 1 for var in uniqueVars}

    # com_cost = sum(relationSizes)
    # return (shares, com_cost, com_cost/np.prod(shares.values()))
    # reducerCapacity = 100000

    objectiveExpression = constructObjective(expressionVars, relationSizes)
    print objectiveExpression
    budgetExpression_UB = constructCapacityConstraintUB(
        expressionVars, objectiveExpression, reducerCapacity)
    budgetExpression_LB = constructCapacityConstraintLB(
        expressionVars, objectiveExpression, reducerCapacity)

    # Create a solver factory using Couenne
    opt = SolverFactory('couenne')
    model = ConcreteModel()
    model.x = Var(uniqueVars, domain=PositiveIntegers)
    model.OBJ = Objective(expr=eval(objectiveExpression))
    model.Constraint1 = Constraint(expr=eval(budgetExpression_UB))
    # model.Constraint2 = Constraint(expr=eval(budgetExpression_LB))
    # Create a model instance and optimize
    instance = model.create_instance()
    results = opt.solve(instance)
    instance.display()
    # Save calculated shares
    for v in instance.component_objects(Var, active=True):
        varobject = getattr(instance, str(v))
        for index in varobject:
            # Round 2.999->3
            shares[str(varobject[index])[2:-1]
                   ] = (int(round(varobject[index].value)))
    # Save communication cost
    for o in instance.component_objects(Objective, active=True):
        oobject = getattr(instance, str(o))
        for idx in oobject:
            com_cost = value(oobject[idx])
    return (shares, com_cost, com_cost/np.prod(shares.values()))


def calculateSharesAdvanced(expressionVars, relationSizes, numberReducers):
    """ Use the MINLP solver to calculate the shares of attribute variables

    input   expressionVars  A list of lists of expression vars
                            ex. [[[3], [1], [2]]
            relationSizes A list ex. [1000, 1000, 1000]
            numberReducers an integer ex. 32

    output (shares, com_cost) Two outputs.
            shares First argument is the shares DICT !! unordered
                    ex. {'1':2, '2': 1, '3': 16}
            com_cost The objective function's value give the shares
                    ex. 2600000
    """
    # print expressionVars
    uniqueVars = getUniqueExpressionVars(expressionVars)
    objectiveExpression = constructObjective(expressionVars, relationSizes)
    budgetExpression = constructConstraintAdvanced(
        expressionVars, numberReducers)
    # print objectiveExpression
    # print budgetExpression
    return (objectiveExpression, budgetExpression)

# minlpSolver.py
""" Module tha utilizes couenne solver (needs to be installed and in $PATH)
via the pyomo module.
"""
from pyomo.environ import *
from pyomo.opt import SolverFactory


# expressionVars = [[3, 2], [1], [2]]
# relationSizes = [100000, 1000000, 100000]
# numberReducers = 32


def constructObjective(expressionVars, relationSizes):
    """ Construct a string representation of the objective fnc i.e. the
    communication cost.

    input expressionVars A list of lists containing the parts of the key
                        missing in each relation
                        ex. [[[3], [1], [2]]
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
        costExpression += " %d" % relationSizes[relation]
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
    """ Construct a string representation of the constraint fnc i.e.
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


def calculateShares(expressionVars, relationSizes, numberReducers):
    """ Use the MINLP solver to calculate the shares of attribute variables

    input   expressionVars
            relationSizes
            numberReducers

    output (shares, com_cost) Two outputs.
            shares First argument is the shares list
                    ex. [2, 1, 16]
            com_cost The objective function's value give the shares
                    ex. 2600000
    """
    uniqueVars = getUniqueExpressionVars(expressionVars)
    # print uniqueVars
    objectiveExpression = constructObjective(expressionVars, relationSizes)
    budgetExpression = constructConstraint(expressionVars, numberReducers)
    # print objectiveExpression
    # print budgetExpression
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
    shares = []
    for v in instance.component_objects(Var, active=True):
        varobject = getattr(instance, str(v))
        for index in varobject:
            shares.append(int(round(varobject[index].value)))  # Round 2.999->3
    # Save communication cost
    for o in instance.component_objects(Objective, active=True):
        oobject = getattr(instance, str(o))
        for idx in oobject:
            com_cost = value(oobject[idx])
    return (shares, com_cost)

# print calculateShares(expressionVars, relationSizes, numberReducers)

from nose.tools import *
from skew import premap

# def test_constructGenericCost():

#     assert_equal(premap.constructGenericCost(schema, relationsizes), )


def test_transformSchema():

    result = premap.readSchema('relations.txt', 6)
    expected_result = [
        [0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0]
    ]
    assert_equal(result, expected_result)


def test_constructDominationMatrix():
    binaryschema = [
        [0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0]
    ]
    result = premap.constructDominationMatrix(binaryschema)
    expected_result = [
        [-1, -1, -1, -1, -1, -1],
        [-1, 0, 0, -1, -1, -1],
        [-1, 1, 0, 1, -1, 1],
        [-1, -1, 1, 0, 1, 1],
        [-1, -1, -1, 0, 0, -1],
        [-1, -1, 0, 0, -1, 0]
        ]
    assert_equal(result, expected_result)


def test_inferDominatingAttrs():
    matrix = [
        [-1, -1, -1, -1, -1, -1],
        [-1, 0, 0, -1, -1, -1],
        [-1, 1, 0, 1, -1, 1],
        [-1, -1, 1, 0, 1, 1],
        [-1, -1, -1, 0, 0, -1],
        [-1, -1, 0, 0, -1, 0]
        ]
    result = premap.inferDominatingAttrs(matrix)
    expected_result = ([2, 3], [1, 4, 5])
    assert_equal(result, expected_result)


def test_constructCostExprVars():
    schema = [
        [0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0]
    ]
    dominatingAttrs = [2, 3]
    dominatedAttrs = [1, 4, 5]
    result = premap.constructCostExprVars(schema, dominatingAttrs,
                                          dominatedAttrs)
    expected_result = [[3], [], [2]]
    assert_equal(result, expected_result)


def test_readRelationSizes():
    result = premap.readRelationSizes('relationsizes.txt')
    expected_result = [5000, 10000, 500]
    assert_equal(result, expected_result)

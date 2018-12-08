'Utility functions for bikewheelcalc'

import numpy as np


def skew_symm(v):
    'Create a skew-symmetric tensor V from vector v such that V*u = v cross u.'

    return np.matrix([[0,     v[2], -v[1]],
                      [-v[2], 0,     v[0]],
                      [v[1], -v[0],  0]])


def pol2rect(p):
    'Convert a point from polar coordinates to Cartesian coordinates.'

    return np.array([p[0]*np.sin(p[1]), -p[0]*np.cos(p[1]), p[2]])


def rect2pol(p):
    'Convert a point from Cartesian coordinates to polar coordinates.'

    r = np.sqrt(p[0]**2 + p[1]**2)
    theta = np.arctan2(p[0], -p[1])

    return np.array([r, theta, p[2]])

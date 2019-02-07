import pytest
import numpy as np


def test_stiffness(client, wheel_dict):
    'Test stiffness calculation'

    post = dict(wheel_dict)
    post['stiffness'] = {}

    response = client.post('/calculate', json=post)

    assert np.allclose(response.json['stiffness']['lateral_stiffness'],
                       94150.65602356319)

    assert np.allclose(response.json['stiffness']['radial_stiffness'],
                       4255534.38869831)

    assert np.allclose(response.json['stiffness']['torsional_stiffness'],
                       108891.17398367148)

def test_stiffness_singular(client, wheel_dict):
    'Check that a radial-spoked wheel with 0 tension returns an error'

    post = dict(wheel_dict)
    post['wheel']['spokes']['num_cross'] = 0  # radial spokes
    post['stiffness'] = {}

    response = client.post('/calculate', json=post)

    assert response.json['stiffness']['success'] == False
    assert response.json['stiffness']['error'] == 'Linear algebra error'

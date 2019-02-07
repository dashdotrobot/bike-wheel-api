import pytest
import numpy as np


def test_tensions_single_spoke(client, wheel_dict):
    'Get tension results for a single spoke'

    post = dict(wheel_dict)
    post['tension'] = {
        'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]}],
        'spokes': [0]
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['tension']['success'] == True
    assert len(response.json['tension']['tension']) == 1
    assert len(response.json['tension']['tension_change']) == 1
    assert np.allclose(response.json['tension']['tension_change'][0], -0.4117197104970742)

def test_tensions_all_spokes(client, wheel_dict):
    'Get tension results for all spokes (default)'

    post = dict(wheel_dict)
    post['tension'] = {
        'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]}]
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['tension']['success'] == True
    assert len(response.json['tension']['tension']) == 36
    assert len(response.json['tension']['tension_change']) == 36

def test_tension_range(client, wheel_dict):
    'Test deformation calculation with mixed inputs'

    post = dict(wheel_dict)
    post['tension'] = {
        'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]},
                   {'location': np.pi, 'f_lat': 1.}],
        'spokes_range': [2, 11, 2]  # every other spoke, 2-10
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['tension']['success'] == True
    assert len(response.json['tension']['tension']) == 5
    assert len(response.json['tension']['tension_change']) == 5

def test_tension_adjustment_single(client, wheel_dict):
    'Get tension influence function for a single adjustment'

    post = dict(wheel_dict)
    post['tension'] = {
        'spoke_adjustments': [{'spoke': 0, 'adjustment': 0.001}]
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['tension']['success'] == True
    assert np.allclose(response.json['tension']['tension_change'][0], 771.8033786298678)

def test_tension_adjustment_single_symm(client, wheel_dict):
    'Check that influence function is identical for symmetry-invariant spokes'

    post_1 = dict(wheel_dict)
    post_1['tension'] = {
        'spoke_adjustments': [{'spoke': 0, 'adjustment': 0.001}]
    }

    response_1 = client.post('/calculate', json=post_1)
    dT_1 = response_1.json['tension']['tension_change']

    post_2 = dict(wheel_dict)
    post_2['tension'] = {
        'spoke_adjustments': [{'spoke': 4, 'adjustment': 0.001}]
    }

    response_2 = client.post('/calculate', json=post_2)
    dT_2 = response_2.json['tension']['tension_change']

    assert np.allclose(dT_1, np.roll(dT_2, -4))

def test_tension_adjustment_all(client, wheel_dict):
    'Get tension influence function for a single adjustment'

    a = [0.001]*36
    post = dict(wheel_dict)
    post['tension'] = {
        'spoke_adjustments': a
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['tension']['success'] == True

    # Similar tensions
    dT = response.json['tension']['tension_change']
    assert np.all(np.abs(dT - np.mean(dT))/np.mean(dT) < 0.01)

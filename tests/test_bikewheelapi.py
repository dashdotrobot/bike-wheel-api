import pytest
import numpy as np


def test_hello_world(client):
    'Test the "hello world" endpoint'

    response = client.get('/')

    assert response.status_code == 200
    assert b'Hello World' in response.data

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

def test_Tc_default(client, wheel_dict):
    'Calculate buckling tension and mode with (default) linear approximation'

    post = dict(wheel_dict)
    post['buckling_tension'] = {}

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['buckling_tension']['success'] == True
    assert np.allclose(response.json['buckling_tension']['buckling_tension'],
                       1787.1372120201747)
    assert response.json['buckling_tension']['buckling_mode'] == 2

def test_Tc_linear(client, wheel_dict):
    'Calculate buckling tension and mode with linear approximation'

    post = dict(wheel_dict)
    post['buckling_tension'] = {
        'approx': 'linear'
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['buckling_tension']['success'] == True
    assert np.allclose(response.json['buckling_tension']['buckling_tension'],
                       1787.1372120201747)
    assert response.json['buckling_tension']['buckling_mode'] == 2

def test_Tc_wrong_approx(client, wheel_dict):
    'Try sending an invalid approximation type'

    post = dict(wheel_dict)
    post['buckling_tension'] = {
        'approx': 'xyzrandom'
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['buckling_tension']['success'] == False
    assert response.json['buckling_tension']['error'] == 'Unknown approximation: xyzrandom'

def test_hub_diff_flanges(client, wheel_dict):
    'Build a wheel with different hub flange diameters'

    post = dict(wheel_dict)
    post['wheel']['hub'] = {'diameter_ds': 0.05, 'diameter_nds': 0.04,
                            'width_ds': 0.02, 'width_nds': 0.03}
    post['mass'] = {}

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['wheel']['hub']['diameter_ds'] == 0.05
    assert response.json['wheel']['hub']['diameter_nds'] == 0.04
    assert response.json['wheel']['hub']['width_ds'] == 0.02
    assert response.json['wheel']['hub']['width_nds'] == 0.03

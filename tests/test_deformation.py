import pytest
import numpy as np


def test_deformation_single(client, wheel_dict):
    'Check that deformation from a radial load matches stiffness calculation'

    post = wheel_dict
    post['deformation'] = {
        'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]}],
        'theta': 0.
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['deformation']['success'] == True
    assert np.allclose(response.json['deformation']['def_rad'][0],
                       1. / 4255534.38869831)

def test_deformation_range(client, wheel_dict):
    'Test deformation calculation with mixed inputs'

    post = wheel_dict
    post['deformation'] = {
        'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]},
                   {'location': np.pi, 'f_lat': 1.}],
        'theta_range': [0., np.pi, 10]}

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['deformation']['success'] == True
    assert len(response.json['deformation']['def_rad']) == 10

def test_deformation_adjustment_single(client, wheel_dict):
    'Get deformation influence function for a single adjustment'

    post = dict(wheel_dict)
    post['deformation'] = {
        'spoke_adjustments': [{'spoke': 0, 'adjustment': 0.001}]
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['deformation']['success'] == True
    assert np.allclose(response.json['deformation']['def_rad'][0],
                       0.00041171971049707427)
    assert np.allclose(response.json['deformation']['def_lat'][0],
                       0.001675641915712939)

def test_tension_adjustment_single_symm(client, wheel_dict):
    'Check that influence function is identical for symmetry-invariant spokes'

    post_1 = dict(wheel_dict)
    post_1['deformation'] = {
        'spoke_adjustments': [{'spoke': 0, 'adjustment': 0.001}],
        'theta_range': np.linspace(-np.pi/6, np.pi/6, 10).tolist()
    }

    response_1 = client.post('/calculate', json=post_1)
    v_1 = response_1.json['deformation']['def_rad']

    post_2 = dict(wheel_dict)
    post_2['deformation'] = {
        'spoke_adjustments': [{'spoke': 4, 'adjustment': 0.001}],
        'theta_range': np.linspace(4*2*np.pi/36-np.pi/6,
                                  4*2*np.pi/36+np.pi/6,
                                  10).tolist()
    }

    response_2 = client.post('/calculate', json=post_2)
    v_2 = response_2.json['deformation']['def_rad']

    assert np.allclose(v_1, v_2)

def test_tension_adjustment_all(client, wheel_dict):
    'Get radial influence function for a uniform spoke adjustment'

    a = [0.001]*36
    post = dict(wheel_dict)
    post['deformation'] = {
        'spoke_adjustments': a
    }

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['deformation']['success'] == True

    # Similar tensions
    v = response.json['deformation']['def_rad']
    assert np.all(np.abs(v - np.mean(v))/np.mean(v) < 0.01)

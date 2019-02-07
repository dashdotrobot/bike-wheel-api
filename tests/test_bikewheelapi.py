import pytest
import numpy as np


def test_hello_world(client):
    'Test the "hello world" endpoint'

    response = client.get('/')

    assert response.status_code == 200
    assert b'Hello World' in response.data

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

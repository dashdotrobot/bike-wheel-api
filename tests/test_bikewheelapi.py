import pytest
from json import dumps, loads
import numpy as np
from bikewheelapi import calculate
import matplotlib.pyplot as plt


class Response:
    def __init__(self, response=None):
        if response:
            self.status_code = response['statusCode']
            self.json = loads(response['body'])

class TestClient:
    def post(self, endpoint, json):
        event = {'body': dumps(json)}
        return Response(calculate(event, context=None))

    def get(self, endpoint):
        response = Response()
        response.status_code = 200
        response.data = b'Hello World'
        return response


@pytest.fixture
def wheel_dict():
    return {
        'wheel': {
            'hub': {
                'diameter': 0.05,
                'width_nds': 0.025,
                'width_ds': 0.025},
            'rim': {
                'radius': 0.3,
                'young_mod': 69e9,
                'shear_mod': 26e9,
                'density': 2700.,
                'section_type': 'general',
                'section_params': {
                    'area': 100e-6,
                    'I_rad': 100 / 69e9,
                    'I_lat': 200 / 69e9,
                    'J_tor': 25 / 26e9,
                    'I_warp': 0.}},
            'spokes': {
                'num': 36,
                'num_cross': 3,
                'diameter': 1.8e-3,
                'young_mod': 210e9,
                'density': 8000.,
                'offset': 0.,
                'tension': 0.}}}

@pytest.fixture
def client(request):
    return TestClient()


def test_hello_world(client):
    response = client.get('/')

    assert b'Hello World' in response.data

    assert response.status_code == 200

def test_stiffness_success(client, wheel_dict):

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

    post = dict(wheel_dict)
    post['wheel']['spokes']['num_cross'] = 0  # radial spokes
    post['stiffness'] = {}

    response = client.post('/calculate', json=post)

    assert response.json['stiffness']['success'] == False
    assert response.json['stiffness']['error'] == 'Linear algebra error'

def test_deformation_single(client, wheel_dict):

    post = wheel_dict
    post['deformation'] = {
        'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]}],
        'theta': 0.
    }

    response = client.post('/calculate', json=post)

    print(response.json)

    assert response.status_code == 200
    assert response.json['deformation']['success'] == True
    assert np.allclose(response.json['deformation']['def_rad'][0],
                       1. / 4255534.38869831)

def test_deformation_range(client, wheel_dict):

    post = wheel_dict

    post['deformation'] = {
        'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]},
                   {'location': np.pi, 'f_lat': 1.}],
        'theta_range': [0., np.pi, 10]}

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['deformation']['success'] == True
    assert len(response.json['deformation']['def_rad']) == 10

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
    assert response.json['tension']['tension_change'][0] < 0

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

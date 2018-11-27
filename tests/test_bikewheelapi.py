import pytest
import numpy as np
from bikewheelapi import app
import matplotlib.pyplot as plt

wheel_dict = {
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
            'tension': 0.}}

@pytest.fixture
def client(request):
    test_client = app.test_client()

    return test_client


def test_hello_world(client):
    response = client.get('/')
    assert b'Hello World' in response.data

def test_stiffness(client):

    response = client.post('/stiffness', json=wheel_dict)

    assert np.allclose(response.json['lateral_stiffness'],
                       94150.65602356319)

    assert np.allclose(response.json['radial_stiffness'],
                       4255534.38869831)

    assert np.allclose(response.json['torsional_stiffness'],
                       108891.17398367148)

def test_deformation_single(client):

    data = {'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]}]}
    data.update({'result': {'theta': 0.}})
    data.update(wheel_dict)

    response = client.post('/deform', json=data)

    assert response.status_code == 200

    assert np.allclose(response.json['result']['def_rad'][0],
                       1. / 4255534.38869831)

def test_deformation_range(client):

    data = {'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]},
                       {'location': np.pi, 'f_lat': 1.}]}
    data.update({'result': {'theta_range': [0., np.pi, 10]}})
    data.update(wheel_dict)

    response = client.post('/deform', json=data)

    assert response.status_code == 200

    assert len(response.json['result']['def_rad']) == 10

def test_tensions_single(client):
    data = {'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]}]}
    data.update({'result': {}})
    data.update(wheel_dict)
    data['spokes']['tension'] = 1000.

    response = client.post('/tensions', json=data)

    print(response.json['result'])

    assert response.status_code == 200

    assert False


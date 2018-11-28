import pytest
import numpy as np
from bikewheelapi import app
import matplotlib.pyplot as plt

wheel_dict = {
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
    test_client = app.test_client()

    return test_client


def test_hello_world(client):
    response = client.get('/')

    assert b'Hello World' in response.data

    assert response.status_code == 200


def test_stiffness(client):

    post = dict(wheel_dict)
    post['stiffness'] = {}

    response = client.post('/calculate', json=post)

    assert np.allclose(response.json['stiffness']['lateral_stiffness'],
                       94150.65602356319)

    assert np.allclose(response.json['stiffness']['radial_stiffness'],
                       4255534.38869831)

    assert np.allclose(response.json['stiffness']['torsional_stiffness'],
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

def test_tensions_single_spoke(client):
    'Get tension results for a single spoke'

    post = dict(wheel_dict)
    post['tension'] = {'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]}],
                        'spokes': [0]}

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['tension']['success'] == True
    assert len(response.json['tension']['tension']) == 1
    assert len(response.json['tension']['d_tension']) == 1

def test_tensions_all_spokes(client):
    'Get tension results for all spokes (default)'

    post = dict(wheel_dict)
    post['tension'] = {'forces': [{'location': 0., 'magnitude': [0., 1., 0., 0.]}]}

    response = client.post('/calculate', json=post)

    assert response.status_code == 200
    assert response.json['tension']['success'] == True
    assert len(response.json['tension']['tension']) == 36
    assert len(response.json['tension']['d_tension']) == 36

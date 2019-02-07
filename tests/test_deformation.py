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

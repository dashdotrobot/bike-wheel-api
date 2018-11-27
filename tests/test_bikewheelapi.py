import pytest
from bikewheelapi import app

@pytest.fixture
def client(request):
    test_client = app.test_client()

    return test_client


def test_hello_world(client):
    response = client.get('/')
    assert b'Hello World' in response.data

def test_make_wheel(client):

    post_dict = {
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
                'I_warp': 0.}}}

    response = client.post('/makewheel', json=post_dict)

    assert False

import pytest
from json import dumps, loads
from bikewheelapi import calculate

# -----------------------------------------------------------------------------
# Test fixtures
#------------------------------------------------------------------------------

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
from flask import Flask, jsonify, make_response, request
from bikewheelcalc import BicycleWheel, Hub, Rim


app = Flask(__name__)


# --------------------------------- ROUTES --------------------------------- #
# Define application endpoints                                               #
# -------------------------------------------------------------------------- #

@app.route('/')
def hello():
    return 'Hello World'

@app.route('/deform', methods=['POST'])
def get_deformation():
    'Return the deformation of a wheel under a set of loads'

    # Not implemented
    return make_response('', 501)

@app.route('/tensions')
def get_tensions():
    'Return the spoke tensions of a wheel under a set of loads'

    # Not implemented
    return make_response('', 501)

@app.route('/makewheel', methods=['POST'])
def make_wheel():
    'TESTING PURPOSES: Create a wheel from POST data'

    # Build wheel from POST data
    wheel_from_json(request.json)

    return make_response('', 501)


# ---------------------------------- MODEL --------------------------------- #
# Define functions to calculate wheel results                                #
# -------------------------------------------------------------------------- #

def validate(json, key, key_type=float):
    'Ensure that key exists and cast to correct type'
    if key in json:
        try:
            if key_type == float:
                return float(json[key])
            elif key_type == str:
                return str(json[key])
        except:
            raise TypeError('Invalid value for parameter {:s}'
                            .format(key))

    else:
        raise KeyError("Parameter '{:s}' not found in POST JSON"
                       .format(key))

def wheel_from_json(json):
    'Create a BicycleWheel object from JSON'

    print(json['hub'])

    w = BicycleWheel

    # Hub
    if 'hub' in json:
        w.hub = Hub(diameter=validate(json['hub'], 'diameter'),
                    width_nds=validate(json['hub'], 'width_nds'),
                    width_ds=validate(json['hub'], 'width_ds'))
    else:
        raise KeyError('Hub definition not found in POST JSON')

    return w

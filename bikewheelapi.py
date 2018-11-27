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
    w = wheel_from_json(request.json)

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

    w = BicycleWheel

    # Hub
    if 'hub' in json:
        w.hub = Hub(diameter=validate(json['hub'], 'diameter'),
                    width_nds=validate(json['hub'], 'width_nds'),
                    width_ds=validate(json['hub'], 'width_ds'))
    else:
        raise KeyError('Hub definition not found in POST JSON')

    # Rim
    if 'rim' in json:
        radius = validate(json['rim'], 'radius')
        young_mod = validate(json['rim'], 'young_mod')
        shear_mod = validate(json['rim'], 'shear_mod')
        density = validate(json['rim'], 'density')

        if json['rim']['section_type'] == 'general':
            area = validate(json['rim']['section_params'], 'area')
            I_rad = validate(json['rim']['section_params'], 'I_rad')
            I_lat = validate(json['rim']['section_params'], 'I_lat')
            J_tor = validate(json['rim']['section_params'], 'J_tor')
            I_warp = validate(json['rim']['section_params'], 'I_warp')
        else:
            raise TypeError("Invalid rim section type '{:s}'"
                            .format(json['rim']['section_type']))

        w.rim = Rim(radius=radius, area=area,
                    I_rad=I_rad, I_lat=I_lat, J_tor=J_tor, I_warp=I_warp,
                    young_mod=young_mod, shear_mod=shear_mod, density=density)


    else:
        raise KeyError('Rim definition not found in POST JSON')

    return w

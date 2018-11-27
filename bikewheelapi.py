from flask import Flask, jsonify, make_response, request
from bikewheelcalc import *


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

    wheel = wheel_from_json(request.json)
    mm = ModeMatrix(wheel, N=24)
    F_ext = F_ext_from_json(request.json, mm)

    K = (mm.K_rim(tension=True, r0=True) +
         mm.K_spk(tension=True, smeared_spokes=False))

    try:
        dm = np.linalg.solve(K, F_ext)
    except Exception as e:
        raise e

    # Not implemented
    return make_response('', 501)

@app.route('/tensions', methods=['POST'])
def get_tensions():
    'Return the spoke tensions of a wheel under a set of loads'

    # Not implemented
    return make_response('', 501)

@app.route('/stiffness', methods=['POST'])
def get_stiffness():
    'Return stiffness properties of a wheel'

    # Build wheel from POST data
    w = wheel_from_json(request.json)

    K_rad = calc_rad_stiff(w)
    K_lat = calc_lat_stiff(w)
    K_tor = calc_tor_stiff(w)

    return jsonify({'radial_stiffness': K_rad,
                    'lateral_stiffness': K_lat,
                    'torsional_stiffness': K_tor}), 200


# ---------------------------------- MODEL --------------------------------- #
# Define functions to calculate wheel results                                #
# -------------------------------------------------------------------------- #

def F_ext_from_json(json, mode_matrix):
    'Calculate modal force vector from JSON'

    # Start with empty force vector
    F_ext = mode_matrix.F_ext(f_theta=0., f=[0., 0., 0., 0.])

    if 'forces' in json:
        for f in json['forces']:
            if 'magnitude' in f:

                mag = np.array(f['magnitude'])
                if len(mag) < 4:
                    mag = np.pad(mag, (0, 4 - len(mag)))
            else:
                fc = {'f_rad': 0., 'f_lat': 0., 'f_tan': 0., 'm_tor': 0.}
                fc.update(f)

                mag = np.array([fc['f_lat'], fc['f_rad'], fc['f_tan'], fc['m_tor']])

            F_ext = F_ext + mode_matrix.F_ext(f_theta=f['location'], f=mag)

    return F_ext

def wheel_from_json(json):
    'Create a BicycleWheel object from JSON'

    w = BicycleWheel()

    # Hub
    w.hub = Hub(diameter=float(json['hub']['diameter']),
                width_nds=float(json['hub']['width_nds']),
                width_ds=float(json['hub']['width_ds']))

    # Rim
    if 'rim' in json:

        if json['rim']['section_type'] == 'general':
            area = float(json['rim']['section_params']['area'])
            I_rad = float(json['rim']['section_params']['I_rad'])
            I_lat = float(json['rim']['section_params']['I_lat'])
            J_tor = float(json['rim']['section_params']['J_tor'])
            I_warp = float(json['rim']['section_params']['I_warp'])
        else:
            raise TypeError("Invalid rim section type '{:s}'"
                            .format(json['rim']['section_type']))

        w.rim = Rim(radius=float(json['rim']['radius']), area=area,
                    I_rad=I_rad, I_lat=I_lat, J_tor=J_tor, I_warp=I_warp,
                    young_mod=float(json['rim']['young_mod']),
                    shear_mod=float(json['rim']['shear_mod']),
                    density=float(json['rim']['density']))

    else:
        raise KeyError('Rim definition not found in POST JSON')

    # Spokes
    if 'spokes' in json:
        w.lace_cross(n_spokes=int(json['spokes']['num']),
                     n_cross=int(json['spokes']['num_cross']),
                     diameter=float(json['spokes']['diameter']),
                     young_mod=float(json['spokes']['young_mod']),
                     density=float(json['spokes'].get('density', 0.)),
                     offset=float(json['spokes'].get('offset', 0.)))

    elif 'spokes_ds' in json and 'spokes_nds' in json:
        w.lace_cross_ds(n_spokes=int(json['spokes_ds']['num']),
                        n_cross=int(json['spokes_ds']['num_cross']),
                        diameter=float(json['spokes_ds']['diameter']),
                        young_mod=float(json['spokes_ds']['young_mod']),
                        density=float(json['spokes_ds'].get('density', 0.)),
                        offset=float(json['spokes_ds'].get('offset', 0.)))

        w.lace_cross_nds(n_spokes=int(json['spokes_nds']['num']),
                         n_cross=int(json['spokes_nds']['num_cross']),
                         diameter=float(json['spokes_nds']['diameter']),
                         young_mod=float(json['spokes_nds']['young_mod']),
                         density=float(json['spokes_nds'].get('density', 0.)),
                         offset=float(json['spokes_nds'].get('offset', 0.)))
    else:
        raise KeyError('Missing or invalid spokes definition in POST JSON')

    return w

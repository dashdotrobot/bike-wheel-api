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

    # Solve for modal deformation vector
    try:
        dm = np.linalg.solve(K, F_ext)
    except Exception as e:
        raise e

    # What values of theta to calculate deflection at
    if 'theta_range' in request.json['result']:
        if len(request.json['result']['theta_range']) == 2:
            theta_range = (request.json['result']['theta_range'][0],
                           request.json['result']['theta_range'][1],
                           100)
        else:
            theta_range = request.json['result']['theta_range']

        theta = np.linspace(float(theta_range[0]),
                            float(theta_range[1]),
                            int(theta_range[2]))
    elif 'theta' in request.json['result']:
        theta = np.array(request.json['result']['theta'])
    else:
        theta = np.linspace(0., 2*np.pi, 50)  # Default range

    Bu = mm.B_theta(theta=theta, comps=0)
    Bv = mm.B_theta(theta=theta, comps=1)
    Bw = mm.B_theta(theta=theta, comps=2)
    Bp = mm.B_theta(theta=theta, comps=3)

    result = {'result': {
        'theta': theta.tolist(),
        'def_lat': Bu.dot(dm).tolist(),
        'def_rad': Bv.dot(dm).tolist(),
        'def_tan': Bw.dot(dm).tolist(),
        'def_tor': Bp.dot(dm).tolist()
    }}

    return jsonify(result), 200

@app.route('/tensions', methods=['POST'])
def get_tensions():
    'Return the spoke tensions of a wheel under a set of loads'

    wheel = wheel_from_json(request.json)
    mm = ModeMatrix(wheel, N=24)
    F_ext = F_ext_from_json(request.json, mm)

    K = (mm.K_rim(tension=True, r0=True) +
         mm.K_spk(tension=True, smeared_spokes=False))

    # Solve for modal deformation vector
    try:
        dm = np.linalg.solve(K, F_ext)
    except Exception as e:
        raise e

    # Which spokes to return results for
    if 'spokes_range' in request.json['result']:
        if len(request.json['result']['spoke_range']) == 2:
            spokes_range = (request.json['result']['spoke_range'][0],
                            request.json['result']['spoke_range'][1],
                            1)
        else:
            spokes_range = request.json['result']['spoke_range']

        spokes = list(range(int(theta_range[0]),
                            int(theta_range[1]),
                            int(theta_range[2])))
    elif 'spokes' in request.json['result']:
        spokes = np.atleast_1d(np.array(request.json['result']['spokes'])).tolist()
    else:
        spokes = list(range(len(wheel.spokes)))  # Default: all spokes

    # Calculate spoke tensions
    dT = [-wheel.spokes[s].EA/wheel.spokes[s].length *
          np.dot(wheel.spokes[s].n,
                 mm.B_theta(wheel.spokes[s].rim_pt[1], comps=[0, 1, 2]).dot(dm))
          for s in spokes]

    tension = [wheel.spokes[s].tension + dt for s, dt in zip(spokes, dT)]

    result = {'result': {
        'spokes': spokes,
        'tension': tension,
        'd_tension': dT
    }}

    # Not implemented
    return jsonify(result), 200

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


# --------------------------------- HELPERS -------------------------------- #
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

        w.apply_tension(T_right=float(json['spokes'].get('tension', 0.)))

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

        w.apply_tension(T_right=float(json['spokes_ds'].get('tension', 0.)))

    else:
        raise KeyError('Missing or invalid spokes definition in POST JSON')

    return w

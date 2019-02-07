import json
import numpy as np
from bikewheelcalc import *
from numpy.linalg import LinAlgError


# --------------------------------- ROUTES --------------------------------- #
# Define application endpoints                                               #
# -------------------------------------------------------------------------- #

def calculate(event, context):
    'Perform the calculations requested in the JSON POST object'

    status_code = 200
    response = {}

    # Parse request JSON
    try:
        request = json.loads(event['body'])
    except Exception as e:
        response = {'success': False, 'error': 'Unable to parse request JSON'}
        return return_response(200, response)

    # Build the wheel
    try:
        wheel = wheel_from_json(request['wheel'])
        response['wheel'] = request['wheel']
    except Exception as e:
        response = {'success': False, 'error': str(e)}
        return return_response(200, response)

    try:
        if 'tension' in request:
            response['tension'] = solve_tensions(wheel, request['tension'])

        if 'deformation' in request:
            response['deformation'] = solve_deformation(wheel, request['deformation'])

        if 'stiffness' in request:
            response['stiffness'] = solve_stiffness(wheel, request['stiffness'])

        if 'buckling_tension' in request:
            response['buckling_tension'] = solve_buckling_tension(wheel, request['buckling_tension'])

        if 'mass' in request:
            response['mass'] = solve_mass(wheel, request['mass'])

    except:
        response = {'success': False, 'error': 'Unknown error'}

    return return_response(200, response)

def return_response(status_code, response):

    return {
        'statusCode': status_code,
        'headers': {
            "Access-Control-Allow-Headers": 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-requested-with',
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": 'POST,GET,OPTIONS'},
        'body': json.dumps(response),
        'isBase64Encoded': False
    }


# --------------------------------- HELPERS -------------------------------- #
# Define functions to build wheel objects                                    #
# -------------------------------------------------------------------------- #

def F_ext_from_json(json, mode_matrix):
    'Calculate modal force vector from JSON'

    # Start with empty force vector
    F_ext = mode_matrix.F_ext(theta=0., f=[0., 0., 0., 0.])

    for f in json:
        if 'magnitude' in f:

            mag = np.array(f['magnitude'])
            if len(mag) < 4:
                mag = np.pad(mag, (0, 4 - len(mag)))
        else:
            fc = {'f_rad': 0., 'f_lat': 0., 'f_tan': 0., 'm_tor': 0.}
            fc.update(f)

            mag = np.array([fc['f_lat'], fc['f_rad'], fc['f_tan'], fc['m_tor']])

        F_ext = F_ext + mode_matrix.F_ext(theta=f['location'], f=mag)

    return F_ext

def a_adj_from_json(json, wheel):
    'Create vector of spoke adjustments'

    # Check that json is a list
    if not (hasattr(json, "__iter__") or hasattr(json, "__getitem__")):
        raise ValueError('spoke_adjustments must be either a numeric vector or a list of {spoke: [s], adjustment: [f]} objects')

    # Check to see if list items are numeric
    if all([isinstance(a, float) for a in json]):
        if len(json) == len(wheel.spokes):
            return np.array(json)
        else:
            raise ValueError('Length of spoke_adjustments array must be equal to number of spokes')
    else:
        a = np.zeros(len(wheel.spokes))
        for j in json:
            try:
                a[int(j['spoke'])] = float(j['adjustment'])
            except Exception as e:
                raise ValueError('Error parsing spoke_adjustments')
        return a

def wheel_from_json(json):
    'Create a BicycleWheel object from JSON'

    w = BicycleWheel()

    # Create hub
    hub_params = {'diameter': None, 'diameter_ds': None, 'diameter_nds': None,
                  'width': None, 'width_ds': None, 'width_nds': None}
    hub_params.update((k, v) for k, v in json['hub'].items() if k in hub_params)

    w.hub = Hub(**hub_params)

    # Rim
    if 'rim' in json:

        if json['rim']['section_type'] == 'general':
            area = float(json['rim']['section_params']['area'])
            I_rad = float(json['rim']['section_params']['I_rad'])
            I_lat = float(json['rim']['section_params']['I_lat'])
            J_tor = float(json['rim']['section_params']['J_tor'])
            I_warp = float(json['rim']['section_params'].get('I_warp', 0.))
        else:
            raise TypeError("Invalid rim section type '{:s}'"
                            .format(json['rim']['section_type']))

        w.rim = Rim(radius=float(json['rim']['radius']), area=area,
                    I_rad=I_rad, I_lat=I_lat, J_tor=J_tor, I_warp=I_warp,
                    young_mod=float(json['rim']['young_mod']),
                    shear_mod=float(json['rim']['shear_mod']),
                    density=float(json['rim'].get('density', 0.)))

    else:
        raise KeyError('Missing or invalid rim definition in POST JSON')

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


# --------------------------------- SOLVERS -------------------------------- #
# Define handlers to fulfill calculation requests                            #
# -------------------------------------------------------------------------- #

def solve_tensions(wheel, json):
    'Calculate spoke tensions under the specified loads'

    warnings = []
    
    # Mode matrix model
    mm = ModeMatrix(wheel, N=24)

    # External forces
    F_ext = mm.F_ext(theta=0., f=[0., 0., 0., 0.])
    try:
        F_ext = F_ext_from_json(json['forces'], mm)
    except:
        warnings.append('Missing or invalid forces object')

    # Spoke adjustments
    a_adj = np.zeros(len(wheel.spokes))
    try:
        a_adj = a_adj_from_json(json['spoke_adjustments'], wheel)
    except Exception as e:
        warnings.append('Missing or invalid spoke adjustments object')

    # Build stiffness matrix
    K = (mm.K_rim(tension=True, r0=True) +
         mm.K_spk(tension=True, smeared_spokes=False))

    # Solve for modal deformation vector
    try:
        dm = np.linalg.solve(K, F_ext + mm.A_adj().dot(a_adj))
    except Exception as e:
        return {'success': False, 'error': 'Linear algebra error'}

    # Which spokes to return results for
    if 'spokes_range' in json:
        if len(json['spokes_range']) == 2:
            spokes_range = (json['spokes_range'][0],
                            json['spokes_range'][1],
                            1)
        else:
            spokes_range = json['spokes_range']

        spokes = list(range(int(spokes_range[0]),
                            int(spokes_range[1]),
                            int(spokes_range[2])))

    elif 'spokes' in json:
        spokes = np.atleast_1d(np.array(json['spokes'])).tolist()
    else:
        spokes = list(range(len(wheel.spokes)))  # Default: all spokes

    # Calculate spoke tensions
    dT = mm.spoke_tension_change(dm=dm, a=a_adj)[spokes].tolist()

    tension = [wheel.spokes[s].tension + dt for s, dt in zip(spokes, dT)]
    tension_0 = [wheel.spokes[s].tension for s in spokes]

    return {
        'success': True,
        'warnings': warnings,
        'spokes': spokes,
        'tension': tension,
        'tension_initial': tension_0,
        'tension_change': dT
    }

def solve_deformation(wheel, json):
    'Calculate the deformation of the wheel under the specified loads'

    # Mode matrix model
    mm = ModeMatrix(wheel, N=24)

    if 'forces' in json:
        F_ext = F_ext_from_json(json['forces'], mm)
    else:
        return {'success': False, 'error': 'Missing or invalid forces object'}

    # Build stiffness matrix
    K = (mm.K_rim(tension=True, r0=True) +
         mm.K_spk(tension=True, smeared_spokes=False))

    # Solve for modal deformation vector
    try:
        dm = np.linalg.solve(K, F_ext)
    except Exception as e:
        return {'success': False, 'error': 'Linear algebra error'}

    # What values of theta to calculate deflection at
    if 'theta_range' in json:
        if len(json['theta_range']) == 2:
            theta_range = (json['theta_range'][0],
                           json['theta_range'][1],
                           100)
        else:
            theta_range = json['theta_range']

        theta = np.linspace(float(theta_range[0]),
                            float(theta_range[1]),
                            int(theta_range[2]))
    elif 'theta' in json:
        theta = np.array(json['theta'])
    else:
        theta = np.linspace(0., 2*np.pi, 50)  # Default range

    Bu = mm.B_theta(theta=theta, comps=0)
    Bv = mm.B_theta(theta=theta, comps=1)
    Bw = mm.B_theta(theta=theta, comps=2)
    Bp = mm.B_theta(theta=theta, comps=3)

    return {
        'success': True,
        'theta': theta.tolist(),
        'def_lat': Bu.dot(dm).tolist(),
        'def_rad': Bv.dot(dm).tolist(),
        'def_tan': Bw.dot(dm).tolist(),
        'def_tor': Bp.dot(dm).tolist()
    }

def solve_stiffness(wheel, json):
    'Calculate wheel stiffness'

    try:
        K_rad = calc_rad_stiff(wheel)
        K_lat = calc_lat_stiff(wheel)
        K_tor = calc_tor_stiff(wheel)

    except LinAlgError:
        return {'success': False, 'error': 'Linear algebra error'}
    except:
        return {'success': False, 'error': 'Unknown error'}

    return {
        'success': True,
        'radial_stiffness': K_rad,
        'lateral_stiffness': K_lat,
        'torsional_stiffness': K_tor
    }

def solve_buckling_tension(wheel, json):
    'Calculate buckling tension'

    if 'approx' in json:
        approx = json['approx']
    else:
        approx = 'linear'

    try:
        Tc, nc = calc_buckling_tension(wheel, approx=approx)
    except ValueError as e:
        return {'success': False, 'error': str(e)}
    except:
        return {'success': False, 'error': 'Unknown error'}

    return {
        'success': True,
        'approx': approx,
        'buckling_tension': Tc,
        'buckling_mode': nc
    }

def solve_mass(wheel, json):
    'Calculate mass properties'

    mass = wheel.calc_mass()
    mass_rim = wheel.rim.calc_mass()

    rot = wheel.calc_rot_inertia()
    rot_rim = wheel.rim.calc_rot_inertia()

    mass_eff = mass + rot / wheel.rim.radius**2

    return {
        'success': True,
        'mass': mass,
        'mass_rim': mass_rim,
        'mass_spokes': mass - mass_rim,
        'mass_rotational': mass_eff,
        'inertia': rot,
        'inertia_rim': rot_rim,
        'inertia_spokes': rot - rot_rim,
    }

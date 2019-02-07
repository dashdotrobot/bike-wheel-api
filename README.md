# Bike Wheel Calc API

RESTful service written in Python/Flask for calculating mechanical properties of bicycle wheels, and simulating deformation and spoke tensions under external loads.

## Usage

The server accepts a single JSON object using the POST method. The request object must contain a `wheel` object, and any combination of optional calculation requests. The request object has the following format:

```
{
  wheel: {...}        # Required
  tension: {...}      # Optional: calculate spoke tensions under the given loads
  deformation: {...}  # Optional: calculate deformation under the given loads
  stiffness: {...}    # Optional: calculate stiffnesses
  mass: {...}         # Optional: calculate mass and inertia properties
}
```

The server responds with a JSON object with the results of the requested calculations, or descriptions of any errors.

### The `wheel` object

The `wheel` object defines the properties of the wheel. It has the following format:

```
wheel: {
  hub: {             # Required: Properties of the hub
    diameter: <m>      # Hub flange diameter (if same on both sides) (required if diameter_ds and diameter_nds are omitted)
    width: <m>         # Lateral distance between hub flanges (required if width_ds and width_nds are omitted)
    diameter_ds: <m>   # Lateral distance from rim to drive-side hub flange
    diameter_nds: <m>  # Lateral distance from rim to non-drive-side hub flange
    width_ds: <m>      # Lateral distance from rim to drive-side hub flange
    width_nds: <m>     # Lateral distance from rim to non-drive-side hub flange
  },
  rim: {...}         # Required: Properties of the rim
  spokes: {...}      # Properties of the spokes (required if spokes_ds and spokes_nds are omitted)
  spokes_ds: {...}   # Properties of the drive-side spokes (required if spokes is omitted)
  spokes_nds: {...}  # Properties of the non-drive-side spokes (required if spokes is omitted)
}
```

For the options `hub->diameter`, `hub->width`, and `spokes`, EITHER the symmetric option must be specified, or both `<option>_ds` and `<option>_nds` must be specified.

The `rim` object has the following format:

```
rim: {
  radius: <m>               # Required: Radius of the rim (at its shear center)
  young_mod: <Pa>           # Required: Young's modulus of the rim material
  shear_mod: <Pa>           # Required: Shear modulus of the rim material
  density: <kg/m^3>         # Optional (default 0): Density of the rim material
  section_type: "general"   # Required: Rim cross-section type (currently only "general" is supported)
  section_params: {...}     # Required: Rim cross-section properties
}
```

In the future, other cross-section types may be available. Currently, the `section_params` object must specify all the section stiffness constants:

```
section_params: {
  area: <m^2>     # Required: Cross-sectional area
  I_rad: <m^4>    # Required: Second moment of area for radial bending
  I_lat: <m^4>    # Required: Second moment of area for lateral bending
  J_tor: <m^4>    # Required: Torsion constant
  I_warp: <m^6>   # Optional (default 0): Warping constant
}
```

The `spokes`, `spokes_ds`, or `spokes_nds` objects have the following identical format:

```
<spokes | spokes_ds | spokes_nds>: {
  num: <integer>        # Required: Number of spokes
  num_cross: <integer>  # Required: Number of crossings in spoke pattern (e.g. 3)
  diameter: <m>         # Required: Spoke diameter
  offset: <m>           # Optional (default 0): Lateral offset of the spoke nipple from rim centerline (positive=towards hub flange)
  young_mod: <Pa>       # Required: Young's modulus of the spoke material
  density: <kg/m^3>     # Optional (default 0): Density of the spoke material
}
```

If `spokes` is specified, then `spokes->num` is the total number of spokes in the wheel. If `spokes_ds` and `spokes_nds` are specified, `spokes_(ds|nds)->num` is the number of spokes on that side only.

### Calculating spoke tensions

Include the `tension` request object to calculate the new spoke tensions in a wheel subject to external forces. The request has the following form:

```
tension: {
  forces: [                                                    # Optional: List of force objects
    {location: <radians>, f_rad: <N>}                          # A single radial force
    {location: <radians>, f_lat: <N>, f_tan: <N>}              # OR use any combination of f_lat, f_rad, f_tan, and m_tor
    {location: <radians>, magnitude: [<N>, <N>, <N>, <N-m>]}   # OR specify a force vector (plus torque)
    ...
  ],
  spoke_adjustments: [                        # Optional: List of spoke adjustments
    <m>, <m>, <m>, <m>, ...                   # Either a list of spoke adjustments (in meters)
                                              # OR
    {spoke: <integer>, adjustment: <m>},      # List of spoke adjustment objects
    {spoke: <integer>, adjustment: <m>},
    ...
  ],
  spokes: [<list of spoke indices, starting at 0>]  # Optional: List of spokes to calculate results for
  spokes_range: [<start>, <stop>, <step>]           # Optional: Range of spokes to calculate results for
}
```

The response has the following form:

```
tension: {
  success: <true | false>    # Whether calculation was successful
  error: 'String'            # Optional: Description of error if one occurred
  spokes: [...]              # List of spoke indices for which results have been calculated
  tension: [<N>...]          # List of spoke tensions in the deformed wheel
  tension_initial: [<N>...]  # List of initial spoke tensions in the undeformed wheel
  tension_change: [<N>...]   # List of changes in spoke tension. Equivalent to tension - tension_initial
}
```

#### The `forces` object

Any number of force objects may be supplied, either in dictionary format or in vector format. In dictionary format, any combination of `f_rad`, `f_lat`, `f_tan`, and `m_tor` may be supplied in units of Newtons (for forces) or Newton-meters for `m_tor`. E.g.,

```
{location: 0, f_rad: 50, f_lat: -10}
```

defines a radial force of 50 Newtons and a lateral force of -10 Newtons, both applied at 0 radians (the "bottom" of the wheel). In vector format, the `magnitude` object defines a force vector in `[f_lat, f_rad, f_tan, m_tor]` format. If the vector length is less than 4, the remaining forces will be zero. E.g.,

```
[location: 3.1415, magnitude: [10, 5]}
```

defines a lateral force of 10 Newtons and a radial force of 5 Newtons, both applied at 3.1415 radians (the "top" of the wheel).

#### The `spoke_adjustments` list

Spoke adjustments may be specified either as a numeric list of spoke length adjustments (the list must have a length equal to the number of spokes):

```
[<adjustment to spoke 0>, <adjustment to spoke 1>, ... <adjustment to spoke n_s>]
```

__OR__ as a list of adjustments to selected spokes:

```
[
  {spoke: <integer>, adjustment: <m>},  # First spoke to be adjusted
  {spoke: <integer>, adjustment: <m>},  # Second spoke to be adjusted
  ...
  {spoke: <integer>, adjustment: <m>}   # Specify as many spokes as desired (up to max. n_s)
]
```

These formats may not be mixed.

The spoke adjustment specifies the length change due to the adjustment ONLY, e.g. a full turn on a standard spoke nipple (56 threads per inch) is equal to 0.0254/56 meters. Positive adjustment means the spoke gets tighter (shorter).

#### The `spokes` or `spokes_range` object

Optionally specify certain spokes to calculate results for. If both `spokes` and `spokes_range` are omitted, the default is all spokes. The `spokes` object defines a list of spoke indices, in any order. The index of the first spoke is 0. The `spokes_range` object defines a range of spokes with a <start> index, <stop> index, and <step>. The <stop> index is omitted. E.g.,
  
```
spokes_range: [0, 10, 2]
```

will calculate results for spokes `[0, 2, 4, 6, 8]`, but not `10`. If the `<step>` parameter is omitted, it will default to a step of 1.

### Calculating wheel deformation

Include the `deformation` request object to calculate the distortion of the rim when the wheel is subject to external forces. The request has the following form:

```
deformation: {
  forces: [...]                             # Same format as in the tension request object
  spoke_adjustments: [...]                  # Same format as in the tension request object
  theta: [<radians>...]                     # Optional: List of angular positions at which to calculate the deformation
  theta_range: [<start>, <stop>, <number>]  # Optional: Range of angular positions
}
```

The response has the following form:

```
deformation: {
  success: <true | false>  # Whether calculation was successful
  error: 'String'          # Optional: Description of error if one occurred
  theta: [<radians>...]    # List of angular positions where results are given
  def_lat: [<m>...]        # Lateral deflection of the rim, in meters
  def_rad: [<m>...]        # Radial deflection of the rim, in meters
  def_tan: [<m>...]        # Tagential deflection of the rim, in meters
  def_tor: [<m>...]        # Torsional 'twist' of the rim around its own axis, in radians
}
```

#### The `theta` or `theta_range` object

Optionally specify specific points on the rim, by angular coordinate, at which to calculate the deformation. If neither is specified, the default is 100 equally-spaced points around the rim. The `theta` object defines a list of coordinates, in any order. The `theta_range` object defines a range of `<num>` equally-spaced points between (and including) `<start>` and `<stop>`. If `<num>` is omitted it will default to 100.

### Calculating wheel stiffness

Include the `stiffness` request object to calculate the principle stiffnesses of the wheel. The request object has no parameters. Simply supply an empty object.

The response has the following form:

```
stiffness: {
  success: <true | false>       # Whether calculation was successful
  error: 'String'               # Optional: Description of error if one occurred
  radial_stiffness: <N/m>       # Radial stiffness at theta=0
  lateral_stiffness: <N/m>      # Lateral stiffness at theta=0
  torsional_stiffness: <N/rad>  # Torsional (wind-up) stiffness at theta=0
}
```

Each stiffness is calculated by applying a single force at theta=0 with unit magnitude in the respective direction and calculating the deformation in that same direction. Therefore, the torsional stiffness is approximately, but not exactly, equal to the wind-up stiffness that would be expected when a force is applied at two points (e.g. during braking with rim brakes).

### Calculating mass properties

Include the `mass` request object to calculate the mass and rotational inertia of the wheel and individual components. The request object has no parameters.

The response has the following form:

```
mass: {
  mass: <kg>,               # Mass of the wheel (minus hub) in kilograms
  mass_rim: <kg>,           # Mass of the rim
  mass_spokes: <kg>,        # Mass of the spokes (equivalent to mass - mass_rim)
  mass_rotational: <kg>,    # Effective rotating mass of the wheel in kilograms
  inertia: <kg-m^2>,        # Rotational inertia of the wheel in kilogram meters squared
  inertia_rim: <kg-m^2>,    # Rotational inertia of the rim
  inertia_spokes: <kg-m^2>  # Rotational inertia of the spokes (equivalent to inertia - inertia_rim)
}
```

The effective rotating mass is the mass which is felt when accelerating the bicycle. It is equal to the mass of an object which would require the same energy to bring to a constant velocity V as would be required to bring a rolling bicycle wheel to a constant center-of-mass velocity V, with no slipping. The effective rotating mass of a wheel has theoretical minimum of `1.333*mass` and a theoretical maximum of `2*mass`, assuming that the spokes do not taper towards the rim and the rim rolls on its circumference.

### Calculating buckling tension

Include the `buckling_tension` request object to calculate the critical buckling tension. The request object has the following form:

```
buckling_tension: {
  approx: <linear | quadratic | small_mu>  # (Optional, default=linear)
}
```

The optional argument `approx` specifies which equation should be used to calculate the buckling tension.
* `linear` uses Eqn. (4.4) from reference [1]
* `quadratic` uses Eqn. (4.3) from reference [1]
* `small_mu` uses Eqn. (4.10) from reference [1]

The response has the following form:

```
buckling_tension: {
  success: <true | false>                  # Whether calculation was successful
  error: 'String'                          # Optional: Description of error if one occurred
  approx: <linear | quadratic | small_mu>  # The approximation used
  buckling_tension: <N>                    # The critical tension in Newtons
  buckling_mode: <number>                  # The critical buckling mode number
}
```

If the `small_mu` approximation is used, the `buckling_mode` need not be an integer.

## References

[1] Matthew Ford, [Reinventing the Wheel: Stress Analysis, Stability, and Optimization of the Bicycle Wheel](https://github.com/dashdotrobot/phd-thesis/releases/download/v1.0/Ford_BicycleWheelThesis_v1.0.pdf), Ph.D. Thesis, Northwestern University (2018)

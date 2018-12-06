# Bike Wheel Calc API

RESTful service for calculating mechanical properties of bicycle wheels, and simulating deformation and spoke tensions under external loads.

## Usage

The server accepts a single JSON object using the POST method. The request object must contain a `wheel` object, and any combination of optional calculation requests.

```
{
  wheel: {...},        # Required
  tension: {...},      # Optional: calculate spoke tensions under the given loads
  deformation: {...},  # Optional: calculate deformation under the given loads
  stiffness: {...},    # Optional: calculate stiffnesses
  mass: {...}          # Optional: calculate mass and inertia properties
}
```

The server responds with a JSON object with the results of the requested calculations, or descriptions of any errors.

### Calculating spoke tensions

Include the `tension` request object to calculate the new spoke tensions in a wheel subject to external forces. The request has the following form:

```
tension: {
  forces: [                                                    # Required: List of force objects
    {location: <radians>, f_rad: <N>},                         # A single radial force
    {location: <radians>, f_lat: <N>, f_tan: <N>},             # OR use any combination of f_lat, f_rad, f_tan, and m_tor
    {location: <radians>, magnitude: [<N>, <N>, <N>, <N-m>]},  # OR specify a force vector (plus torque)
    ...
  ],
  spokes: [<list of spoke indices, starting at 0>],  # Optional: List of spokes to calculate results for
  spokes_range: [<start>, <stop>, <step>]            # Optional: Range of spokes to calculate results for
}
```

The response has the following form:

```
tension: {
  success: <true | false>,    # Whether calculation was successful
  error: 'String',            # Optional: Description of error if one occurred
  spokes: [...],              # List of spoke indices for which results have been calculated
  tension: [<N>...],          # List of spoke tensions in the deformed wheel
  tension_initial: [<N>...],  # List of initial spoke tensions in the undeformed wheel
  tension_change: [<N>...]    # List of changes in spoke tension. Equivalent to tension - tension_initial
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
  forces: [...],                             # Same format as in the tension request object
  theta: [<radians>...],                     # Optional: List of angular positions at which to calculate the deformation
  theta_range: [<start>, <stop>, <number>]   # Optional: Range of angular positions
}
```

The response has the following form:

```
deformation: {
  success: <true | false>,    # Whether calculation was successful
  error: 'String',            # Optional: Description of error if one occurred
  theta: [<radians>...],      # List of angular positions where results are given
  def_lat: [<m>...],          # Lateral deflection of the rim, in meters
  def_rad: [<m>...],          # Radial deflection of the rim, in meters
  def_tan: [<m>...],          # Tagential deflection of the rim, in meters
  def_tor: [<m>...],          # Torsional 'twist' of the rim around its own axis, in radians
}
```

#### The `theta` or `theta_range` object

Optionally specify specific points on the rim, by angular coordinate, at which to calculate the deformation. If neither is specified, the default is 100 equally-spaced points around the rim. The `theta` object defines a list of coordinates, in any order. The `theta_range` object defines a range of `<num>` equally-spaced points between (and including) `<start>` and `<stop>`. If `<num>` is omitted it will default to 100.

### Calculating wheel stiffness

Include the `stiffness` request object to calculate the principle stiffnesses of the wheel. The request object has no parameters. Simply supply an empty object.

The response has the following form:

```
stiffness: {
  radial_stiffness: <N/m>,      # Radial stiffness at theta=0
  lateral_stiffness: <N/m>,     # Lateral stiffness at theta=0
  torsional_stiffness: <N/rad>  # Torsional (wind-up) stiffness at theta=0
}
```

Each stiffness is calculated by applying a single force with unit magnitude in the respective direction and calculating the deformation in that same direction. Therefore, the torsional stiffness is approximately, but not exactly, equal to the wind-up stiffness that would be expected when a force is applied at two points (e.g. during braking with rim brakes).

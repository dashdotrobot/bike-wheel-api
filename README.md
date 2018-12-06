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
  spokes_range: {[<start>, <stop>, <step>]           # Optional: Range of spokes to calculate results for
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

will calculate results for spokes `[0, 2, 4, 6, 8]`, but not `10`.

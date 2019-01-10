from typing import NewType


# The only purpose these types serve is for the units of function parameters to appear in PyCharm's parameter info
# popup.
Length = NewType('m', float)
Area = NewType('m²', float)
Volume = NewType('m³', float)
Density = NewType('kg/m³', float)
Acceleration = NewType('m/s²', float)
SurfaceTension = NewType('N/m', float)

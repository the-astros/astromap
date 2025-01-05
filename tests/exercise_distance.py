import numpy as np

from astromap.star import PolarCoordinates

# """calculate angular distance between two points on unit sphere

# with polar coords (azimuth, zenith) for two points on the sphere a, b:
# aa: azimuth a
# az: zenith a
# ba: azimuth b
# bz: zenith b

# distance = arccos(sin(az)sin(bz) + cos(az)cos(bz)cos(ba - aa))
# """
# return np.arccos(
#     (np.sin(az) * np.sin(bz))
#     + (np.cos(az) * np.cos(bz) * np.cos(ba - aa))
# )


def distance(a: PolarCoordinates, b: PolarCoordinates) -> float:
  delta_azimuth: float = np.min(np.abs(a.azimuth - b.azimuth), (2 * np.pi) - np.abs(a.azimuth - b.azimuth))
  return 0.0



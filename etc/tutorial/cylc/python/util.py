# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office - GNU V3+.
# This is illustrative code developed for tutorial purposes, it is not
# intended for scientific use and is not guarantied to be accurate or correct.
# -----------------------------------------------------------------------------
from copy import copy
import math
import jinja2


R_0 = 6371.  # Radius of the Earth (km).
DEG2RAD = math.pi / 180.  # Conversion from degrees to radians.


def frange(start, stop, step):
    """Implementation of python's xrange which works with floats."""
    while start < stop:
        yield start
        start += step


def read_csv(filename, cast=float):
    """Reads in data from a 2D csv file.

    Args:
        filename (str): The path to the file to read.
        cast (function): A function to call on each value to convert the data
            into the desired format.

    """
    data = []
    with open(filename, 'r') as datafile:
        line = datafile.readline()
        while line:
            data.append(map(cast, line.split(',')))
            line = datafile.readline()
    return data


def write_csv(filename, matrix, fmt='%.2f'):
    """Write data from a 2D array to a csv format file."""
    with open(filename, 'w+') as datafile:
        for row in matrix:
            datafile.write(', '.join(fmt % x for x in row) + '\n')


def field_to_csv(field, x_range, y_range, filename):
    """Extrapolate values from the field and write them to a csv file.

    Args:
        filename (str): The path of the csv file to write to.
        field (function): A function of the form f(x, y) -> z.
        x_range (list): List of the x coordinates of the extrapolated grid.
            These are the extrapolation coordinates, the length of this list
            defines the size of the grid.
        x_range (list): List of the y coordinates of the extrapolated grid.
            These are the extrapolation coordinates, the length of this list
            defines the size of the grid.

    """
    with open(filename, 'w+') as csv_file:
        for itt_y in y_range:
            csv_file.write(', '.join('%.2f' % field(x, itt_y) for
                                     x in x_range) + '\n')


def generate_matrix(dim_x, dim_y, value=0.):
    """Generates a 2D list with the desired dimensions.

    Args:
        dim_x (int): The x-dimension of the matrix.
        dim_y (int): The y-dimension of the matrix.
        value: The default value for each cell of the matrix.

    """
    matrix = []
    for _ in range(dim_y):
        matrix.append([copy(value)] * dim_x)
    return matrix


def permutations(collection_1, collection_2):
    """Yield all permutations of two collections."""
    for val_1 in collection_1:
        for val_2 in collection_2:
            yield val_1, val_2


def great_arc_distance((lng_1, lat_1), (lng_2, lat_2)):
    """Compute the distance between two (lng, lat) coordinates in km.

    Uses the Haversine formula.

    Args:
        coorinate_1 (tuple): A 2-tuple (lng, lat) of the first coordinate.
        coorinate_2 (tuple): A 2-tuple (lng, lat) of the second coordinate.

    """
    lng_1 *= DEG2RAD
    lat_1 *= DEG2RAD
    lng_2 *= DEG2RAD
    lat_2 *= DEG2RAD
    return (
        2 * R_0 * math.asin(
            math.sqrt(
                (math.sin((lat_2 - lat_1) / 2.) ** 2) + (
                    math.cos(lat_1) *
                    math.cos(lat_2) *
                    (math.sin((lng_2 - lng_1) / 2.) ** 2)
                )
            )
        )
    )


def interpolate_grid(points, dim_x, dim_y, d_x, d_y, spline_order=0):
    """Interpolate 2D data onto a grid.

    Args:
        points (list): The points to interpolate as a list of 3-tuples
            (x, y, z).
        dim_x (int): The size of the grid in the x-dimension.
        dim_y (int): The size of the grid in the y-dimension.
        d_x (float): The grid spacing in the x-dimension.
        d_y (float): The grid spacing in the y-dimension.
        spline_order (int): The order of the beta-spline to use for
            interpolation (0 = nearset).

    Return:
        list - 2D matrix of dimensions dim_x, dim_y containing the interpolated
        data.

    """
    def spline_0(pos_x, pos_y, z_val):
        """Zeroth order beta spline (i.e. nearest point)."""
        return [(int(round(pos_x)), int(round(pos_y)), z_val)]  # [(x, y, z)]

    def spline_1(pos_x, pos_y, z_val):
        """First order beta spline (weight spread about four nearest ponts)."""
        x_0 = int(math.floor(pos_x))
        y_0 = int(math.floor(pos_y))
        x_1 = x_0 + 1
        y_1 = y_0 + 1
        return [
            # (x, y, z), ...
            (x_0, y_0, (x_0 + d_x - pos_x) * (y_0 + d_y - pos_y) * z_val),
            (x_1, y_0, (pos_x - x_0) * (y_0 + d_y - pos_y) * z_val),
            (x_0, y_1, (x_0 + d_x - pos_x) * (pos_y - y_0) * z_val),
            (x_1, y_1, (pos_x - x_0) * (pos_y - y_0) * z_val)
        ]

    if spline_order == 0:
        spline = spline_0
    elif spline_order == 1:
        spline = spline_1
    else:
        raise ValueError('Invalid spline order "%d" must be in (0, 1).' %
                         spline_order)

    grid = generate_matrix(dim_x, dim_y, 0.)

    for x_val, y_val, z_val in points:
        x_coord = x_val / d_x
        y_coord = y_val / d_y
        for grid_x, grid_y, grid_z in spline(x_coord, y_coord, z_val):
            try:
                grid[grid_y][grid_x] += grid_z
            except IndexError:
                # Grid point out of bounds => skip.
                pass

    return grid


def plot_vector_grid(filename, x_grid, y_grid):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print 'Plotting diasbled'
        return

    fig = plt.figure()
    x_coords = []
    y_coords = []
    z_coords = []
    for itt_x in range(len(x_grid[0])):
        for itt_y in range(len(x_grid)):
            x_coords.append(itt_x)
            y_coords.append(itt_y)
            z_coords.append((
                x_grid[itt_y][itt_x],
                y_grid[itt_y][itt_x]
            ))

    plt.quiver(x_coords,
               y_coords,
               [x[0] for x in z_coords],
               [y[1] for y in z_coords])
    fig.savefig(filename)


def get_grid_coordinates(lng, lat, domain, resolution):
    return (
        int((abs(lng - domain['lng1'])) // resolution),
        int((abs(lat - domain['lat1'])) // resolution))


class SurfaceFitter(object):
    """A 2D interpolation for random points.
    
    A standin for scipy.interpolate.interp2d

    Args:
        x_points (list): A list of the x coordinates of the points to
            interpolate.
        y_points (list): A list of the y coordinates of the points.
        z_points (list): A list of the z coordinates of the points.
        kind (str): String representing the order of the interpolation to
            perform (either linear, quadratic or cubic).

    Returns:
        function: fcn(x, y) -> z

    """

    def __init__(self, x_points, y_points, z_points, kind='linear'):
        self.points = zip(x_points, y_points, z_points)

        if kind == 'linear':
            self.power = 1.
        elif kind == 'quadratic':
            self.power = 2.
        elif kind == 'cubic':
            self.power = 3.
        else:
            raise ValueError('"%s" is not a valid interpolation method' % kind)

    def __call__(self, grid_x, grid_y):
        sum_value = 0.0
        sum_weight = 0.0
        z_val = None
        for x_point, y_point, z_point in self.points:
            d_x = grid_x - x_point
            d_y = grid_y - y_point
            if d_x == 0 and d_y == 0:
                # This point is exactly at the grid location we are
                # interpolating for, return this value.
                z_val = z_point
                break
            else:
                weight = 1. / ((math.sqrt(d_x ** 2 + d_y ** 2)) ** self.power)
                sum_weight += weight
                sum_value += weight * z_point

        if z_val is None:
            z_val = sum_value / sum_weight

        return z_val


def parse_domain(domain):
    bbox = map(float, domain.split(','))
    return {
        'lng1': bbox[0],
        'lat1': bbox[1],
        'lng2': bbox[2],
        'lat2': bbox[3]
    }


def generate_html_map(filename, data, domain, resolution):
    template = """<html>
  <head>
    <link rel="stylesheet"
          href="https://unpkg.com/leaflet@1.2.0/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.2.0/dist/leaflet.js"></script>
  </head>
  <body>
    <div id="map" style="width:100%;height:100%"></div>

    <script type="text/javascript">
      // Define the colours to display for the different rainfall values.
      // NOTE: Rainfall values range from 0 to 6+.
      function get_colour(value) {
          if (value < 0.1)
              return '#ffffff88';
          if (value < 0.5)
              return '#00F7FF';
          if (value < 1)
              return '#00AAFF';
          else if (value < 2)
              return '#0051FF';
          else if (value < 3)
              return '#6600FF';
          else if (value < 4)
              return '#AE00FF';
          else if (value < 5)
              return '#FF00EA';
          else
              return '#FF0055';
      }

      // Forecast data as dict {'lead_time': [2d data matrix]}.
      var data = {{ data }};

      // Annotate map with data.
      var lng;
      var lat;
      var rects;
      var times = [];
      var layers = [];
      for (let time in data) {
          rects = L.layerGroup();
          for (let pos_y in data[time]) {
              for (let pos_x in data[time][0]) {
                  lng = (pos_x * {{ resolution }}) + {{ lng_1 }};
                  lat = {{ lat_2}} - (pos_y * {{ resolution }});
                  L.rectangle(
                      [[lat, lng],
                      [lat + {{ resolution }}, lng + {{ resolution }}]],
                      {color: get_colour(data[time][pos_y][pos_x]),
                       weight: 0, fillOpacity: 0.5}).addTo(rects);
              }
          }
          layers.push(rects);
          times.push(time);
      }

      // Sort map layers lexicographically.
      var sorted_times = times.slice(0);  // Copy the times list.
      var fcsts = {};  // {'lead_time': L.LayerGroup}  Note dicts are ordered.
      sorted_times.sort();
      var ind;
      for (let time of sorted_times) {
          ind = times.indexOf(time);
          fcsts[times[ind]] = layers[ind];
      }

      // Create map.
      var map = L.map('map', {layers: [fcsts[sorted_times[0]]]});

      // Zoom / center map to fit domain.
      map.fitBounds([[{{lat_1}}, {{lng_1}}], [{{lat_2}}, {{lng_2}}]]);

      // Add mapp tiles.
      map.addLayer(
          L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'));

      // Add layer selector.
      L.control.layers(fcsts).addTo(map);
    </script>
  </body>
</html>"""

    with open(filename, 'w+') as html_file:
        html_file.write(jinja2.Template(template).render(
            resolution=resolution,
            lng_1=domain['lng1'],
            lng_2=domain['lng2'],
            lat_1=domain['lat1'],
            lat_2=domain['lat2'],
            data=data))

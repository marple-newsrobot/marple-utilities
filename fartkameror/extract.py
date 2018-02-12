#! /usr/bin/env python3
"""
 Extracts metadata about speeding cameras from various shape files.
 Will be slow, move data to a proper DB if that's a problem.
 Working with Python on shape files will never be efficient.

 Shapefiles are downloaded from “Lastkajen”, the data warehouse of
 Trafikverket. Select NVDB/Vägnummer + Mätplats.
 CRS should be SWEREF 99 TM.

"""
import json
import fiona
from shapely.geometry import shape, Point
from pyproj import Proj


CAMERA_FILE = "geo/trafikkameror_SEATKATK_Matplats.shp"
ROAD_FILE = "geo/vagnummerNVDB_DKVagnummer.shp"

projection = Proj(init="epsg:3006")
with fiona.open(CAMERA_FILE) as camera_collection:
    with fiona.open(ROAD_FILE) as road_collection:

        sections = {}  # Our output: A list of camera sections
        for camera in camera_collection:
            print("---")
            geom = shape(camera['geometry'])
            # A buffer of 1 is more than enough to find the road,
            # the cameras are placed quite accurately
            # We could start small and increase gradually,
            # but there is no need, really
            pnt = Point(geom.coords).buffer(1)
            for road in road_collection:
                line = shape(road['geometry'])
                if pnt.intersects(line):
                    section_id = camera["properties"]["ID"][:5]
                    road_number = road["properties"]["HUVUDNR"]
                    name = camera["properties"]["NAMN"]
                    eroad = (road["properties"]["EUROPAVÄG"] == "-1")
                    x, y, z = camera["geometry"]["coordinates"]
                    lon, lat = projection(x, y, inverse=True)
                    camera_obj = {
                        'name': name,
                        'x': x,
                        'y': y,
                        'lat': lat,
                        'lon': lon,
                        'direction': camera["properties"]["VINKEL"],
                    }
                    if section_id in sections:
                        sections[section_id]["count"] += 1
                        sections[section_id]["road_numbers"].add(road_number)
                        sections[section_id]["names"].append(name)
                        sections[section_id]["eroad"] |= eroad
                        sections[section_id]["cameras"].append(camera_obj)
                    else:
                        sections[section_id] = {
                            'id': section_id,
                            'count': 1,
                            'road_numbers': set([road_number]),
                            'names': [name],
                            'eroad': eroad,
                            'cameras': [camera_obj]
                        }
                    section_id = camera["properties"]["ID"][:5]
                    # continue
            print(sections)
        for k, v in sections.items():
            v["road_numbers"] = list(v["road_numbers"])
        json_str = json.dumps(sections)
        print(json_str)

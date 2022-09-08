# -*- coding: utf-8 -*-
# from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.dialects.sqlite import insert
# pip install sqlalchemy-utils
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, insert, delete, update, text
import json
# import geojson as geojson
# import pip
import requests
import numpy as np
from numpy import arctan2, cos, sin, sqrt, pi, power, append, diff, deg2rad
# import sqlalchemy as sqlalchemy
# !pip install geojson
import geojson


def init_db():
    try:
        global my_conn
        my_conn = create_engine("sqlite:///my_db.db")
        if not database_exists(my_conn.url):
            create_database(my_conn.url)
        meta = MetaData()
        global parking_data_table
        parking_data_table = Table(
            'parking_data', meta,
            Column('node_id', Integer, primary_key=True),
            Column('free_count', Integer),
            Column('occupied_count', Integer),
            Column('probability', Float)
        )

        meta.create_all(my_conn)
    except:
        print("Initiating DB ERROR")

def find_osm_node_id(coordinate):
    lat = coordinate[0]
    lon = coordinate[1]
        # get the way id - request json format of the reverse method of OSM librery nominatim
    try:
        request_url = "https://nominatim.openstreetmap.org/reverse?format=geojson&osm_type=N&lat=" + f'{lat:f}' + "&lon=" + f'{lon:f}'
        response = requests.get(request_url)
        way_id_response = json.loads(response.text)
        osm_type = way_id_response['features'][0]['properties']['osm_type']
        node_id = way_id_response['features'][0]['properties']['osm_id']
        if osm_type != "node":
            print("not node: " + str(node_id))

        return node_id
    except requests.exceptions.HTTPError as errh:
        print ("Http ERROR:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Connecting ERROR:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout ERROR:",errt)
    except requests.exceptions.RequestException as err:
        print ("General ERROR",err)


def calculate_coords(list_of_old_coorinates):
    data = [f"{point[0]},{point[1]}" for point in list_of_old_coorinates]
    data = ";".join(data)
    request_url = f"https://epsg.io/trans?data={data}&s_srs=25833&&t_srs=4326"
    try:
        response = requests.get(request_url)
        transform_coordinates_response = json.loads(response.text)
        transformed_coordinates = [[float(dict["y"]), float(dict["x"])] for dict in transform_coordinates_response]

        return transformed_coordinates
    except requests.exceptions.HTTPError as errh:
        print ("Http ERROR:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Connecting ERROR:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout ERROR:",errt)
    except requests.exceptions.RequestException as err:
        print ("General ERROR",err)
         

def transform_line(line):
    try:
        old_coords = line['geometry']['coordinates'][0][0]
        transformed_coords = calculate_coords(old_coords)
        osm_id = find_osm_node_id(transformed_coords[0])
        # calculate parking area
        all_lats = [x for x, y in transformed_coords]
        all_lons = [y for x, y in transformed_coords]
        parking_area = polygon_area(all_lats, all_lons)  # we multiply by 1000 to convet to m2 instead of km2
        # calculate number of parking spots in the parking area
        single_parking_area = 4.88 * 2.44
        number_of_parking = parking_area / single_parking_area
        # get the label (parking empty/occupied)
        line_label = line['properties']['label_x']

        return osm_id, line_label, number_of_parking
    except:
        print("Tranforming lines ERROR")

def polygon_area(lats, lons, radius=6378137):
    """
    Computes area of spherical polygon, assuming spherical Earth. 
    Returns result in ratio of the sphere's area if the radius is specified.
    Otherwise, in the units of provided radius.
    lats and lons are in degrees.
    """
    try:
        lats = np.deg2rad(lats)
        lons = np.deg2rad(lons)

        # Line integral based on Green's Theorem, assumes spherical Earth
        # close polygon
        if lats[0] != lats[-1]:
            lats = append(lats, lats[0])
            lons = append(lons, lons[0])

        # colatitudes relative to (0,0)
        a = sin(lats / 2) ** 2 + cos(lats) * sin(lons / 2) ** 2
        colat = 2 * arctan2(sqrt(a), sqrt(1 - a))

        # azimuths relative to (0,0)
        az = arctan2(cos(lats) * sin(lons), sin(lats)) % (2 * pi)

        # Calculate diffs
        # daz = diff(az) % (2*pi)
        daz = diff(az)
        daz = (daz + pi) % (2 * pi) - pi
        deltas = diff(colat) / 2
        colat = colat[0:-1] + deltas

        # Perform integral
        integrands = (1 - cos(colat)) * daz

        # Integrate 
        area = abs(sum(integrands)) / (4 * pi)
        area = min(area, 1 - area)
        if radius is not None:  # return in units of radius
            return area * 4 * pi * radius ** 2
        else:  # return in ratio of sphere total area
            return area
    except:
        print("Calculating Area ERROR")

def save_data_to_db(empty_count, occupied_count):
    # save all the empty data
    try:
        for node, count in empty_count.items():
            res = my_conn.execute(f'''select * from parking_data where node_id = {node}''').first()
            if not res:
                stmt = (insert(parking_data_table).values(node_id=node, free_count=count, occupied_count=0, probability=0))
            else:
                existing_count = res['free_count']
                stmt = (update(parking_data_table).where(parking_data_table.c.node_id == node).values(
                    free_count=count + existing_count))
            my_conn.execute(stmt)
        # save all the occupied data
        for node, count in occupied_count.items():
            res = my_conn.execute(f'''select * from parking_data where node_id = {node}''').first()
            if not res:
                stmt = (insert(parking_data_table).values(node_id=node, free_count=0, occupied_count=count, probability=0))
            else:
                existing_count = res['occupied_count']
                stmt = (update(parking_data_table).where(parking_data_table.c.node_id == node).values(
                    occupied_count=count + existing_count))
            my_conn.execute(stmt)
    except:
        print("Saving Data to DB ERROR")

def main():
    try:
        init_db()
        file_path = "parking01.geojson"
        # count the parking spots members:
        empty_pk_spots = {}
        occupied_pk_spots = {}

        with open(file_path) as f:
            data_file = geojson.load(f)
            features_array = data_file['features']

            i = 1
            for feature in features_array:
                node_id, label, amount = transform_line(feature)
                if label == 'PK-space-occupied':
                    occupied_count = occupied_pk_spots.setdefault(node_id, 0)
                    occupied_pk_spots[node_id] = occupied_count + amount
                elif label == 'PK-space-empty':
                    empty_count = empty_pk_spots.setdefault(node_id, 0)
                    empty_pk_spots[node_id] = empty_count + amount
                print(i)
                i += 1

        save_data_to_db(empty_pk_spots, occupied_pk_spots)

        res = my_conn.execute('''SELECT * FROM parking_data''')
        for row in res:
            print(row)
    except:
        print("Error from main createDB")
        exit

#main()
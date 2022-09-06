import sqlite3
import overpy
import json

def get_nodes_in_radius(lat, long, raduis = 100):
    api = overpy.Overpass()
    result = api.query("[out:json];node(around:{}, {}, {});out;".format(raduis,lat, long))
    return tuple(result._nodes.keys())

def DB_Connection(db_file):
    # Create a SQL connection to our SQLite database
    con = sqlite3.connect("my_db.db")

    cur = con.cursor()

    # The result of a "cursor.execute" can be iterated over by row
    # for row in cur.execute('SELECT * FROM parking_data;'):
    #     print(row)
    return cur

def Close_DB_Connection(db):
    db.close()

def Route_to_Parking(lat_source, lon_source ,lat_destination , lon_destination ):
    db = DB_Connection("my_db.db")
    db_nodes_string = get_nodes_in_radius(lat_destination, lon_destination)
    query = 'SELECT node_id , max(probability) from parking_data where node_id in {}'.format(db_nodes_string)
    max_value = db.execute(query)
    #### convert node_id to lat , long by using OSM API or OVERPASS API
    final_path = "https://www.waze.com/live-map/directions?to=ll.{}%2C{}6&from=ll.{}%2C{}".format(max["lat"],max["lon"],lat_source,lon_source)
    Close_DB_Connection(db)
    return final_path


# driver code
lat1 = 52.5180573
lat2 = 52.4798443
lon1 = 13.1863636
lon2 = 13.2743052
node_id = 116676564

api = overpy.Overpass()
result = api.query("[out:json];area[name='Berlin']->.searchArea;(  node    (116676564)    (area.searchArea);  way    (116676564)    (area.searchArea););out;")

print(result.__)















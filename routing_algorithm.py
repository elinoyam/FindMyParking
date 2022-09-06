import sqlite3
import overpy
import requests
import json

"""
TODO 
    Exception and handle with edge case
    Naming convention
EXTRA
    Convert address to coordiantes
"""
def get_nodes_in_radius(lat, long, raduis = 100):
    api = overpy.Overpass()
    result = api.query("[out:json];node(around:{}, {}, {});out;".format(raduis,lat, long))
    return tuple(result._nodes.keys())

def DB_Connection(db_file):
    # Create a SQL connection to our SQLite database
    con = sqlite3.connect("my_db.db")

    cur = con.cursor()

    return cur

def Close_DB_Connection(db):
    db.close()

"""
Route_to_Parking algorithem is creating a URL link of Waze route from origin location to parking lot nearby destination location 
"""
def Route_to_Parking(lat_source, lon_source ,lat_destination , lon_destination ):
    db = DB_Connection("my_db.db")
    db_nodes_string = get_nodes_in_radius(lat_destination, lon_destination)
    query = f"SELECT node_id FROM parking_data WHERE node_id = (SELECT node_id FROM parking_data where node_id in {db_nodes_string} ORDER BY probability DESC LIMIT 1);"
    max_prob_node = db.execute(query)
    max_prob_node = max_prob_node.fetchall()
    node_id = max_prob_node[0][0]
    #### check for getting node id as result ####
    request_url = f"https://nominatim.openstreetmap.org/lookup?osm_ids=N{node_id},W{node_id}&format=json&extratags=1"
    lat, lon = get_first_latlon_of_node(request_url)
    #### check if response ####
    final_path = "https://www.waze.com/live-map/directions?to=ll.{}%2C{}6&from=ll.{}%2C{}".format(lat, lon, lat_source, lon_source)
    Close_DB_Connection(db)
    print(final_path)
    return final_path

def get_first_latlon_of_node(request_url):
    json_response = requests.get(request_url)
    result = json_response.text
    nodes_list = json.loads(result)
    if len(nodes_list) == 0:
        raise Exception("BAD INPUT")
    for row in nodes_list:
        if row["osm_type"] == "node":
            return (row['lat'] , row['lon'])
    return nodes_list[0]['lat'], nodes_list[0]['lon']

cord1 = [52.536535, 13.3939797]
cord2 = [52.5380103 , 13.3982403]

result_url = Route_to_Parking(cord1[0], cord1[1] ,cord2[0], cord2[1])











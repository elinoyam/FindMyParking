import sqlite3
import overpy
import requests
import json
import webbrowser
from flask import Flask, url_for, render_template, request, redirect


def get_nodes_in_radius(lat, long, radius):
    try:
        api = overpy.Overpass()
        result = api.query("[out:json];node(around:{}, {}, {});out;".format(radius,lat, long))
        return tuple(result._nodes.keys())
    except overpy.exception as err:
        print("Query API ERROR:", err)

def db_connection(db_file):
    # Create a SQL connection to our SQLite database
    try:
        con = sqlite3.connect("Fixed_DB.db")
        cur = con.cursor()
        return cur
    except:
        print("Connect DB ERROR")

def close_db_connection(db):
    db.close()

"""
route_to_parking algorithem is creating a URL link of Waze route from origin location to parking lot nearby destination location 
"""
def route_to_parking(lat_source, lon_source ,lat_destination, lon_destination, radius):
    try:
        db = db_connection("Fixed_DB.db")
        db_nodes_string = get_nodes_in_radius(lat_destination, lon_destination, radius)
        query = f"SELECT node_id FROM parking_data WHERE node_id = (SELECT node_id FROM parking_data where node_id in {db_nodes_string} ORDER BY probability DESC LIMIT 1);"
        max_prob_node = db.execute(query)
        max_prob_node = max_prob_node.fetchall()
        node_id = max_prob_node[0][0]
        #### check for getting node id as result ####
        request_url = f"https://nominatim.openstreetmap.org/lookup?osm_ids=N{node_id},W{node_id}&format=json&extratags=1"
        lat, lon = get_first_latlon_of_node(request_url)
        #### check if response ####
        final_path = "https://www.waze.com/live-map/directions?to=ll.{}%2C{}6&from=ll.{}%2C{}".format(lat, lon, lat_source, lon_source)
        close_db_connection(db)
        print(final_path)
        return final_path
    except Exception as e:
        print("Bad Input")

def get_first_latlon_of_node(request_url):
    try:
        json_response = requests.get(request_url)
    except requests.exceptions.HTTPError as errh:
        print ("Http ERROR:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Connecting ERROR:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout ERROR:",errt)
    except requests.exceptions.RequestException as err:
        print ("General ERROR",err)

    else:
        result = json_response.text
        nodes_list = json.loads(result)
        if len(nodes_list) == 0:
            raise Exception("BAD INPUT")
        for row in nodes_list:
            if row["osm_type"] == "node":
                return (row['lat'] , row['lon'])
        return nodes_list[0]['lat'], nodes_list[0]['lon']


def is_float(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

def is_valid_coord(lat, lon):
    is_valid = False
    lat = float(lat)
    lon = float(lon)

    if -90 <= lat and lat <= 90 and -180 <= lon and lon <= 180:
        is_valid = True
    return  is_valid

app = Flask(__name__)

@app.route('/', methods =["GET", "POST"])
def main():
    # cord1 = [52.536535, 13.3939797]
    # cord2 = [52.5380103 , 13.3982403]

    if request.method == "POST":
        cord1_lat = request.form.get('cord1_lat')
        cord1_lon = request.form.get('cord1_lon')
        cord2_lat = request.form.get('cord2_lat')
        cord2_lon = request.form.get('cord2_lon')
        radius= request.form.get('radius')
        if radius:
            radius= float(radius)
        else:
            radius=100
        if is_float(cord1_lat) and is_float(cord1_lon) and is_float(cord2_lat) and is_float(cord2_lon) \
                and is_valid_coord(cord1_lat, cord1_lon):
            cord1_lat = float(cord1_lat)
            cord1_lon = float(cord1_lon)
            cord2_lat = float(cord2_lat)
            cord2_lon = float(cord2_lon)
            result_url = str(route_to_parking(cord1_lat, cord1_lon, cord2_lat, cord2_lon, radius))
            if result_url!= "None":
                chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
                webbrowser.get(chrome_path).open(result_url)
            else:
                return render_template("form.html", error_msg= "BAD INPUT")
        else:
             return render_template("form.html", error_msg= "BAD INPUT")
    return render_template("form.html", error_msg="")


if __name__ == "__main__":
    app.run()

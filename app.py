import sqlite3
import overpy
import requests
import json
import webbrowser
from flask import Flask, url_for, render_template, request


def get_nodes_in_radius(lat, long, raduis = 100):
    try:
        api = overpy.Overpass()
        result = api.query("[out:json];node(around:{}, {}, {});out;".format(raduis,lat, long))
        return tuple(result._nodes.keys())
    except overpy.exception as err:
        print("Query API ERROR:", err)

def db_connection(db_file):
    # Create a SQL connection to our SQLite database
    try:
        con = sqlite3.connect("parking_db.db")
        cur = con.cursor()
        return cur
    except:
        print("Connect DB ERROR")

def close_db_connection(db):
    db.close()

"""
route_to_parking algorithem is creating a URL link of Waze route from origin location to parking lot nearby destination location 
"""
def route_to_parking(lat_source, lon_source ,lat_destination , lon_destination ):
    try:
        db = db_connection("parking_db.db")
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
        close_db_connection(db)
        print(final_path)
        return final_path
    except:
        exit

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

app = Flask(__name__)

@app.route('/', methods =["GET", "POST"])
def main():
    # cord1 = [52.536535, 13.3939797]
    # cord2 = [52.5380103 , 13.3982403]

    if request.method == "POST":
        cord1_lat = float(request.form.get('cord1_lat'))
        cord1_lon = float(request.form.get('cord1_lon'))
        cord2_lat = float(request.form.get('cord2_lat'))
        cord2_lon = float(request.form.get('cord2_lon'))

        result_url = str(route_to_parking(cord1_lat, cord1_lon, cord2_lat, cord2_lon))
        chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
        print(result_url)
        webbrowser.get(chrome_path).open(result_url)

    return render_template("form.html")

if __name__ == "__main__":
    app.run()
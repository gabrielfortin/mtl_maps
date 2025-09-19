import pandas as pd
import folium
import requests
import json
import zipfile
import ssl
import urllib3
from urllib.request import urlopen
import urllib.request
import subprocess
import os

from google.protobuf import json_format
import gtfsrealtime_pb2

def getTripUpdates():
    r = requests.get("https://api.stm.info/pub/od/gtfs-rt/ic/v2/tripUpdates", headers={"apiKey": f"{key}"})
    protobuf_bytes = r.content
    message = gtfsrealtime_pb2.TripUpdate()
    message.ParseFromString(protobuf_bytes)
    json_data = json_format.MessageToJson(message)
    return json.loads(json_data)

def getVehiclePositions():
    r = requests.get("https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions", headers={"apiKey": f"{key}"})
    protobuf_bytes = r.content
    message = gtfsrealtime_pb2.VehiclePosition()
    message.ParseFromString(protobuf_bytes)
    json_data = json_format.MessageToJson(message)
    return json.loads(json_data)

def getGtfs(url: str, filename: str):
    print(f"Downloading {url}...")
    
    try:
        requests.get(url, timeout=5)  
            
        with open(f"auto_data/{filename}", "wb") as f:
            f.write(content)
            
        print(f"Successfully downloaded {filename}")
        return
        
    except Exception as e:
        print(f"urllib.request failed: {e}")
    
    # Fallback to requests with various SSL configurations
    try:
        session = requests.Session()
        # Try with disabled SSL verification
        print(f"Trying requests with disabled SSL verification...")
        r = session.get(url, verify=False, timeout=30)
        r.raise_for_status()
        
        with open(f"auto_data/{filename}", "wb") as f:
            f.write(r.content)
        
        print(f"Successfully downloaded {filename}")
        return
        
    except Exception as e:
        print(f"requests failed: {e}")
    
    # Final fallback: use curl
    try:
        print(f"Trying curl as final fallback...")
        file_path = f"auto_data/{filename}"
        
        # Make sure auto_data directory exists
        os.makedirs("auto_data", exist_ok=True)
        
        # Use curl with insecure SSL
        result = subprocess.run([
            "curl", "-L", "--insecure", "--silent", "--show-error",
            "-o", file_path, url
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            print(f"Successfully downloaded {filename} using curl")
            return
        else:
            print(f"curl failed with return code {result.returncode}")
            if result.stderr:
                print(f"curl error: {result.stderr}")
                
    except Exception as e:
        print(f"curl failed: {e}")
    
    raise Exception(f"All download methods failed for {url}. You may need to download this file manually.")


m = None

def init_map():
    global m
    # Centrer la carte sur Montréal
    m = folium.Map(location=[45.5017, -73.5673], zoom_start=11, tiles='cartodbpositron')
    #m = folium.Map(location=[stops['stop_lat'][0], stops['stop_lon'][0]], zoom_start=11)

def draw_map(zip_path: str, modes: list):
    global m 

    # Charger les arrêts GTFS pour centrer la carte
    with zipfile.ZipFile(zip_path) as z:
        with z.open('stops.txt') as f:
            stops = pd.read_csv(f)
        with z.open('routes.txt') as f:
            lines = pd.read_csv(f)
        with z.open('trips.txt') as f:
            trips = pd.read_csv(f)
        with z.open('shapes.txt') as f:
            shapes = pd.read_csv(f)    

    # If STM, Change 439 to tram
    if 'gtfs_stm' in zip_path:
        lines['route_id'] = lines['route_id'].astype(int)
        lines.loc[lines['route_id'] == 439, 'route_type'] = 0

    # If GPMMOM change S2 to metro
    if 'gtfs_rem' in zip_path:
        trips['route_id'] = trips['route_id'].astype(str)
        lines.loc[lines['route_id'] == "S2", 'route_type'] = 1

    # Draw lines for metro and tram
    shape_ids = trips['shape_id'].unique()
    for shape_id in shape_ids:
        shape = shapes[shapes['shape_id'] == shape_id]
        points = list(zip(shape['shape_pt_lat'], shape['shape_pt_lon']))
        trip = trips[trips['shape_id'] == shape_id].iloc[0]
        route_id = trip['route_id']
        route = lines[lines['route_id'] == route_id].iloc[0]
        route_type = route['route_type']
        color = '#' + route['route_color']

        if route_type == 0 and 0 in modes:  # tram uniquement
            weight = 4
        elif route_type == 1 and 1 in modes:  # metro uniquement
            weight = 6
        elif (route_type == 3 or route_type == 700)  and 3 in modes:  # bus uniquement
            weight = 1
        elif route_type == 2 and 2 in modes:  # train uniquement
            weight = 3
        else:
            continue
        
        folium.PolyLine(points, color=color, weight=weight, opacity=1).add_to(m)

def getGtfsAndDraw(url: str, filename: str, modes: list):
    getGtfs(url, filename)
    draw_map(f"auto_data/{filename}", modes)

init_map()

getGtfsAndDraw("https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip", "gtfs_stm.zip", modes=[3])
getGtfsAndDraw("https://www.rtl-longueuil.qc.ca/transit/latestfeed/RTL.zip", "gtfs_rtl.zip", modes=[3])
getGtfsAndDraw("https://www.rtm.quebec/xdata/trains/google_transit.zip", "gtfs_exo_train.zip", modes=[2])
getGtfsAndDraw("https://www.stlaval.ca/datas/opendata/GTF_STL.zip", "gtfs_stl.zip", modes=[3])
getGtfsAndDraw("https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip", "gtfs_stm.zip", modes=[0,1])
draw_map("auto_data/gtfs_stm.zip", modes=[0,1])
getGtfsAndDraw("https://gtfs.gpmmom.ca/gtfs/gtfs.zip", "gtfs_rem.zip", modes=[0,1])

m.save('live_rem_metro.html')


#https://www.stlaval.ca/datas/opendata/GTF_STL.zip
# https://www.rtl-longueuil.qc.ca/transit/latestfeed/RTL.zip
#https://www.rtm.quebec/xdata/trains/google_transit.zip


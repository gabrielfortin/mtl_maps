import pandas as pd
import folium
import requests
import json
import zipfile

from google.protobuf import json_format
import gtfsrealtime_pb2

key = ""

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

def getGtfsStm():
    url = "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip"
    r = requests.get(url)
    with open("auto_data/gtfs_stm.zip", "wb") as f:
        f.write(r.content)

def getGtfsRem():
    url = "https://gtfs.gpmmom.ca/gtfs/gtfs.zip"
    r = requests.get(url)
    with open("auto_data/gtfs_rem.zip", "wb") as f:
        f.write(r.content)

getGtfsStm()
getGtfsRem()

m = None

def draw_stm_map():
    global m 

    # Charger les arrêts GTFS pour centrer la carte
    with zipfile.ZipFile('auto_data/gtfs_stm.zip') as z:
        with z.open('stops.txt') as f:
            stops = pd.read_csv(f)
        with z.open('routes.txt') as f:
            lines = pd.read_csv(f)
        with z.open('trips.txt') as f:
            trips = pd.read_csv(f)
        with z.open('shapes.txt') as f:
            shapes = pd.read_csv(f)    

    m = folium.Map(location=[stops['stop_lat'][0], stops['stop_lon'][0]], zoom_start=11)


    # Change 439 to tram
    lines['route_id'] = lines['route_id'].astype(int)
    lines.loc[lines['route_id'] == 439, 'route_type'] = 0
    
    # STM metro & tram lines only
    shape_ids = trips['shape_id'].unique()
    for shape_id in shape_ids:
        shape = shapes[shapes['shape_id'] == shape_id]
        points = list(zip(shape['shape_pt_lat'], shape['shape_pt_lon']))
        trip = trips[trips['shape_id'] == shape_id].iloc[0]
        route_id = trip['route_id']
        route = lines[lines['route_id'] == route_id].iloc[0]
        route_type = route['route_type']
        color = '#' + route['route_color']

        if route_type == 0:  # tram uniquement
            weight = 3
        elif route_type == 1:  # metro uniquement
            weight = 6
        else:
            continue
        
        folium.PolyLine(points, color=color, weight=weight, opacity=1).add_to(m)

def draw_gpmm_map():
    global m
    # Charger les arrêts GTFS pour centrer la carte
    with zipfile.ZipFile('auto_data/gtfs_rem.zip') as z:
        with z.open('stops.txt') as f:
            stops = pd.read_csv(f)
        with z.open('routes.txt') as f:
            lines = pd.read_csv(f)
        with z.open('trips.txt') as f:
            trips = pd.read_csv(f)
        with z.open('shapes.txt') as f:
            shapes = pd.read_csv(f)    

    # REM lines
    shape_ids = trips['shape_id'].unique()
    for shape_id in shape_ids:
        shape = shapes[shapes['shape_id'] == shape_id]
        points = list(zip(shape['shape_pt_lat'], shape['shape_pt_lon']))
        trip = trips[trips['shape_id'] == shape_id].iloc[0]
        route_id = trip['route_id']
        route = lines[lines['route_id'] == route_id].iloc[0]
        route_type = route['route_type']
        color = '#' + route['route_color']
        
        weight = 6
        folium.PolyLine(points, color=color, weight=weight, opacity=1).add_to(m)

draw_stm_map()
draw_gpmm_map()

m.save('live_rem_metro.html')




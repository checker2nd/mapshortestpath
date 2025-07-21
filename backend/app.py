from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import osmnx as ox
import networkx as nx

# 起動時に一度だけグラフを構築
G = ox.graph_from_place("Chiyoda City, Tokyo, Japan", network_type="drive")
G = ox.add_edge_lengths(G)

app = FastAPI()

class RouteResponse(BaseModel):
    geometry: dict   # GeoJSON LineString
    distance: float  # メートル
    duration: float  # 秒

@app.get("/route", response_model=RouteResponse)
def get_route(
    start_lat: float = Query(...),
    start_lng: float = Query(...),
    end_lat: float = Query(...),
    end_lng: float = Query(...)
):
    orig = ox.distance.nearest_nodes(G, start_lng, start_lat)
    dest = ox.distance.nearest_nodes(G, end_lng, end_lat)

    try:
        route = nx.dijkstra_path(G, orig, dest, weight='length')
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="Route not found")

    # 距離と所要時間（45km/h想定）を計算
    lengths = nx.get_edge_attributes(G, 'length')
    total_dist = sum(lengths[(route[i], route[i+1], 0)] for i in range(len(route)-1))
    avg_speed = 45_000 / 3600  # m/s
    duration = total_dist / avg_speed

    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
    geojson = {
        "type": "LineString",
        "coordinates": [(lng, lat) for lat, lng in coords]
    }
    return RouteResponse(geometry=geojson, distance=total_dist, duration=duration)

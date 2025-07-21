from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import osmnx as ox
import networkx as nx
import pyproj

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1) グラフ取得（専修大学 生田キャンパス半径1km）
center = (35.619264, 139.540682)
G = ox.graph_from_point(center, dist=1000, network_type="drive")

# 2) 投影座標系に変換（メートル単位）
G = ox.project_graph(G)
# 3) 各エッジに距離属性を追加
G = ox.distance.add_edge_lengths(G)

# 4) 投影系 ↔ 緯度経度 変換器を用意
proj_to_graph = pyproj.Transformer.from_crs("epsg:4326", G.graph["crs"], always_xy=True)
proj_to_latlon = pyproj.Transformer.from_crs(G.graph["crs"], "epsg:4326", always_xy=True)

class RouteResponse(BaseModel):
    geometry: dict   # GeoJSON LineString
    distance: float  # メートル
    duration: float  # 秒

def nearest_node_bruteforce(G, x, y):
    """グラフ G 上で (x, y) に最も近いノードを線形探索で返す"""
    best = None
    best_dist2 = float("inf")
    for n, data in G.nodes(data=True):
        dx = data["x"] - x
        dy = data["y"] - y
        d2 = dx * dx + dy * dy
        if d2 < best_dist2:
            best, best_dist2 = n, d2
    return best

@app.get("/route", response_model=RouteResponse)
def get_route(
    start_lat: float = Query(...),
    start_lng: float = Query(...),
    end_lat:   float = Query(...),
    end_lng:   float = Query(...)
):
    # 1) クリック座標（緯度経度）を投影系 (m) に変換
    sx, sy = proj_to_graph.transform(start_lng, start_lat)
    ex, ey = proj_to_graph.transform(end_lng,   end_lat)

    # 2) 最近傍ノードを自前実装で検索
    orig_node = nearest_node_bruteforce(G, sx, sy)
    dest_node = nearest_node_bruteforce(G, ex, ey)

    # 3) Dijkstra で最短経路探索
    try:
        route = nx.dijkstra_path(G, orig_node, dest_node, weight="length")
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="Route not found")

    # 4) 総距離・所要時間を計算 (45 km/h 想定)
    # lengths = nx.get_edge_attributes(G, "length")
    # total_dist = sum(lengths[(route[i], route[i+1], 0)] for i in range(len(route)-1))
    # 4) 総距離 [m] を NetworkX の組み込みで取得
    # total_dist = nx.shortest_path_length(
    #     G, orig_node, dest_node, weight="length"
    # )
    # 4) 総距離 [m] をノード座標から直接計算
    total_dist = sum(
        ((G.nodes[u]["x"] - G.nodes[v]["x"])**2 +
         (G.nodes[u]["y"] - G.nodes[v]["y"])**2) ** 0.5
        for u, v in zip(route[:-1], route[1:])
    )
    avg_speed_m_s = 45000 / 3600
    duration = total_dist / avg_speed_m_s



    # 5) ルートノード座標を緯度経度に戻して GeoJSON 化
    coords_proj   = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in route]
    coords_latlon = [proj_to_latlon.transform(x, y) for x, y in coords_proj]
    geojson = {"type": "LineString", "coordinates": coords_latlon}

    return RouteResponse(geometry=geojson, distance=total_dist, duration=duration)

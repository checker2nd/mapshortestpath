from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import osmnx as ox
import pyproj

SUFFICIENTLY_BIG=100000000 
class Vertex:
    def __init__(self,n):
        self.name=n
        self.d=SUFFICIENTLY_BIG
        self.isVisited=False
        self.edgeHead=None
        self.shortestPath=None
        self.index=-1 # ヒープ内での添字

class EdgeList:
    def __init__(self):
        self.length=0 #辺の長さ
        self.to=None
        self.next=None


def compareVertex(a, b):
    if a.d < b.d :
        return -1
    elif a.d > b.d:
        return 1
    elif a.name < b.name:
        return -1
    else:
        return 1


class BinaryHeap:
    def __init__(self, a):
        self.last = len(a)-1 #末尾添字
        self.array= a[:]
        for i in range(len(a)):
            self.array[i].index = i
        self.buildHeap()
    
    def leftChild(self, i):
        ret=i*2
        if ret <= self.last:
            return ret
        else:
            return None
    def rightChild(self, i):
        ret=i*2+1
        if ret <= self.last:
            return ret
        else:
            return None
            
    def parent(self, i):
        return int(i/2)
    
    
    def swapInHeap(self, i, j):
        work = self.array[i]
        self.array[i] = self.array[j]
        self.array[j] = work
        self.array[i].index = i
        self.array[j].index = j


    def minHeapify(self, i):
        left= self.leftChild(i)
        right= self.rightChild(i)
        if left is not None and right is not None:
            if compareVertex(self.array[left],self.array[right])==-1:
                min = left
            else: min = right
        else:
            if left is not None: min = left
            elif right is not None: min = right
            else: return
        if compareVertex(self.array[i],self.array[min])==-1:
            return
        
        self.swapInHeap(i, min)
        self.minHeapify(min) # 再帰呼出

    def buildHeap(self):
        for i in reversed(range(1,self.last+1)):
            self.minHeapify(i)

    def siftUp(self, i):
        if self.parent(i) <=0: return
        if compareVertex(self.array[i],self.array[self.parent(i)])==-1:
            self.swapInHeap(i, self.parent(i))
            self.siftUp(self.parent(i)) #再帰呼出


    def extractMin(self):
        self.swapInHeap(1,self.last)
        self.last-=1
        self.minHeapify(1)
        return self.array[self.last + 1]

def Dijkstra(s,binaryheap):
    s.d=0;binaryheap.siftUp(s.index)
    while binaryheap.last>=1:
        u=binaryheap.extractMin()
        e=u.edgeHead
        while e is not None:   
            if(e.to.d > u.d + e.length):    
                e.to.d=u.d+e.length
                e.to.shortestPath=u
                binaryheap.siftUp(e.to.index)
            e=e.next
        
def connectDirectedEdge(fro, to, length):
    newEdge = EdgeList()
    newEdge.to = to
    newEdge.next = fro.edgeHead
    fro.edgeHead = newEdge
    newEdge.length = length

def connectUndirectedEdge(fro, to, length):
    connectDirectedEdge(fro, to, length)
    connectDirectedEdge(to, fro, length)




CENTER = (35.619264, 139.540682)  # 生田駅終点(ここを変えた場合はフロントも変える　wikiに書かれてた大学の座標ではうまくいかなかった)
LOAD_DIST = 3000                #CENTERから道路を読み込む半径(m)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# OSM グラフ取得
G = ox.graph_from_point(CENTER, dist=LOAD_DIST, network_type="drive")#道路ネットワークグラフを取得
G = ox.project_graph(G)#グラフを地理座標系から投影座標系に変換する(緯度経度の3次元　→　2次元にする)
G = ox.distance.add_edge_lengths(G)#道路のedgeに長さの属性を追加する

# フロントから受け取った地理座標系を投影座標系に変換する変換器
proj_to_graph = pyproj.Transformer.from_crs("epsg:4326", G.graph["crs"], always_xy=True)
#投影座標系→地理座標系に変換する（出力用)
proj_to_latlon = pyproj.Transformer.from_crs(G.graph["crs"], "epsg:4326", always_xy=True)

#FastAPIのレスポンス(JSON)形式を定義
class RouteResponse(BaseModel):
    geometry: dict
    distance: float
    car_time: float
    bike_time: float
    walk_time: float

#フロントから送られてきた座標をもとに、最短経路を返す
@app.get("/route", response_model=RouteResponse)
def get_route(
    start_lat: float = Query(...),
    start_lng: float = Query(...),
    end_lat:   float = Query(...),
    end_lng:   float = Query(...)
):
    #緯度経度から投影座標になおす
    sx, sy = proj_to_graph.transform(start_lng, start_lat)
    ex, ey = proj_to_graph.transform(end_lng,   end_lat)

    #クリックされた場所に一番近いノードを取得
    def nearest_node(G, x, y):
        min_id, min_d = None, float("inf")
        for id, d in G.nodes(data=True):
            dx, dy = d["x"]-x, d["y"]-y
            d2 = dx*dx + dy*dy
            if d2 < min_d:
                min_id, min_d = id, d2
        return min_id
    start_node = nearest_node(G, sx, sy)
    end_node = nearest_node(G, ex, ey)

    #OSMのグラフからVertexのリストを作る
    node_ids = list(G.nodes)
    id_to_idx = {}
    idx = 1
    for nid in node_ids:
        id_to_idx[nid] = idx
        idx += 1
    
    VA = [Vertex(None)]#0番目はダミー
    for nid in node_ids:
        VA.append(Vertex(nid))  
    
    for u, v, data in G.edges(data=True):
        connectUndirectedEdge(VA[id_to_idx[u]], VA[id_to_idx[v]], data["length"]) 

    # ダイクストラ法
    heap = BinaryHeap(VA)
    Dijkstra(VA[id_to_idx[start_node]], heap)

    #目的地までのパス復元
    route = []
    cur = VA[id_to_idx[end_node]]
    while cur:
        route.append(cur.name)
        cur = cur.shortestPath
    route.reverse()

    #距離と時間を求める
    total_dist = sum(
        ((G.nodes[u]["x"] - G.nodes[v]["x"])**2 + (G.nodes[u]["y"] - G.nodes[v]["y"])**2) ** 0.5
        for u, v in zip(route[:-1], route[1:])
    )
    total_dist /= 1000
    car_time = total_dist / (40/60)  # 40km/h
    bike_time = total_dist / (15/60) #15km/h
    walk_time = total_dist / (5/60) #5km/h

    #JSON化してフロントに返す
    coords_proj = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in route]
    coords_latlon = [proj_to_latlon.transform(x, y) for x, y in coords_proj]
    geojson = {"type": "LineString", "coordinates": coords_latlon}

    return RouteResponse(geometry=geojson, distance=total_dist, car_time=car_time, bike_time=bike_time, walk_time=walk_time)

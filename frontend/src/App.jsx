import { MapContainer, TileLayer, useMapEvents, Polyline } from 'react-leaflet';
import { useState } from 'react';
import axios from 'axios';

function RouteSelector({ onRoute }) {
  const [pts, setPts] = useState([]);
  useMapEvents({
    click(e) {
    //   const next = [...pts, e.latlng];
    //   setPts(next);
    //   console.log("おした、"+next);
    //   if (next.length === 2) {
    //     axios
    //       .get(`${process.env.REACT_APP_API_URL}/route`, {
    //         params: {
    //           start_lat: next[0].lat,
    //           start_lng: next[0].lng,
    //           end_lat: next[1].lat,
    //           end_lng: next[1].lng,
    //         },
    //       })
    //       .then(res => {
    //         const line = res.data.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
    //         onRoute({ line, info: res.data });
    //       });
    //   }
      const nextPts = [...pts, e.latlng];
      setPts(nextPts);
      console.log("クリック:", nextPts);

      if (nextPts.length === 2) {
        axios
          .get(`${process.env.REACT_APP_API_URL}/route`, {
            params: {
              start_lat: nextPts[0].lat,
              start_lng: nextPts[0].lng,
              end_lat: nextPts[1].lat,
              end_lng: nextPts[1].lng,
            },
          })
          .then(res => {
            const line = res.data.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
            onRoute({ line, info: res.data });
            setPts([]);  // ← ★ポイント：2点選択後に初期化！
          })
          .catch(err => {
            console.error("経路取得エラー:", err);
            setPts([]);  // エラーでもリセット
          });
      }
    },
  });
  return null;
}

export default function App() {
    const [routeData, setRouteData] = useState({ line: null, info: null });
    
    return (
      <div style={{ display: 'flex', height: '100vh' }}>
        {/* 初期表示を専修大学生田キャンパス（35.619264, 139.540682）に */}
        <MapContainer center={[35.619264, 139.540682]} zoom={15} style={{ flex: 1 }}>
           <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
           <RouteSelector onRoute={setRouteData} />
           {routeData.line && <Polyline positions={routeData.line} />}
        </MapContainer>
        <div style={{ width: 300, padding: 16 }}>
          {routeData.info ? (
            <>
              {/* <p>距離: {(routeData.info.distance / 1000).toFixed(2)} km</p>
              <p>所要時間: {(routeData.info.duration / 60).toFixed(1)} 分</p>
              <p><b>距離:</b> {(routeData.info.distance / 1000).toFixed(2)} km</p> */}

            {/* ===== 追加表示 ===== */}
            {(() => {
              const distKm = routeData.info.distance / 1000;
              return (
                <>
                  <p><b>距離:</b> {(routeData.info.distance / 1000).toFixed(2)} km</p>
                  <p><b>車:</b> {(distKm / 40 * 60).toFixed(1)} 分 (40 km/h)</p>
                  <p><b>自転車:</b> {(distKm / 15 * 60).toFixed(1)} 分 (15 km/h)</p>
                  <p><b>徒歩:</b> {(distKm / 5 * 60).toFixed(1)} 分 (5 km/h)</p>
                </>
              );
            })()}
            </>
            
          ) : (
            <p>地図を2回クリックしてルートを取得</p>
          )}
        </div>
      </div>
    );
  }
